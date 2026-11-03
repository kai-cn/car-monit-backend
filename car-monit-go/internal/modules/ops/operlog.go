// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/SysOperlogController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysOperLogServiceImpl.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysOperLogMapper.xml
// 类/职责: 操作日志 — 列表 / 导出 / 批量删除 / 清空（truncate）
// 对应 Go 文件: internal/modules/ops/operlog.go
//
// DIFF: Java 的 Service 层只是对 Mapper 的透传，Go 侧同样没有额外的业务逻辑，SQL 直接写在
// 本文件（对照 XML）。`@PreAuthorize` / `@Log` 由路由注册处的中间件承担。
// DIFF: `/export` 没有 startPage()，导出的是**全量**命中行；这里传入空 PageDomain 达到同样效果。
package ops

import (
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// operLogSelectVo 逐字对应 SysOperLogMapper.xml 的 <sql id="selectOperLogVo">。
const operLogSelectVo = "select oper_id, title, business_type, method, request_method, operator_type, " +
	"oper_name, dept_name, oper_url, oper_ip, oper_location, oper_param, json_result, status, " +
	"error_msg, oper_time from sys_oper_log"

// operLogExportSheet 对应 `util.exportExcel(list, "操作日志")` 的工作表名。
const operLogExportSheet = "操作日志"

// operLogColumns 对应 SysOperLog 上 @Excel 字段的声明顺序。
var operLogColumns = []excelColumn{
	{Name: "操作序号"},
	{Name: "操作模块"},
	{Name: "业务类型"},
	{Name: "请求方法"},
	{Name: "请求方式"},
	{Name: "操作类别"},
	{Name: "操作人员"},
	{Name: "部门名称"},
	{Name: "请求地址"},
	{Name: "操作地址"},
	{Name: "操作地点"},
	{Name: "请求参数"},
	{Name: "返回参数"},
	{Name: "状态"},
	{Name: "错误消息"},
	{Name: "操作时间", Width: excelDateWidth},
}

type operLogHandler struct {
	app *app.App
}

// operLogQuery 对应控制器形参 SysOperLog（只有查询用得到的字段）。
type operLogQuery struct {
	Title         string
	BusinessType  *int
	BusinessTypes []int
	Status        *int
	OperName      string
	BeginTime     string
	EndTime       string
}

// bindOperLogQuery 对应 Spring 把 query string 绑到 SysOperLog 实体。
func bindOperLogQuery(c *gin.Context) (*operLogQuery, error) {
	q := &operLogQuery{
		Title:     c.Query("title"),
		OperName:  c.Query("operName"),
		BeginTime: timeParam(c, "beginTime"),
		EndTime:   timeParam(c, "endTime"),
	}
	var err error
	if q.BusinessType, err = intPtr(c, "businessType", "java.lang.Integer"); err != nil {
		return nil, err
	}
	if q.BusinessTypes, err = intArray(c, "businessTypes", "java.lang.Integer[]"); err != nil {
		return nil, err
	}
	if q.Status, err = intPtr(c, "status", "java.lang.Integer"); err != nil {
		return nil, err
	}
	return q, nil
}

// buildOperLogSQL 逐条对应 SysOperLogMapper.xml 的 <where>，顺序与 XML 的 <if> 序列一致。
func buildOperLogSQL(q *operLogQuery) (string, []any) {
	var conds []string
	var args []any

	if q.Title != "" {
		conds = append(conds, "title like concat('%', ?, '%')")
		args = append(args, q.Title)
	}
	// JAVA 对照: <if test="businessType != null and businessType != ''">
	// DIFF: OGNL 把 Integer 与 '' 比较折成 double，'' 等于 0.0，因此 businessType=0（其它）
	// 时该条件被丢弃、查出全部记录。这里显式跳过 0，与 Java 的实际行为一致。
	if q.BusinessType != nil && *q.BusinessType != 0 {
		conds = append(conds, "business_type = ?")
		args = append(args, *q.BusinessType)
	}
	if len(q.BusinessTypes) > 0 {
		conds = append(conds, "business_type in ("+inPlaceholders(len(q.BusinessTypes))+")")
		for _, bt := range q.BusinessTypes {
			args = append(args, bt)
		}
	}
	// JAVA 对照: <if test="status != null"> —— 没有 != ''，0 是有效条件。
	if q.Status != nil {
		conds = append(conds, "status = ?")
		args = append(args, *q.Status)
	}
	if q.OperName != "" {
		conds = append(conds, "oper_name like concat('%', ?, '%')")
		args = append(args, q.OperName)
	}
	if q.BeginTime != "" {
		conds = append(conds, "date_format(oper_time,'%y%m%d') >= date_format(?,'%y%m%d')")
		args = append(args, q.BeginTime)
	}
	if q.EndTime != "" {
		conds = append(conds, "date_format(oper_time,'%y%m%d') <= date_format(?,'%y%m%d')")
		args = append(args, q.EndTime)
	}

	if len(conds) == 0 {
		return operLogSelectVo, nil
	}
	return operLogSelectVo + " where " + strings.Join(conds, " and "), args
}

// List 对应 SysOperlogController.list：`GET /monitor/operlog/list`。
func (h *operLogHandler) List(c *gin.Context) {
	q, err := bindOperLogQuery(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	baseSQL, args := buildOperLogSQL(q)
	page := web.PageAlways(c)
	rows, total, err := queryPage[model.SysOperLog](c.Request.Context(), h.app.DB, baseSQL, args,
		orderFor("order by oper_id desc", page), page)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysOperlogController.export：文件名落在 msg，前端再走 /common/download。
func (h *operLogHandler) Export(c *gin.Context) {
	q, err := bindOperLogQuery(c)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	baseSQL, args := buildOperLogSQL(q)
	rows, _, err := queryPage[model.SysOperLog](c.Request.Context(), h.app.DB, baseSQL, args,
		"order by oper_id desc", web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	data := make([][]any, 0, len(rows))
	for _, row := range rows {
		data = append(data, []any{
			row.OperID,
			row.Title,
			convertByExp(row.BusinessType, businessTypeLabels),
			row.Method,
			row.RequestMethod,
			convertByExp(row.OperatorType, operatorTypeLabels),
			row.OperName,
			row.DeptName,
			row.OperURL,
			row.OperIP,
			row.OperLocation,
			row.OperParam,
			row.JSONResult,
			convertByExp(row.Status, operStatusLabels),
			row.ErrorMsg,
			excelDate(row.OperTime),
		})
	}
	ajax, err := exportExcel(h.app, operLogExportSheet, operLogColumns, data)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, ajax)
}

// Remove 对应 SysOperlogController.remove：`DELETE /monitor/operlog/{operIds}`（逗号切分）。
// 注意：Java 的 remove **没有** @Log（只有 logininfor 的 remove 有）。
func (h *operLogHandler) Remove(c *gin.Context) {
	ids, err := parsePathIDs(c.Param("operIds"), "operIds")
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	placeholders := inPlaceholders(len(ids))
	args := make([]any, 0, len(ids))
	for _, id := range ids {
		args = append(args, id)
	}
	res := h.app.DB.WithContext(c.Request.Context()).
		Exec("delete from sys_oper_log where oper_id in ("+placeholders+")", args...)
	if res.Error != nil {
		web.JSON(c, web.ErrorResult(res.Error))
		return
	}
	web.JSON(c, web.ToAjax(res.RowsAffected))
}

// Clean 对应 SysOperlogController.clean：`truncate table sys_oper_log`（DDL、不可回滚）。
// 返回值不看影响行数，直接 AjaxResult.success()。
func (h *operLogHandler) Clean(c *gin.Context) {
	if err := h.app.DB.WithContext(c.Request.Context()).
		Exec("truncate table sys_oper_log").Error; err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// newOperLogRoutes 注册 /monitor/operlog/**。
func newOperLogRoutes(reg gin.IRouter, a *app.App) {
	h := &operLogHandler{app: a}
	list := reg.Group("/monitor/operlog")
	list.GET("/list", middleware.Perm("monitor:operlog:list"), h.List)
	list.GET("/export", middleware.Perm("monitor:operlog:export"),
		middleware.OperLog(a, "操作日志", middleware.BusinessExport), h.Export)
	list.DELETE("/clean", middleware.Perm("monitor:operlog:remove"),
		middleware.OperLog(a, "操作日志", middleware.BusinessClean), h.Clean)
	list.DELETE("/:operIds", middleware.Perm("monitor:operlog:remove"), h.Remove)
}

// 便于测试与阅读：id 段转换成字符串（Java @PathVariable 原样接收）。
var _ = strconv.Itoa
