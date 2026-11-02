// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java
// 类/职责: 代码生成 HTTP 入口 — 15 个映射（列表/详情/列/导入/保存/删除/预览/下载/同步/批量）
// 对应 Go 文件: internal/modules/generator/handler.go
//
// DIFF: Java 的 `@Validated @RequestBody` 在进入方法（@PreAuthorize）之前完成校验；
// Gin 的中间件永远先于 handler，所以"无权限 + 缺字段"的请求这里返回 403 而不是校验文案。
// DIFF: importTable / batchGenCode 的 `tables` 在 Java 里由 getParameter 取值（同时覆盖
// query 与 form body）；这里先查 form 再查 query。
package generator

import (
	"errors"
	"net/http"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/web"
)

const (
	zipContentType        = "application/octet-stream; charset=UTF-8"
	zipContentDisposition = `attachment; filename="ruoyi.zip"`
)

type genHandler struct {
	app *app.App
	svc *genTableService
}

func newGenHandler(a *app.App) *genHandler {
	return &genHandler{app: a, svc: newGenTableService(a)}
}

// ---------------------------------------------------------------------------
// 参数绑定
// ---------------------------------------------------------------------------

// bindGenTableQuery 对应形参 `GenTable genTable`（Spring 从 query string 绑定）。
func bindGenTableQuery(c *gin.Context) *GenTable {
	table := &GenTable{}
	if value, ok := c.GetQuery("tableName"); ok {
		table.TableName = &value
	}
	if value, ok := c.GetQuery("tableComment"); ok {
		table.TableComment = &value
	}
	params := map[string]any{}
	if value := queryParam(c, "params[beginTime]", "params.beginTime"); value != "" {
		params["beginTime"] = value
	}
	if value := queryParam(c, "params[endTime]", "params.endTime"); value != "" {
		params["endTime"] = value
	}
	if len(params) > 0 {
		table.Params = params
	}
	return table
}

// queryParam 对应 BaseEntity.params["beginTime"]（下标的两种写法都接受）。
func queryParam(c *gin.Context, keys ...string) string {
	for _, key := range keys {
		if value, ok := c.GetQuery(key); ok {
			return strings.TrimSpace(value)
		}
	}
	return ""
}

// bindColumnQuery 对应 @RequestBody GenTableColumn（只有查询用得到的字段）。
func bindColumnQuery(c *gin.Context) (*GenTableColumn, error) {
	column := &GenTableColumn{}
	if err := c.ShouldBindJSON(column); err != nil {
		return nil, web.NewServiceError("请求参数解析异常：%s", err.Error())
	}
	return column, nil
}

// bindGenTableBody 对应 @RequestBody GenTable。
func bindGenTableBody(c *gin.Context) (*GenTable, error) {
	table := &GenTable{}
	if err := c.ShouldBindJSON(table); err != nil {
		return nil, web.NewServiceError("请求参数解析异常：%s", err.Error())
	}
	return table, nil
}

// validateGenTable 对应 GenTable/GenTableColumn 上的 @NotBlank（父级字段顺序 = 声明序，
// 然后 @Valid 级联到每一列的 javaField）。
func validateGenTable(table *GenTable) error {
	checks := []struct {
		value   *string
		message string
	}{
		{table.TableName, "表名称不能为空"},
		{table.TableComment, "表描述不能为空"},
		{table.ClassName, "实体类名称不能为空"},
		{table.PackageName, "生成包路径不能为空"},
		{table.ModuleName, "生成模块名不能为空"},
		{table.BusinessName, "生成业务名不能为空"},
		{table.FunctionName, "生成功能名不能为空"},
		{table.FunctionAuthor, "作者不能为空"},
	}
	for _, check := range checks {
		if check.value == nil || strings.TrimSpace(*check.value) == "" {
			return web.NewServiceError("%s", check.message)
		}
	}
	for _, column := range table.Columns {
		if column.JavaField == nil || strings.TrimSpace(*column.JavaField) == "" {
			return web.NewServiceError("Java属性不能为空")
		}
	}
	return nil
}

// parseLongPath 对应 @PathVariable Long / Long[] 的类型转换失败文案。
func parseLongPath(name, raw string) (int64, error) {
	value, err := strconv.ParseInt(strings.TrimSpace(raw), 10, 64)
	if err != nil {
		return 0, web.NewServiceError(
			"请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Long'，但输入值为：'%s'", name, raw)
	}
	return value, nil
}

// parseLongArrayPath 对应 @PathVariable Long[]（Spring 按逗号切分并 trim）。
func parseLongArrayPath(name, raw string) ([]int64, error) {
	parts := splitJava(raw, ",")
	values := make([]int64, 0, len(parts))
	for _, part := range parts {
		value, err := parseLongPath(name, strings.TrimSpace(part))
		if err != nil {
			return nil, err
		}
		values = append(values, value)
	}
	return values, nil
}

// tablesParam 对应 `String tables`：缺失时 Java 抛 NPE（返回的布尔值即"参数是否存在"）。
func tablesParam(c *gin.Context) (string, bool) {
	if value, ok := c.GetPostForm("tables"); ok {
		return value, true
	}
	return c.GetQuery("tables")
}

