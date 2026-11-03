// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUpgradeInfoController.java:20-111
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUpgradeInfoServiceImpl.java:23-126
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysUpgradeInfoMapper.xml:23-103
// 类/职责: 系统升级信息 — list/newest/export/getInfo/add/edit/remove（无权限点）
// 对应 Go 文件: internal/modules/systemaux/upgrade.go
//
// DIFF: 实体 SysUpgradeInfo 没有任何 @Excel 注解，Java 的 util.exportExcel(list, sheetName)
// 只会生成一张空表头的表；Go 侧同样以空 headers 调用 exportExcel，文件名仍放 msg。
// DIFF: 控制器方法上只有 @Log，没有 @PreAuthorize —— 这里同样不挂 middleware.Perm。
package systemaux

import (
	"context"
	"errors"
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

const upgradeSelectVo = `select t.id, t.ver, t.info, t.back_col1, t.eps_id, t.del_flag,
       t.create_by, t.create_time, t.update_by, t.update_time, t.tenant_id
from sys_upgrade_info t`

// upgradeQuery 对应 Spring 以 GET 参数绑定的 SysUpgradeInfo。
type upgradeQuery struct {
	ID       *string
	Ver      *string
	Info     *string
	BackCol1 *string
	EpsID    *int64
	TenantID *int64
	CreateBy *int64
}

func bindUpgradeQuery(c *gin.Context) upgradeQuery {
	return upgradeQuery{
		ID:       queryPtr(c, "id"),
		Ver:      queryPtr(c, "ver"),
		Info:     queryPtr(c, "info"),
		BackCol1: queryPtr(c, "backCol1"),
		EpsID:    queryInt64Ptr(c, "epsId"),
		TenantID: queryInt64Ptr(c, "tenantId"),
		CreateBy: queryInt64Ptr(c, "createBy"),
	}
}

// upgradeBody 对应 @RequestBody SysUpgradeInfo。
type upgradeBody struct {
	ID       *string `json:"id"`
	Ver      *string `json:"ver"`
	Info     *string `json:"info"`
	BackCol1 *string `json:"backCol1"`
	EpsID    *int64  `json:"epsId"`
	DelFlag  *string `json:"delFlag"`
	CreateBy *int64  `json:"createBy"`
	UpdateBy *int64  `json:"updateBy"`
	TenantID *int64  `json:"tenantId"`
}

type upgradeService struct {
	app *app.App
}

func newUpgradeService(a *app.App) *upgradeService { return &upgradeService{app: a} }

// selectUpgradeList 对应 selectSysUpgradeInfoList。
func (s *upgradeService) selectUpgradeList(ctx context.Context, pd web.PageDomain, q upgradeQuery) ([]model.SysUpgradeInfo, int64, error) {
	where := " where t.del_flag = '0'"
	args := make([]any, 0, 7)
	if v := strVal(q.ID); v != "" {
		where += " and t.id = ?"
		args = append(args, v)
	}
	if v := strVal(q.Ver); v != "" {
		where += " and t.ver = ?"
		args = append(args, v)
	}
	if v := strVal(q.Info); v != "" {
		where += " and t.info = ?"
		args = append(args, v)
	}
	if v := strVal(q.BackCol1); v != "" {
		where += " and t.back_col1 = ?"
		args = append(args, v)
	}
	if q.EpsID != nil {
		where += " and t.eps_id = ?"
		args = append(args, *q.EpsID)
	}
	if q.TenantID != nil {
		where += " and t.tenant_id = ?"
		args = append(args, *q.TenantID)
	}
	if q.CreateBy != nil {
		where += " and t.create_by = ?"
		args = append(args, *q.CreateBy)
	}
	return queryPage[model.SysUpgradeInfo](ctx, s.app.DB, pd,
		"select count(1) from sys_upgrade_info t"+where, args,
		upgradeSelectVo+where, "t.create_time desc,t.id")
}

// selectUpgradeByID 对应 selectSysUpgradeInfoById（主键是字符串 UUID）。
func (s *upgradeService) selectUpgradeByID(ctx context.Context, id string) (*model.SysUpgradeInfo, error) {
	var row model.SysUpgradeInfo
	err := s.app.DB.WithContext(ctx).Raw(upgradeSelectVo+" where t.id = ?", id).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// selectUpgradeNewest 对应 selectSysUpgradeInfoNewest（参数被 service 忽略）。
func (s *upgradeService) selectUpgradeNewest(ctx context.Context) (*model.SysUpgradeInfo, error) {
	var row model.SysUpgradeInfo
	err := s.app.DB.WithContext(ctx).Raw(
		upgradeSelectVo + " where t.del_flag = '0' and t.back_col1 = 1 order by t.update_time desc limit 1").
		Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// saveUpgrade 对应 saveSysUpgradeInfo：有 id 改、无 id 增，审计字段由登录上下文补。
func (s *upgradeService) saveUpgrade(ctx context.Context, b *upgradeBody, userID, epsID, tenantID int64) (*web.AjaxResult, error) {
	curDate := nowPtr()
	if isNotEmpty(b.ID) {
		sets := make([]string, 0, 12)
		args := make([]any, 0, 13)
		if b.Ver != nil {
			sets = append(sets, "ver = ?")
			args = append(args, *b.Ver)
		}
		if b.Info != nil {
			sets = append(sets, "info = ?")
			args = append(args, *b.Info)
		}
		if b.BackCol1 != nil {
			sets = append(sets, "back_col1 = ?")
			args = append(args, *b.BackCol1)
		}
		if b.EpsID != nil {
			sets = append(sets, "eps_id = ?")
			args = append(args, *b.EpsID)
		}
		if b.DelFlag != nil {
			sets = append(sets, "del_flag = ?")
			args = append(args, *b.DelFlag)
		}
		if b.CreateBy != nil {
			sets = append(sets, "create_by = ?")
			args = append(args, *b.CreateBy)
		}
		if b.TenantID != nil {
			sets = append(sets, "tenant_id = ?")
			args = append(args, *b.TenantID)
		}
		sets = append(sets, "update_by = ?", "update_time = ?")
		args = append(args, userID, curDate)
		args = append(args, *b.ID)
		if err := s.app.DB.WithContext(ctx).Exec(
			"update sys_upgrade_info set "+strings.Join(sets, ", ")+" where id = ?", args...).Error; err != nil {
			return nil, err
		}
		return web.SuccessFull("操作成功！", *b.ID), nil
	}

	// Java: setId(StringUtils.getUUID()) + del_flag/epsId/tenantId/审计字段
	newID := uuidString()
	row := map[string]any{
		"id":          newID,
		"del_flag":    "0",
		"eps_id":      epsID,
		"tenant_id":   tenantID,
		"create_by":   userID,
		"create_time": curDate,
		"update_by":   userID,
		"update_time": curDate,
	}
	if b.Ver != nil {
		row["ver"] = *b.Ver
	}
	if b.Info != nil {
		row["info"] = *b.Info
	}
	if b.BackCol1 != nil {
		row["back_col1"] = *b.BackCol1
	}
	if err := s.app.DB.WithContext(ctx).Table("sys_upgrade_info").Create(row).Error; err != nil {
		return nil, err
	}
	return web.SuccessFull("操作成功！", newID), nil
}

// deleteUpgradeByIDs 对应 deleteSysUpgradeInfoByIds：软删除，count==0 也返回 success。
func (s *upgradeService) deleteUpgradeByIDs(ctx context.Context, ids []string) (int64, error) {
	args := make([]any, 0, len(ids))
	for _, id := range ids {
		args = append(args, id)
	}
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_upgrade_info set del_flag = '1' where id in ("+inPlaceholders(len(ids))+")", args...)
	return res.RowsAffected, res.Error
}

// parseStringArray 对应 Spring 对 @PathVariable String[] 的 “a,b” 拆分。
func parseStringArray(raw string) []string {
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}

// ---------------------------------------------------------------------------
// HTTP 入口
// ---------------------------------------------------------------------------

type upgradeHandler struct {
	app *app.App
	svc *upgradeService
}

func newUpgradeHandler(a *app.App) *upgradeHandler {
	return &upgradeHandler{app: a, svc: newUpgradeService(a)}
}

// List 对应 GET /system/upgradeInfo/list：强制按登录用户租户过滤。
func (h *upgradeHandler) List(c *gin.Context) {
	q := bindUpgradeQuery(c)
	lu := auth.CurrentUser(c)
	q.TenantID = lu.User.TenantID
	rows, total, err := h.svc.selectUpgradeList(c.Request.Context(), web.PageAlways(c), q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(nonNil(rows), total))
}

// Newest 对应 GET /system/upgradeInfo/newest。
func (h *upgradeHandler) Newest(c *gin.Context) {
	row, err := h.svc.selectUpgradeNewest(c.Request.Context())
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// Export 对应 GET /system/upgradeInfo/export（实体无 @Excel，导出空表头）。
func (h *upgradeHandler) Export(c *gin.Context) {
	rows, _, err := h.svc.selectUpgradeList(c.Request.Context(), web.PageDomain{}, bindUpgradeQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([][]any, 0, len(rows))
	filename, err := exportExcel(h.app, "系统升级信息数据", nil, data)
	excelSend(c, filename, err)
}

// GetInfo 对应 GET /system/upgradeInfo/{id}。
func (h *upgradeHandler) GetInfo(c *gin.Context) {
	row, err := h.svc.selectUpgradeByID(c.Request.Context(), c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// Add 对应 POST /system/upgradeInfo。
func (h *upgradeHandler) Add(c *gin.Context) {
	var body upgradeBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	lu := auth.CurrentUser(c)
	result, err := h.svc.saveUpgrade(c.Request.Context(), &body, lu.UserID(), lu.User.DeptID, model.Int64Val(lu.User.TenantID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, result)
}

// Edit 对应 PUT /system/upgradeInfo。
func (h *upgradeHandler) Edit(c *gin.Context) {
	h.Add(c)
}

// Remove 对应 DELETE /system/upgradeInfo/{ids}。
func (h *upgradeHandler) Remove(c *gin.Context) {
	ids := parseStringArray(c.Param("ids"))
	if len(ids) == 0 {
		web.JSON(c, web.SuccessData(int64(0)))
		return
	}
	count, err := h.svc.deleteUpgradeByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// registerUpgrade 挂载 /system/upgradeInfo/**。
func registerUpgrade(reg *router.Registry) {
	h := newUpgradeHandler(reg.App)

	g := reg.Authed.Group("/system/upgradeInfo")
	g.GET("/list", h.List)
	g.GET("/newest", h.Newest)
	g.GET("/export", middleware.OperLog(reg.App, "系统升级信息", middleware.BusinessExport), h.Export)
	g.GET("/:id", h.GetInfo)
	g.POST("", middleware.OperLog(reg.App, "系统升级信息", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.OperLog(reg.App, "系统升级信息", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:ids", middleware.OperLog(reg.App, "系统升级信息", middleware.BusinessDelete), h.Remove)
}
