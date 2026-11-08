// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysNoticeController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysNoticeServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysNoticeMapper.xml
// 类/职责: 通知公告 — 列表/详情/匿名查看/增删改
// 对应 Go 文件: internal/modules/systemaux/notice.go
//
// DIFF: Java 的 noticeType 在 service 里被强制成 "1"（通知），前端传 "2" 也会被覆盖。
// DIFF: create_by / update_by 由 service 覆盖成 **userId 的字符串**（不是用户名）。
// DIFF: list / listquery / getInfo 在 Java 里没有 @PreAuthorize，只有 add/edit/remove 有。
// DIFF: /view/{noticeId} 在 SecurityConfig 里是 anonymous() —— 只允许**匿名**访问；
//
//	本工程把该路由挂在未认证的 Engine 上，已登录用户同样可以访问（安全过滤器
//	已认证分支不会拦截 Engine 路由）。
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

// noticeBody 对应 @RequestBody SysNotice；指针用于区分“未传”与“空串”。
type noticeBody struct {
	NoticeID      *int64  `json:"noticeId"`
	NoticeTitle   *string `json:"noticeTitle"`
	NoticeType    *string `json:"noticeType"`
	NoticeContent *string `json:"noticeContent"`
	Status        *string `json:"status"`
	CreateBy      *string `json:"createBy"`
	UpdateBy      *string `json:"updateBy"`
	Remark        *string `json:"remark"`
	BussID        *string `json:"bussId"`
	BussName      *string `json:"bussName"`
	TenantID      *int64  `json:"tenantId"`
}

// noticeQuery 对应 query string 绑定的 SysNotice 查询条件。
type noticeQuery struct {
	NoticeTitle   *string
	NoticeType    *string
	CreateBy      *string
	Status        *string
	BussID        *string
	BussName      *string
	NoticeContent *string
	TenantID      *int64
}

func bindNoticeQuery(c *gin.Context) noticeQuery {
	q := noticeQuery{
		NoticeTitle:   queryPtr(c, "noticeTitle"),
		NoticeType:    queryPtr(c, "noticeType"),
		CreateBy:      queryPtr(c, "createBy"),
		Status:        queryPtr(c, "status"),
		BussID:        queryPtr(c, "bussId"),
		BussName:      queryPtr(c, "bussName"),
		NoticeContent: queryPtr(c, "noticeContent"),
	}
	if v := queryPtr(c, "tenantId"); v != nil && *v != "" {
		n, err := strconv.ParseInt(strings.TrimSpace(*v), 10, 64)
		if err == nil {
			q.TenantID = &n
		}
	}
	return q
}

const noticeSelectVo = `select t.notice_id, t.notice_title, t.notice_type,
       cast(t.notice_content as char) as notice_content, t.status,
       t.create_by, t.create_time, t.update_by, t.update_time, t.remark,
       t.buss_id, t.buss_name, t.tenant_id
from sys_notice t`

type noticeService struct {
	app *app.App
}

func newNoticeService(a *app.App) *noticeService { return &noticeService{app: a} }

// selectNoticeList 对应 SysNoticeMapper.selectNoticeList。
func (s *noticeService) selectNoticeList(ctx context.Context, pd web.PageDomain, q noticeQuery) ([]model.SysNotice, int64, error) {
	where := " where 1 = 1"
	args := make([]any, 0, 8)
	if v := strVal(q.NoticeTitle); v != "" {
		where += " and t.notice_title like concat('%', ?, '%')"
		args = append(args, v)
	}
	if v := strVal(q.NoticeType); v != "" {
		where += " and t.notice_type = ?"
		args = append(args, v)
	}
	if q.CreateBy != nil {
		where += " and t.create_by = ?"
		args = append(args, *q.CreateBy)
	}
	if v := strVal(q.Status); v != "" {
		where += " and t.status = ?"
		args = append(args, v)
	}
	if v := strVal(q.BussID); v != "" {
		where += " and t.buss_id = ?"
		args = append(args, v)
	}
	if v := strVal(q.BussName); v != "" {
		where += " and t.buss_name like concat('%', ?, '%')"
		args = append(args, v)
	}
	if q.TenantID != nil {
		// JAVA 对照: and (t.TENANT_ID = #{tenantId} or t.TENANT_ID = 100) —— 100 号租户始终可见。
		where += " and (t.tenant_id = ? or t.tenant_id = 100)"
		args = append(args, *q.TenantID)
	}
	if v := strVal(q.NoticeContent); v != "" {
		where += " and (t.notice_content = ?)"
		args = append(args, v)
	}
	listSQL := noticeSelectVo + where
	countSQL := "select count(1) from sys_notice t" + where
	return queryPage[model.SysNotice](ctx, s.app.DB, pd, countSQL, args, listSQL, "t.create_time desc")
}