// ---------------------------------------------------------------------------
// 响应
// ---------------------------------------------------------------------------

// renderError 把 error 转成 AjaxResult；NPE/NoSuchElement 之外的错误沿用 ErrorResult。
func renderError(c *gin.Context, err error) {
	if errors.Is(err, errNullMessage) {
		// JAVA 对照: GlobalExceptionHandler -> AjaxResult.error(null) -> {"msg":null,"code":500}
		result := web.NewAjaxResult()
		result.Put(web.TagCode, web.StatusInternalError)
		result.Put(web.TagMsg, nil)
		web.JSON(c, result)
		return
	}
	if errors.Is(err, errNoSuchElement) {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	web.JSON(c, web.ErrorResult(err))
}

// writeZip 对应 private genCode(HttpServletResponse, byte[] data)。
func writeZip(c *gin.Context, data []byte) {
	c.Header("Access-Control-Allow-Origin", "*")
	c.Header("Access-Control-Expose-Headers", "Content-Disposition")
	c.Header("Content-Disposition", zipContentDisposition)
	c.Header("Content-Length", strconv.Itoa(len(data)))
	c.Data(http.StatusOK, zipContentType, data)
}

// columnTableInfo 对应手工构造的 TableDataInfo：code=0、msg=null（Java 基本类型默认值）。
type columnTableInfo struct {
	Total int64 `json:"total"`
	Rows  any   `json:"rows"`
	Code  int   `json:"code"`
	Msg   any   `json:"msg"`
}

// ---------------------------------------------------------------------------
// 查询
// ---------------------------------------------------------------------------

// genList GET /tool/gen/list。
func (h *genHandler) genList(c *gin.Context) {
	filter := bindGenTableQuery(c)
	rows, total, err := h.svc.selectGenTableList(c.Request.Context(), filter, web.PageAlways(c))
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// getAllGenerateTableList GET /tool/gen/all/list（无权限点、无 startPage）。
func (h *genHandler) getAllGenerateTableList(c *gin.Context) {
	filter := bindGenTableQuery(c)
	rows, _, err := h.svc.selectGenTableList(c.Request.Context(), filter, web.PageDomain{})
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// dataList GET /tool/gen/db/list。
func (h *genHandler) dataList(c *gin.Context) {
	filter := bindGenTableQuery(c)
	rows, total, err := h.svc.selectDbTableList(c.Request.Context(), filter, web.PageAlways(c))
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// columnList GET /tool/gen/column/{talbleId}：路径变量是死的，真正入参是 query tableId。
func (h *genHandler) columnList(c *gin.Context) {
	_ = c.Param("talbleId") // Java 方法参数没有 @PathVariable，路径段不参与绑定
	var tableID *int64
	if raw, ok := c.GetQuery("tableId"); ok && strings.TrimSpace(raw) != "" {
		value, err := parseLongPath("tableId", raw)
		if err != nil {
			renderError(c, err)
			return
		}
		tableID = &value
	}
	rows, err := h.svc.selectGenTableColumnListByTableID(c.Request.Context(), tableID)
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, &columnTableInfo{Total: int64(len(rows)), Rows: rows, Code: 0, Msg: nil})
}

// getColumnList POST /tool/gen/getColumnList（无权限点，startPage）。
func (h *genHandler) getColumnList(c *gin.Context) {
	column, err := bindColumnQuery(c)
	if err != nil {
		renderError(c, err)
		return
	}
	rows, err := h.svc.selectGenTableColumnList(c.Request.Context(), column)
	if err != nil {
		renderError(c, err)
		return
	}
	// JAVA 对照: startPage() + getDataTable(list)；Go 统一在 SQL 层分页。
	rows, total := pageColumns(rows, web.Page(c))
	web.JSON(c, web.Table(rows, total))
}

// getAllColumnList POST /tool/gen/getAllColumnList（无权限点、无 startPage）。
func (h *genHandler) getAllColumnList(c *gin.Context) {
	column, err := bindColumnQuery(c)
	if err != nil {
		renderError(c, err)
		return
	}
	rows, err := h.svc.selectGenTableColumnList(c.Request.Context(), column)
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// pageColumns 对已查出的列做内存分页（列查询没有独立的 COUNT 语句需求）。
func pageColumns(rows []*GenTableColumn, pd web.PageDomain) ([]*GenTableColumn, int64) {
	total := int64(len(rows))
	if !pd.HasPage {
		return rows, total
	}
	limit, start := pd.LimitOffset(total)
	if start >= len(rows) {
		return make([]*GenTableColumn, 0), total
	}
	end := start + limit
	if end > len(rows) {
		end = len(rows)
	}
	return rows[start:end], total
}

// ---------------------------------------------------------------------------
// 增删改
// ---------------------------------------------------------------------------

// importTableSave POST /tool/gen/importTable。
func (h *genHandler) importTableSave(c *gin.Context) {
	raw, ok := tablesParam(c)
	if !ok {
		renderError(c, errNullMessage)
		return
	}
	tableNames := splitJava(raw, ",")
	tableList, err := h.svc.selectDbTableListByNames(c.Request.Context(), tableNames)
	if err != nil {
		renderError(c, err)
		return
	}
	if err := h.svc.importGenTable(c.Request.Context(), tableList, auth.CurrentUsername(c)); err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Success())
}

// editSave PUT /tool/gen。
func (h *genHandler) editSave(c *gin.Context) {
	table, err := bindGenTableBody(c)
	if err != nil {
		renderError(c, err)
		return
	}
	if err := validateGenTable(table); err != nil {
		renderError(c, err)
		return
	}
	if err := h.svc.validateEdit(table); err != nil {
		renderError(c, err)
		return
	}
	if err := h.svc.updateGenTable(c.Request.Context(), table); err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Success())
}

// remove DELETE /tool/gen/{tableIds}。
func (h *genHandler) remove(c *gin.Context) {
	tableIDs, err := parseLongArrayPath("tableIds", c.Param("tableIds"))
	if err != nil {
		renderError(c, err)
		return
	}
	if err := h.svc.deleteGenTableByIDs(c.Request.Context(), tableIDs); err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Success())
}

// ---------------------------------------------------------------------------
// 预览 / 生成
// ---------------------------------------------------------------------------

// preview GET /tool/gen/preview/{tableId}。
func (h *genHandler) preview(c *gin.Context) {
	tableID, err := parseLongPath("tableId", c.Param("tableId"))
	if err != nil {
		renderError(c, err)
		return
	}
	dataMap, err := h.svc.previewCode(c.Request.Context(), tableID)
	if err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.SuccessData(dataMap))
}

