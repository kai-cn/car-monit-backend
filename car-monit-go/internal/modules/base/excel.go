// JAVA 对照: com.ruoyi.common.utils.poi.ExcelUtil（@Excel 字段导出）
// JAVA 对照: EasyPOI TemplateExportParams 模板导出（附件流）
// 类/职责: base 模块的 Excel 导出
// 对应 Go 文件: internal/modules/base/excel.go
//
// DIFF: Java 的 ExcelUtil.encodingFilename(sheetName) = UUID + "_" + sheetName + ".xlsx"，
// 文件写入 profile/download 后把文件名放进 msg；EasyPOI 模板导出直接写附件流。
// Go 用 excelize 生成同样的表头与列顺序，单元格样式做保守近似。
package base

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/web"
)

// exportCol 描述导出的一列（Field 为结构体 json 名）。
type exportCol struct {
	Title    string
	Field    string
	DateOnly bool
}

const excelMaxRows = 65536

// plainValue 把实体字段值转成可写入单元格的普通值。
// JAVA 对照: ExcelUtil#getCellValue（Date 按 dateFormat 格式化）
func plainValue(v any, dateFmtOnly bool) any {
	dateFmt := func(d web.DateTime) any {
		if d.IsZero() {
			return ""
		}
		if dateFmtOnly {
			return d.Format(dateOnlyLayout)
		}
		return d.String()
	}
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return x
	case *string:
		if x == nil {
			return ""
		}
		return *x
	case int:
		return x
	case *int:
		if x == nil {
			return ""
		}
		return *x
	case int64:
		return x
	case *int64:
		if x == nil {
			return ""
		}
		return *x
	case float64:
		return x
	case *float64:
		if x == nil {
			return ""
		}
		return *x
	case *web.DateTime:
		if x == nil {
			return ""
		}
		return dateFmt(*x)
	case web.DateTime:
		return dateFmt(x)
	case *dateOnly:
		if x == nil || x.IsZero() {
			return ""
		}
		return x.Format(dateOnlyLayout)
	case dateOnly:
		return x.String()
	case *isoDateTime:
		if x == nil || x.IsZero() {
			return ""
		}
		return x.String()
	case isoDateTime:
		return x.String()
	default:
		return fmt.Sprint(x)
	}
}

// buildWorkbook 生成 xlsx 字节（首行表头）。
// JAVA 对照: ExcelUtil#getAbsoluteFile + Workbook.write（写 xlsx 字节）
func buildWorkbook(sheet string, cols []exportCol, rows [][]any) ([]byte, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()
	if err := f.SetSheetName("Sheet1", sheet); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	header := make([]any, len(cols))
	for i, col := range cols {
		header[i] = col.Title
	}
	if err := f.SetSheetRow(sheet, "A1", &header); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if len(rows) > excelMaxRows {
		rows = rows[:excelMaxRows]
	}
	for i, row := range rows {
		cell, err := excelize.CoordinatesToCellName(1, i+2)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		values := row
		if err := f.SetSheetRow(sheet, cell, &values); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
	}
	for i := range cols {
		name, err := excelize.ColumnNumberToName(i + 1)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		_ = f.SetColWidth(sheet, name, name, 18)
	}
	var buf bytes.Buffer
	if err := f.Write(&buf); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return buf.Bytes(), nil
}

// jsonTagIndex 建立 "json 名 -> 字段访问路径" 的索引（用于导出取值）。
func jsonTagIndex(t reflect.Type) map[string][]int {
	for t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	index := make(map[string][]int, t.NumField())
	var walk func(rt reflect.Type, prefix []int)
	walk = func(rt reflect.Type, prefix []int) {
		for i := 0; i < rt.NumField(); i++ {
			field := rt.Field(i)
			path := append(append([]int{}, prefix...), i)
			if field.Anonymous && field.Type.Kind() == reflect.Struct {
				walk(field.Type, path)
				continue
			}
			name := strings.Split(field.Tag.Get("json"), ",")[0]
			if name == "" || name == "-" {
				continue
			}
			index[name] = path
		}
	}
	walk(t, nil)
	return index
}

// fieldValue 读取结构体（或指针）上 json 名为 key 的字段值。
func fieldValue(row reflect.Value, index map[string][]int, key string) any {
	path, ok := index[key]
	if !ok {
		return nil
	}
	v := row
	for _, i := range path {
		for v.Kind() == reflect.Ptr {
			if v.IsNil() {
				return nil
			}
			v = v.Elem()
		}
		if v.Kind() != reflect.Struct || i >= v.NumField() {
			return nil
		}
		v = v.Field(i)
	}
	return v.Interface()
}

// buildRows 用反射把切片元素映射成单元格行。
// JAVA 对照: ExcelUtil#createExcelField 的字段取值（反射读 @Excel 属性）
func buildRows(dest any, cols []exportCol) [][]any {
	index := jsonTagIndex(reflectTypeOf(dest))
	var out [][]any
	v := reflect.ValueOf(dest)
	if v.Kind() != reflect.Ptr || v.IsNil() || v.Elem().Kind() != reflect.Slice {
		return out
	}
	slice := v.Elem()
	for i := 0; i < slice.Len(); i++ {
		rowValue := slice.Index(i).Interface()
		row := make([]any, len(cols))
		for j, col := range cols {
			row[j] = plainValue(fieldValue(reflect.ValueOf(rowValue), index, col.Field), col.DateOnly)
		}
		out = append(out, row)
	}
	return out
}

// exportTable 按 tableSpec 的条件导出全量数据（ExcelUtil 形态：写文件 + 返回文件名）。
func (h *handler) exportTable(c *gin.Context, spec *tableSpec, sheet string, cols []exportCol) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	h.exportWithClause(c, spec, clause, args, sheet, cols)
}

// exportWithClause 使用给定 WHERE 片段导出。
func (h *handler) exportWithClause(c *gin.Context, spec *tableSpec, clause string, args []any,
	sheet string, cols []exportCol) {
	dest := newSliceOf(spec.prototype)
	if _, err := h.list(context.Background(), listQuery{
		SelectSQL: spec.selectSQL,
		FromSQL:   "FROM " + spec.from() + " ",
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   spec.orderBy,
	}, dest); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data, err := buildWorkbook(sheet, cols, buildRows(dest, cols))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	h.exportResult(c, data, newUUIDDashed()+"_"+sheet+".xlsx", true)
}

// templateExport 以附件流返回 xlsx（EasyPOI 模板导出的形态）。
func (h *handler) templateExport(c *gin.Context, sheet string, cols []exportCol, rows [][]any) {
	data, err := buildWorkbook(sheet, cols, rows)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	h.exportResult(c, data, newUUID()+"_"+sheet+".xlsx", false)
}

// writeFile 写导出文件（ExcelUtil 的 profile/download 形态）。
func writeFile(path string, data []byte) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return nil
}

// cellValue 把 map 里的值转成单元格值（EasyPOI 模板导出用）。
func cellValue(m map[string]any, key string) any {
	v, ok := m[key]
	if !ok {
		return ""
	}
	switch x := v.(type) {
	case nil:
		return ""
	case float64:
		return x
	case bool:
		return x
	default:
		return fmt.Sprint(x)
	}
}

// dictCell 取字典标签，未命中时保留原值。
func dictCell(value any, dict map[string]string) any {
	key := ""
	switch x := value.(type) {
	case nil:
		return ""
	case string:
		key = x
	case float64:
		key = strconv.FormatFloat(x, 'f', -1, 64)
	default:
		key = fmt.Sprint(x)
	}
	if label, ok := dict[key]; ok {
		return label
	}
	return key
}