// selectNoticeByID 对应 selectNoticeById。
func (s *noticeService) selectNoticeByID(ctx context.Context, noticeID int64) (*model.SysNotice, error) {
	var row model.SysNotice
	err := s.app.DB.WithContext(ctx).Raw(noticeSelectVo+" where t.notice_id = ?", noticeID).Take(&row).Error
	if errors.Is(err, gorm.ErrRecordNotFound) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &row, nil
}

// insertNotice 对应 SysNoticeServiceImpl.insertNotice：
// 强制 noticeType="1"，并覆盖 createBy（userId 字符串）与 tenantId。
func (s *noticeService) insertNotice(ctx context.Context, b *noticeBody, userID int64, tenantID int64) (int64, error) {
	userStr := strconv.FormatInt(userID, 10)
	columns := make([]string, 0, 10)
	values := make([]string, 0, 10)
	args := make([]any, 0, 10)
	add := func(col string, val any) {
		columns = append(columns, col)
		values = append(values, "?")
		args = append(args, val)
	}
	if v := strVal(b.NoticeTitle); v != "" {
		add("notice_title", v)
	}
	// Java: notice.setNoticeType("1")
	add("notice_type", "1")
	if v := strVal(b.NoticeContent); v != "" {
		add("notice_content", v)
	}
	if v := strVal(b.Status); v != "" {
		add("status", v)
	}
	if v := strVal(b.Remark); v != "" {
		add("remark", v)
	}
	// Java: notice.setCreateBy(SecurityUtils.getUserId() + "")
	add("create_by", userStr)
	if b.BussID != nil {
		add("buss_id", *b.BussID)
	}
	if b.BussName != nil {
		add("buss_name", *b.BussName)
	}
	// Java: notice.setTenantId(SecurityUtils.getTenantId())
	add("tenant_id", tenantID)
	columns = append(columns, "create_time")
	values = append(values, "sysdate()")

	sql := "insert into sys_notice (" + strings.Join(columns, ",") + ") values (" + strings.Join(values, ",") + ")"
	res := s.app.DB.WithContext(ctx).Exec(sql, args...)
	if res.Error != nil {
		return 0, res.Error
	}
	if res.RowsAffected > 0 {
		var id int64
		if err := s.app.DB.WithContext(ctx).Raw("select last_insert_id()").Scan(&id).Error; err == nil {
			b.NoticeID = &id
		}
	}
	return res.RowsAffected, nil
}

// updateNotice 对应 SysNoticeServiceImpl.updateNotice（updateBy 覆盖成 userId 字符串）。
func (s *noticeService) updateNotice(ctx context.Context, b *noticeBody, userID int64) (int64, error) {
	sets := make([]string, 0, 8)
	args := make([]any, 0, 8)
	if v := strVal(b.NoticeTitle); v != "" {
		sets = append(sets, "notice_title = ?")
		args = append(args, v)
	}
	if v := strVal(b.NoticeType); v != "" {
		sets = append(sets, "notice_type = ?")
		args = append(args, v)
	}
	if b.NoticeContent != nil {
		sets = append(sets, "notice_content = ?")
		args = append(args, *b.NoticeContent)
	}
	if v := strVal(b.Status); v != "" {
		sets = append(sets, "status = ?")
		args = append(args, v)
	}
	// Java: notice.setUpdateBy(SecurityUtils.getUserId() + "")
	sets = append(sets, "update_by = ?")
	args = append(args, strconv.FormatInt(userID, 10))
	if v := strVal(b.BussID); v != "" {
		sets = append(sets, "buss_id = ?")
		args = append(args, v)
	}
	if v := strVal(b.BussName); v != "" {
		sets = append(sets, "buss_name = ?")
		args = append(args, v)
	}
	sets = append(sets, "update_time = sysdate()")
	args = append(args, b.NoticeID)

	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_notice set "+strings.Join(sets, ", ")+" where notice_id = ?", args...)
	return res.RowsAffected, res.Error
}

