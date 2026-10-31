// JAVA 对照: ruoyi-admin/.../monitor/SysLogininforController.java
// JAVA 对照: ruoyi-system/.../service/impl/SysLogininforServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysLogininforMapper.xml
// 类/职责: 系统访问记录 — 列表 / 导出 / 批量删除 / 清空
// 对应 Go 文件: internal/modules/ops/logininfor.go
//
// DIFF: Service 层是对 Mapper 的纯透传，SQL 直接写在 handler 内（与 XML 逐条对应）。
// DIFF: SysLogininfor.status 在 Java 是 String，@Excel 的 readConverterExp 按字符串匹配；
// 这里同样按字符串匹配（不转 int），未知值原样输出。
package ops

import (
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// logininforSelectVo 对应 SysLogininforMapper.xml 的 select 列。
const logininforSelectVo = "select info_id, user_name, ipaddr, login_location, browser, os, status, msg, login_time " +
	"from sys_logininfor"

const logininforExportSheet = "登录日志"

// logininforColumns 对应 SysLogininfor 上 @Excel 字段的声明顺序。
var logininforColumns = []excelColumn{
	{Name: "序号"},
	{Name: "用户账号"},
	{Name: "登录状态"},
	{Name: "登录地址"},
	{Name: "登录地点"},
	{Name: "浏览器"},
	{Name: "操作系统"},
	{Name: "提示消息"},
	{Name: "访问时间", Width: excelDateWidth},
}

type logininforHandler struct {
	app *app.App
}

// logininforQuery 对应控制器形参 SysLogininfor 中参与查询的字段。
type logininforQuery struct {
	IPAddr    string
	Status    string
	UserName  string
	BeginTime string
	EndTime   string
}

// buildLogininforSQL 逐条对应 SysLogininforMapper.xml 的 <where>。
func buildLogininforSQL(q *logininforQuery) (string, []any) {
	var conds []string
	var args []any
	if q.IPAddr != "" {
		conds = append(conds, "ipaddr like concat('%', ?, '%')")
		args = append(args, q.IPAddr)
	}
	if q.Status != "" {
		conds = append(conds, "status = ?")
		args = append(args, q.Status)
	}
	if q.UserName != "" {
		conds = append(conds, "user_name like concat('%', ?, '%')")
		args = append(args, q.UserName)
	}
	if q.BeginTime != "" {
		conds = append(conds, "date_format(login_time,'%y%m%d') >= date_format(?,'%y%m%d')")
		args = append(args, q.BeginTime)
	}
	if q.EndTime != "" {
		conds = append(conds, "date_format(login_time,'%y%m%d') <= date_format(?,'%y%m%d')")
		args = append(args, q.EndTime)
	}
	if len(conds) == 0 {
		return logininforSelectVo, nil
	}
	return logininforSelectVo + " where " + strings.Join(conds, " and "), args
}

// bindLogininforQuery 对应 Spring 把 query string 绑到 SysLogininfor。
func bindLogininforQuery(c *gin.Context) *logininforQuery {
	return &logininforQuery{
		IPAddr:    c.Query("ipaddr"),
		Status:    c.Query("status"),
		UserName:  c.Query("userName"),
		BeginTime: timeParam(c, "beginTime"),
		EndTime:   timeParam(c, "endTime"),
	}
}

// List 对应 GET /monitor/logininfor/list（没有 @Log）。
func (h *logininforHandler) List(c *gin.Context) {
	q := bindLogininforQuery(c)
	baseSQL, args := buildLogininforSQL(q)
	rows, total, err := queryPage[model.SysLogininfor](c.Request.Context(), h.app.DB, baseSQL, args,
		"order by info_id desc", web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 GET /monitor/logininfor/export（导出全量，不分页）。
func (h *logininforHandler) Export(c *gin.Context) {
	q := bindLogininforQuery(c)
	baseSQL, args := buildLogininforSQL(q)
	rows, _, err := queryPage[model.SysLogininfor](c.Request.Context(), h.app.DB, baseSQL, args,
		"order by info_id desc", web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	data := make([][]any, 0, len(rows))
	for _, row := range rows {
		data = append(data, []any{
			row.InfoID,
			model.Str(row.UserName),
			convertStatusLabel(model.Str(row.Status)),
			model.Str(row.IPAddr),
			model.Str(row.LoginLocation),
			model.Str(row.Browser),
			model.Str(row.OS),
			model.Str(row.Msg),
			excelDate(row.LoginTime),
		})
	}
	ajax, err := exportExcel(h.app, logininforExportSheet, logininforColumns, data)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, ajax)
}

// Remove 对应 DELETE /monitor/logininfor/{infoIds}（逗号切分，带 @Log）。
func (h *logininforHandler) Remove(c *gin.Context) {
	ids, err := parsePathIDs(c.Param("infoIds"), "infoIds")
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	args := make([]any, 0, len(ids))
	for _, id := range ids {
		args = append(args, id)
	}
	res := h.app.DB.WithContext(c.Request.Context()).
		Exec("delete from sys_logininfor where info_id in ("+inPlaceholders(len(ids))+")", args...)
	if res.Error != nil {
		web.JSON(c, web.ErrorResult(res.Error))
		return
	}
	web.JSON(c, web.ToAjax(res.RowsAffected))
}

// Clean 对应 DELETE /monitor/logininfor/clean（truncate）。
func (h *logininforHandler) Clean(c *gin.Context) {
	if err := h.app.DB.WithContext(c.Request.Context()).
		Exec("truncate table sys_logininfor").Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// convertStatusLabel 等价 ExcelUtil.convertByExp(String value, "0=成功,1=失败")。
func convertStatusLabel(value string) string {
	switch value {
	case "0":
		return loginStatusLabels[0]
	case "1":
		return loginStatusLabels[1]
	}
	return value
}

// newLogininforRoutes 注册 /monitor/logininfor/**。
func newLogininforRoutes(reg gin.IRouter, a *app.App) {
	h := &logininforHandler{app: a}
	g := reg.Group("/monitor/logininfor")
	g.GET("/list", middleware.Perm("monitor:logininfor:list"), h.List)
	g.GET("/export", middleware.Perm("monitor:logininfor:export"),
		middleware.OperLog(a, "登录日志", middleware.BusinessExport), h.Export)
	g.DELETE("/clean", middleware.Perm("monitor:logininfor:remove"),
		middleware.OperLog(a, "登录日志", middleware.BusinessClean), h.Clean)
	g.DELETE("/:infoIds", middleware.Perm("monitor:logininfor:remove"),
		middleware.OperLog(a, "登录日志", middleware.BusinessDelete), h.Remove)
}
