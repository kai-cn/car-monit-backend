// JAVA 对照: com.ruoyi.common.utils.poi.ExcelUtil（@Excel 字段导出）
// JAVA 对照: EasyPOI TemplateExportParams 模板导出（附件流）
// 类/职责: manager 模块的 Excel 导出
// 对应 Go 文件: internal/modules/manager/excel_export.go
//
// DIFF: Java 用 POI/EasyPOI；Go 用 excelize。表头、列顺序与数据内容照抄，
// 单元格样式（边框/字体）做保守近似。
package manager

import (
	"bytes"
	"context"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/web"
)

// exportCol 描述导出的一列。
type exportCol struct {
	Title string
	Field string // 结构体 json 名
	Dict  string // 字典类型（值 -> 标签）
	Exp   string // @Excel(readConverterExp) 的值 -> 文案表达式
}

// convertByExp 对应 ExcelUtil.convertByExp：按 readConverterExp 把值替换成文案，未命中则原样返回。
//
// JAVA 对照: com/ruoyi/common/utils/poi/ExcelUtil.java convertByExp / separator(=)
func convertByExp(value, exp string) string {
	for _, item := range strings.Split(exp, ",") {
		kv := strings.SplitN(item, "=", 2)
		if len(kv) == 2 && kv[0] == value {
			return kv[1]
		}
	}
	return value
}

const excelMaxRows = 65536

// plainValue 把实体字段值转成可写入单元格的普通值。
func plainValue(v any) any {
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
		if x == nil || x.IsZero() {
			return ""
		}
		return x.String()
	case *dateOnly:
		if x == nil || x.IsZero() {
			return ""
		}
		return x.Format(dateOnlyLayout)
	case web.DateTime:
		if x.IsZero() {
			return ""
		}
		return x.String()
	default:
		return fmt.Sprint(x)
	}
}

// dictKey 把字段值转成字典 value 的字符串形态。
func dictKey(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case *string:
		if x == nil {
			return ""
		}
		return *x
	case string:
		return x
	case *int64:
		if x == nil {
			return ""
		}
		return strconv.FormatInt(*x, 10)
	case int64:
		return strconv.FormatInt(x, 10)
	case *float64:
		if x == nil {
			return ""
		}
		return strconv.FormatFloat(*x, 'f', -1, 64)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return fmt.Sprint(x)
	}
}

// buildWorkbook 生成 xlsx 字节（首行表头）。
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

// exportTable 按 tableSpec 的查询条件导出全量数据。
func (h *handler) exportTable(c *gin.Context, spec *tableSpec, fileName, sheet string, cols []exportCol, envelope bool) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	h.exportWithClause(c, spec, clause, args, fileName, sheet, cols, envelope, nil)
}

// exportWithClause 使用给定 WHERE 片段导出，transform 可在写表前改写行值。
func (h *handler) exportWithClause(c *gin.Context, spec *tableSpec, clause string, args []any,
	fileName, sheet string, cols []exportCol, envelope bool, transform func(values []any)) {
	dest := newSliceOf(spec.prototype)
	_, err := h.list(context.Background(), listQuery{
		SelectSQL: spec.selectSQL + spec.selectSuffix,
		FromSQL:   spec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   spec.orderBy,
	}, dest)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	dicts := make(map[string]map[string]string)
	for _, col := range cols {
		if col.Dict == "" {
			continue
		}
		if _, ok := dicts[col.Dict]; ok {
			continue
		}
		m, err := h.dictValueLabel(c.Request.Context(), col.Dict)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		dicts[col.Dict] = m
	}
	exportRows := buildExportRows(dest, cols, dicts, transform)
	data, err := buildWorkbook(sheet, cols, exportRows)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	_ = fileName // Java 的 ExcelUtil 用 sheet 名生成文件名；EasyPOI 用模板文件名
	h.exportResult(c, data, sheet, envelope)
}

// buildExportRows 用反射把切片元素映射成单元格行。
func buildExportRows(dest any, cols []exportCol, dicts map[string]map[string]string, transform func([]any)) [][]any {
	index := jsonTagIndex(reflectTypeOf(dest))
	var out [][]any
	err := forEachElement(dest, func(rowValue any) {
		row := make([]any, len(cols))
		for i, col := range cols {
			value := plainValue(fieldValueAny(rowValue, index, col.Field))
			if col.Exp != "" {
				value = convertByExp(dictKey(value), col.Exp)
			}
			if col.Dict != "" {
				raw := dictKey(fieldValueAny(rowValue, index, col.Field))
				if label, ok := dicts[col.Dict][raw]; ok {
					value = label
				}
			}
			row[i] = value
		}
		if transform != nil {
			transform(row)
		}
		out = append(out, row)
	})
	if err != nil {
		return nil
	}
	return out
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

// downloadAttachment 以附件流返回字节（EasyPOI 模板导出的形态）。
func downloadAttachment(c *gin.Context, fileName string, data []byte) {
	c.Header("Content-Type", "application/octet-stream;charset=UTF-8")
	c.Header("Content-Disposition", "attachment; filename="+fileName)
	c.Data(http.StatusOK, "application/octet-stream", data)
}