// download GET /tool/gen/download/{tableName}。
func (h *genHandler) download(c *gin.Context) {
	tableName := c.Param("tableName")
	data, err := h.svc.downloadCode(c.Request.Context(), []string{tableName})
	if err != nil {
		renderError(c, err)
		return
	}
	writeZip(c, data)
}

// genCode GET /tool/gen/genCode/{tableName}。
func (h *genHandler) genCode(c *gin.Context) {
	if err := h.svc.generatorCode(c.Request.Context(), c.Param("tableName")); err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Success())
}

// synchDb GET /tool/gen/synchDb/{tableName}。
func (h *genHandler) synchDb(c *gin.Context) {
	if err := h.svc.synchDb(c.Request.Context(), c.Param("tableName")); err != nil {
		renderError(c, err)
		return
	}
	web.JSON(c, web.Success())
}

// batchGenCode GET /tool/gen/batchGenCode。
func (h *genHandler) batchGenCode(c *gin.Context) {
	raw, ok := tablesParam(c)
	if !ok {
		renderError(c, errNullMessage)
		return
	}
	data, err := h.svc.downloadCode(c.Request.Context(), splitJava(raw, ","))
	if err != nil {
		renderError(c, err)
		return
	}
	writeZip(c, data)
}

// ---------------------------------------------------------------------------
// 详情（必须最后注册：/{talbleId} 会吃掉所有单段 GET）
// ---------------------------------------------------------------------------

// getInfo GET /tool/gen/{talbleId}。
func (h *genHandler) getInfo(c *gin.Context) {
	tableID, err := parseLongPath("talbleId", c.Param("talbleId"))
	if err != nil {
		renderError(c, err)
		return
	}
	ctx := c.Request.Context()
	table, err := h.svc.selectGenTableByID(ctx, tableID)
	if err != nil {
		renderError(c, err)
		return
	}
	tables, err := h.svc.selectGenTableAll(ctx)
	if err != nil {
		renderError(c, err)
		return
	}
	columns, err := h.svc.selectGenTableColumnListByTableID(ctx, &tableID)
	if err != nil {
		renderError(c, err)
		return
	}
	if len(columns) > 0 {
		for _, column := range columns {
			if ids := strVal(column.DialogSearchColumnIDs); ids != "" {
				found, err := h.svc.selectGenTableColumnListByColumnIDs(ctx, ids)
				if err != nil {
					renderError(c, err)
					return
				}
				if len(found) > 0 {
					names := make([]string, 0, len(found))
					for _, item := range found {
						names = append(names, strVal(item.ColumnName))
					}
					joined := strings.Join(names, ",")
					column.DialogSearchColumnNames = &joined
				}
			}
			if ids := strVal(column.DialogListColumnIDs); ids != "" {
				found, err := h.svc.selectGenTableColumnListByColumnIDs(ctx, ids)
				if err != nil {
					renderError(c, err)
					return
				}
				if len(found) > 0 {
					names := make([]string, 0, len(found))
					for _, item := range found {
						names = append(names, strVal(item.ColumnName))
					}
					joined := strings.Join(names, ",")
					column.DialogListColumnNames = &joined
				}
			}
		}
	}
	// JAVA 对照: HashMap 桶序 —— tables(2) / rows(12) / info(15)
	data := web.NewJavaMap().
		Put("info", table).
		Put("rows", columns).
		Put("tables", tables)
	web.JSON(c, web.SuccessData(data))
}