// deleteNoticeByIDs 对应 deleteNoticeByIds。
func (s *noticeService) deleteNoticeByIDs(ctx context.Context, ids []int64) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec(
		"delete from sys_notice where notice_id in ("+inPlaceholders(len(ids))+")", int64Args(ids)...)
	return res.RowsAffected, res.Error
}

// ---------------------------------------------------------------------------
// HTTP 入口
// ---------------------------------------------------------------------------

type noticeHandler struct {
	svc *noticeService
}

func newNoticeHandler(a *app.App) *noticeHandler { return &noticeHandler{svc: newNoticeService(a)} }

// List 对应 GET /system/notice/list（无 @PreAuthorize，登录即可）。
func (h *noticeHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectNoticeList(c.Request.Context(), web.PageAlways(c), bindNoticeQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListQuery 对应 GET /system/notice/listquery：startPage 之后强制 status="0"。
func (h *noticeHandler) ListQuery(c *gin.Context) {
	q := bindNoticeQuery(c)
	status := "0"
	q.Status = &status
	rows, total, err := h.svc.selectNoticeList(c.Request.Context(), web.PageAlways(c), q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ViewInfo 对应 GET /system/notice/view/{noticeId}（匿名）。
func (h *noticeHandler) ViewInfo(c *gin.Context) {
	ids, err := parseLongArray("noticeId", c.Param("noticeId"))
	if err != nil || len(ids) == 0 {
		web.JSON(c, web.ErrorResult(orParamTypeError(err)))
		return
	}
	row, err := h.svc.selectNoticeByID(c.Request.Context(), ids[0])
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

// GetInfo 对应 GET /system/notice/{noticeId}。
func (h *noticeHandler) GetInfo(c *gin.Context) {
	h.ViewInfo(c)
}

// Add 对应 POST /system/notice。
func (h *noticeHandler) Add(c *gin.Context) {
	var body noticeBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	rows, err := h.svc.insertNotice(c.Request.Context(), &body, auth.CurrentUserID(c), model.Int64Val(auth.CurrentUser(c).User.TenantID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 PUT /system/notice。
func (h *noticeHandler) Edit(c *gin.Context) {
	var body noticeBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	rows, err := h.svc.updateNotice(c.Request.Context(), &body, auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 DELETE /system/notice/{noticeIds}。
func (h *noticeHandler) Remove(c *gin.Context) {
	ids, err := parseLongArray("noticeIds", c.Param("noticeIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteNoticeByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// registerNotice 挂载 /system/notice/**。
func registerNotice(reg *router.Registry) {
	h := newNoticeHandler(reg.App)

	// JAVA 对照: SecurityConfig.antMatchers("/system/notice/view/**").anonymous()
	reg.Engine.GET("/system/notice/view/:noticeId", middleware.AnonymousOnly(reg.App), h.ViewInfo)

	g := reg.Authed.Group("/system/notice")
	g.GET("/list", h.List)
	g.GET("/listquery", h.ListQuery)
	g.GET("/:noticeId", h.GetInfo)
	g.POST("", middleware.Perm("system:notice:add"),
		middleware.OperLog(reg.App, "通知公告", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:notice:edit"),
		middleware.OperLog(reg.App, "通知公告", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:noticeIds", middleware.Perm("system:notice:remove"),
		middleware.OperLog(reg.App, "通知公告", middleware.BusinessDelete), h.Remove)
}
