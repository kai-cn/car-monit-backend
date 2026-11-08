// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexMenuController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysIndexMenuServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysIndexMenuMapper.xml
// 类/职责: 用户常用菜单 — 九宫格候选/我的常用/增删改
// 对应 Go 文件: internal/modules/systemaux/indexmenu.go
//
// DIFF: list / add / remove 的 @PreAuthorize 在 Java 源码里是注释掉的，这里不挂权限点。
// DIFF: userId 一律由登录上下文覆盖（客户端传值无效）；控制器与 service 各覆盖一次。
// DIFF: list 与 getList 的 SQL 自带 ORDER BY，分页不再追加客户端排序列。
package systemaux

import (
	"context"
	"errors"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// indexMenuBody 对应 @RequestBody SysIndexMenu；id 兼容数字/字符串两种写法。
type indexMenuBody struct {
	ID        any     `json:"id"`
	UserID    *int64  `json:"userId"`
	MenuID    *int64  `json:"menuId"`
	MenuName  *string `json:"menuName"`
	MenuName2 *string `json:"menuName2"`
	MenuIDs   *string `json:"menuIds"`
	MenuURL   *string `json:"menuUrl"`
	Sort      *int64  `json:"sort"`
}

type indexMenuQuery struct {
	MenuName  *string
	MenuName2 *string
}

func bindIndexMenuQuery(c *gin.Context) indexMenuQuery {
	return indexMenuQuery{
		MenuName:  queryPtr(c, "menuName"),
		MenuName2: queryPtr(c, "menuName2"),
	}
}

const indexMenuListVo = `select t2.menu_name as menu_name2, t1.menu_id, t1.menu_name
from sys_menu t1, sys_menu t2
where t1.menu_type='C' and t1.visible = '0'
and t2.menu_id = t1.parent_id`

const indexMenuSelectVo = `select t.id, t.user_id, t.menu_id, t.sort, t.eps_id, t.del_flag,
       t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id
from sys_index_menu t`

type indexMenuService struct {
	app *app.App
}

func newIndexMenuService(a *app.App) *indexMenuService { return &indexMenuService{app: a} }

// selectList 对应 selectSysIndexMenuList：候选菜单（排除已加入的、排除还有子菜单的）。
func (s *indexMenuService) selectList(ctx context.Context, pd web.PageDomain, q indexMenuQuery, userID int64) ([]model.SysIndexMenu, int64, error) {
	where := ""
	args := make([]any, 0, 4)
	// JAVA 对照: <if test="userId != 1"> —— 超管不加角色授权过滤。
	if userID != 1 {
		where += " and exists (select 1 from sys_role_menu rm, sys_user_role ur" +
			" where rm.role_id = ur.role_id and rm.menu_id = t1.menu_id and ur.user_id = ?)"
		args = append(args, userID)
	}
	where += " and not exists (select 1 from sys_index_menu tim where tim.del_flag = '0'" +
		" and tim.menu_id = t1.menu_id and tim.user_id = ?)"
	args = append(args, userID)
	where += " and not exists (select 1 from sys_menu t3 where t3.menu_type = 'C' and t3.parent_id = t1.menu_id)"
	if v := strVal(q.MenuName); v != "" {
		where += " and t1.menu_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.MenuName2); v != "" {
		where += " and t2.menu_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	listSQL := indexMenuListVo + where
	countSQL := "select count(1) from (" + indexMenuListVo + where + ") table_count"
	// JAVA 对照: OrderByParser 会替换语句自带的 order by，故把它作为默认排序传入。
	return queryPage[model.SysIndexMenu](ctx, s.app.DB, pd, countSQL, args, listSQL,
		"t2.parent_id,t2.order_num,t1.order_num,t1.menu_id")
}

// getList 对应 getList：我常用的菜单（SQL 自带 limit 9）。
func (s *indexMenuService) getList(ctx context.Context, userID int64) ([]model.SysIndexMenu, error) {
	var rows []model.SysIndexMenu
	err := s.app.DB.WithContext(ctx).Raw(`select t.id,t1.menu_name,concat(t2.path,'/',t1.path) as menu_url
from sys_index_menu t
left join sys_menu t1 on t.menu_id = t1.menu_id
left join sys_menu t2 on t1.parent_id = t2.menu_id
where t.del_flag='0'
and t.user_id = ?
order by t.create_time desc
limit 9`, userID).Scan(&rows).Error
	return rows, err
}

// selectByID 对应 selectSysIndexMenuById。
func (s *indexMenuService) selectByID(ctx context.Context, id int64) (*model.SysIndexMenu, error) {
	var row model.SysIndexMenu
	err := s.app.DB.WithContext(ctx).Raw(indexMenuSelectVo+" where t.id = ?", id).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// save 对应 saveSysIndexMenu：有 id 就改，没有就新增（新增时补 UUID 主键）。
func (s *indexMenuService) save(ctx context.Context, b *indexMenuBody, userID, epsID int64) (*web.AjaxResult, error) {
	curDate := nowPtr()
	id := anyToString(b.ID)
	if isNotEmpty(id) {
		updateID, err := strconv.ParseInt(*id, 10, 64)
		if err != nil {
			return nil, web.NewServiceError("%s", err.Error())
		}
		sets := make([]string, 0, 10)
		args := make([]any, 0, 11)
		if b.UserID != nil {
			sets = append(sets, "user_id = ?")
			args = append(args, *b.UserID)
		}
		if b.MenuID != nil {
			sets = append(sets, "menu_id = ?")
			args = append(args, *b.MenuID)
		}
		if b.Sort != nil {
			sets = append(sets, "sort = ?")
			args = append(args, *b.Sort)
		}
		sets = append(sets, "update_by = ?", "update_time = ?")
		args = append(args, userID, curDate)
		args = append(args, updateID)
		if err := s.app.DB.WithContext(ctx).Exec(
			"update sys_index_menu set "+strings.Join(sets, ", ")+" where id = ?", args...).Error; err != nil {
			return nil, err
		}
		return web.SuccessFull("操作成功！", *id), nil
	}

	// Java: sysIndexMenu.setId(StringUtils.getUUID())
	newID := uuidString()
	row := map[string]any{
		"id":          newID,
		"del_flag":    "0",
		"eps_id":      epsID,
		"create_by":   userID,
		"create_time": curDate,
		"update_by":   userID,
		"update_time": curDate,
	}
	if b.UserID != nil {
		row["user_id"] = *b.UserID
	}
	if b.MenuID != nil {
		row["menu_id"] = *b.MenuID
	}
	if b.Sort != nil {
		row["sort"] = *b.Sort
	}
	if err := s.app.DB.WithContext(ctx).Table("sys_index_menu").Create(row).Error; err != nil {
		return nil, err
	}
	return web.SuccessFull("操作成功！", newID), nil
}

// insertByMenuIDs 对应 insertSysIndexMenu(String menuIds)：拆逗号、先删后插。
func (s *indexMenuService) insertByMenuIDs(ctx context.Context, menuIDs *string, userID, epsID int64) error {
	curDate := nowPtr()
	raw := strVal(menuIDs)
	if !isBlank(raw) {
		// Java: if (menuIds.endsWith(",")) menuIds.substring(0, len-1) —— 只剥一个。
		raw = deleteEnd(raw)
		for _, part := range splitJava(raw) {
			menuID, err := strconv.ParseInt(part, 10, 64)
			if err != nil {
				return web.NewServiceError("%s", err.Error())
			}
			if err := s.app.DB.WithContext(ctx).Exec(
				"delete from sys_index_menu where menu_id = ? and user_id = ?", menuID, userID).Error; err != nil {
				return err
			}
			row := map[string]any{
				"user_id":     userID,
				"menu_id":     menuID,
				"del_flag":    "0",
				"eps_id":      epsID,
				"create_by":   userID,
				"create_time": curDate,
				"update_by":   userID,
				"update_time": curDate,
			}
			if err := s.app.DB.WithContext(ctx).Table("sys_index_menu").Create(row).Error; err != nil {
				return err
			}
		}
	}
	return nil
}

// splitJava 等价于 Java String#split(",")：丢弃尾部空串。
func splitJava(s string) []string {
	parts := strings.Split(s, ",")
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

// deleteByIDs 对应 deleteSysIndexMenuByIds（软删除，count==0 也算成功）。
func (s *indexMenuService) deleteByIDs(ctx context.Context, ids []int64) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_index_menu set del_flag = '1' where id in ("+inPlaceholders(len(ids))+")", int64Args(ids)...)
	return res.RowsAffected, res.Error
}

// anyToString 对应 Jackson 把数字/字符串写入 String 字段的行为。
func anyToString(v any) *string {
	switch t := v.(type) {
	case nil:
		return nil
	case string:
		return &t
	case float64:
		s := strconv.FormatInt(int64(t), 10)
		return &s
	case bool:
		s := strconv.FormatBool(t)
		return &s
	default:
		s := ""
		return &s
	}
}

// ---------------------------------------------------------------------------
// HTTP 入口
// ---------------------------------------------------------------------------

type indexMenuHandler struct {
	app *app.App
	svc *indexMenuService
}

func newIndexMenuHandler(a *app.App) *indexMenuHandler {
	return &indexMenuHandler{app: a, svc: newIndexMenuService(a)}
}

// List 对应 GET /system/indexmenu/list（无权限点）。
func (h *indexMenuHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectList(c.Request.Context(), web.PageAlways(c), bindIndexMenuQuery(c), auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(nonNil(rows), total))
}

// Export 对应 GET /system/indexmenu/export：文件名放在 msg。
func (h *indexMenuHandler) Export(c *gin.Context) {
	rows, _, err := h.svc.selectList(c.Request.Context(), web.PageDomain{}, bindIndexMenuQuery(c), auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([][]any, 0, len(rows))
	for i := range rows {
		data = append(data, []any{nil, numVal(rows[i].MenuID)})
	}
	filename, err := exportExcel(h.app, "用户常用菜单数据", []string{"用户ID", "菜单ID"}, data)
	excelSend(c, filename, err)
}

// MyList 对应 GET /system/indexmenu/mylist：控制器与 service 各覆盖一次 userId。
func (h *indexMenuHandler) MyList(c *gin.Context) {
	rows, err := h.svc.getList(c.Request.Context(), auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(nonNil(rows)))
}

// GetInfo 对应 GET /system/indexmenu/{id}。
func (h *indexMenuHandler) GetInfo(c *gin.Context) {
	ids, err := parseLongArray("id", c.Param("id"))
	if err != nil || len(ids) == 0 {
		web.JSON(c, web.ErrorResult(orParamTypeError(err)))
		return
	}
	row, err := h.svc.selectByID(c.Request.Context(), ids[0])
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if row == nil {
		web.JSON(c, web.SuccessData(nil))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// Add 对应 POST /system/indexmenu：只读 menuIds。
func (h *indexMenuHandler) Add(c *gin.Context) {
	var body indexMenuBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	lu := auth.CurrentUser(c)
	if err := h.svc.insertByMenuIDs(c.Request.Context(), body.MenuIDs, lu.UserID(), lu.User.DeptID); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// Edit 对应 PUT /system/indexmenu。
func (h *indexMenuHandler) Edit(c *gin.Context) {
	var body indexMenuBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	lu := auth.CurrentUser(c)
	result, err := h.svc.save(c.Request.Context(), &body, lu.UserID(), lu.User.DeptID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, result)
}

// Remove 对应 DELETE /system/indexmenu/{ids}（软删除，成功即便 count==0）。
func (h *indexMenuHandler) Remove(c *gin.Context) {
	ids, err := parseLongArray("ids", c.Param("ids"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// registerIndexMenu 挂载 /system/indexmenu/**。
func registerIndexMenu(reg *router.Registry) {
	h := newIndexMenuHandler(reg.App)

	g := reg.Authed.Group("/system/indexmenu")
	g.GET("/list", h.List)
	g.GET("/export", middleware.Perm("system:indexmenu:export"),
		middleware.OperLog(reg.App, "用户常用菜单", middleware.BusinessExport), h.Export)
	g.GET("/mylist", h.MyList)
	g.GET("/:id", middleware.Perm("system:indexmenu:query"), h.GetInfo)
	g.POST("", middleware.OperLog(reg.App, "用户常用菜单", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:indexmenu:edit"),
		middleware.OperLog(reg.App, "用户常用菜单", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:ids", middleware.OperLog(reg.App, "用户常用菜单", middleware.BusinessDelete), h.Remove)
}
