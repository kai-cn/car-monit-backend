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
	"time"

	"github.com/gin-gonic/gin"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/excelx"
	"car-monit-go/internal/web"
)

// exportCol 描述导出的一列。
type exportCol struct {
	Title string
	Field string // 结构体 json 名
	Dict  string // 字典类型（值 -> 标签）
	Exp   string // @Excel(readConverterExp) 的值 -> 文案表达式
	// BlankOnMiss: EasyPOI 模板导出的字典前置翻译走 CommonUtil.isNull(map.get(code))，
	// 未命中给空串；ExcelUtil 的 @Excel(dictType) 走另一套（未命中保留原值），两者不能混。
	BlankOnMiss bool
	// Money: Java 侧 decimal(x,2) 映射成 BigDecimal，模板导出写 String.valueOf 恒带两位小数。
	Money bool
	// JavaDate: 字段在 Java 里是 java.util.Date 且模板不做格式化 ⇒ 落 Date#toString()。
	JavaDate bool
	// Stamp: 字段在 Java 里是 java.sql.Timestamp（BasePlusEntity.createTime）⇒ 落 Timestamp#toString()。
	Stamp bool
}

// javaDateText 对应 java.util.Date#toString()：形如 Thu Aug 21 00:00:00 CST 2025。
// 时区名硬编码 CST：DSN 是 loc=Local（+08:00），而 Windows 下 Go 的本地时区缩写可能是全称。
func javaDateText(t time.Time) string {
	return t.Format("Mon Jan 02 15:04:05") + " CST " + t.Format("2006")
}

// stampText 对应 java.sql.Timestamp#toString()：小数秒去掉尾零、至少保留 1 位
// （2025-12-18 11:19:27.0 / 2026-02-03 16:19:19.572）。
func stampText(t time.Time) string {
	base := t.Format("2006-01-02 15:04:05")
	nanos := t.Nanosecond()
	if nanos == 0 {
		return base + ".0"
	}
	return base + "." + strings.TrimRight(fmt.Sprintf("%09d", nanos), "0")
}

// stampOf / javaDateOf 给手工拼行的导出点用：接受实体里的日期字段形态
// （*web.DateTime、web.DateTime、*dateOnly、dateOnly），空值给空串。
func javaDateOf(v any) string {
	if t, ok := timeValue(v); ok {
		return javaDateText(t)
	}
	return ""
}

func stampOf(v any) string {
	if t, ok := timeValue(v); ok {
		return stampText(t)
	}
	return ""
}

// moneyText 对应 BigDecimal 的 String.valueOf：只给两位小数，nil 给空串。
func moneyText(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case *float64:
		if x == nil {
			return ""
		}
		return strconv.FormatFloat(*x, 'f', 2, 64)
	case float64:
		return strconv.FormatFloat(x, 'f', 2, 64)
	case *int64:
		if x == nil {
			return ""
		}
		return strconv.FormatFloat(float64(*x), 'f', 2, 64)
	case int64:
		return strconv.FormatFloat(float64(x), 'f', 2, 64)
	default:
		return ""
	}
}

// moneySumText 对应「BigDecimal.ZERO 起算、再 add(decimal(x,2))」的聚合金额：
// 一行都没累加到时是 scale 0 的 0（打印 "0"），累加过则恒两位小数。
func moneySumText(v any) string {
	s := moneyText(v)
	if s == "0.00" {
		return "0"
	}
	return s
}

// convertByExp 对应 ExcelUtil.convertByExp：未命中返回空串（Java 的 propertyString 兜底就是空）。
//
// JAVA 对照: com/ruoyi/common/utils/poi/ExcelUtil.java convertByExp / separator(=)
func convertByExp(value, exp string) string {
	return excelx.ConvertByExp(value, exp)
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
	header := make([]any, len(cols))
	for i, col := range cols {
		header[i] = col.Title
	}
	return buildStaticWorkbook(sheet, [][]any{header}, rows)
}

// buildStaticWorkbook 写「静态行 + 数据行」。静态行由调用方原样给出：
// EasyPOI 模板导出的表头可能是多行（报表标题行、列名行、副表头行），
// 每一格都过一遍 plainValue，避免调用方把 GORM 模型的 *string 直接塞进单元格
// （写出来就是 0xc000… 的指针地址）。
func buildStaticWorkbook(sheet string, static [][]any, rows [][]any) ([]byte, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()
	if err := f.SetSheetName("Sheet1", sheet); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	width := 0
	for i, line := range static {
		cell, err := excelize.CoordinatesToCellName(1, i+1)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		values := normalizeRow(line)
		if len(values) > width {
			width = len(values)
		}
		if err := f.SetSheetRow(sheet, cell, &values); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
	}
	if len(rows) > excelMaxRows {
		rows = rows[:excelMaxRows]
	}
	for i, row := range rows {
		cell, err := excelize.CoordinatesToCellName(1, len(static)+i+1)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		values := normalizeRow(row)
		if len(values) > width {
			width = len(values)
		}
		if err := f.SetSheetRow(sheet, cell, &values); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
	}
	for i := 0; i < width; i++ {
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

func normalizeRow(row []any) []any {
	out := make([]any, len(row))
	for i, v := range row {
		// ExcelUtil 的 = - + @ 前补 TAB 规则只属于 ExcelUtil 形态；manager 这些端点
		// 是 EasyPOI 模板导出，只需要指针解引用 + 非法 XML 字符 + 超长置空。
		out[i] = excelx.Cell(plainValue(v))
	}
	return out
}

// exportTable 按 tableSpec 的查询条件导出全量数据。
func (h *handler) exportTable(c *gin.Context, spec *tableSpec, fileName, sheet string, cols []exportCol, envelope bool) {
	clause, args := buildWhere(c, spec.prefix(), spec.conditions)
	h.exportWithClause(c, spec, clause, args, fileName, sheet, cols, envelope, nil)
}

// exportWithClause 使用给定 WHERE 片段导出，transform 可在写表前改写行值。
func (h *handler) exportWithClause(c *gin.Context, spec *tableSpec, clause string, args []any,
	fileName, sheet string, cols []exportCol, envelope bool, transform func(values []any)) {
	rows, err := h.exportQuery(c.Request.Context(), spec, clause, args, web.PageDomain{}, cols, transform, nil)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	h.writeExport(c, sheet, cols, rows, fileName, envelope)
}

// exportQuery 跑导出查询并展开成单元格行。Java 侧只有少数控制器在导出前调 startPage()，
// 所以默认不分页；prepare 用来在展开前把派生字段（例如「A至B」拼接）写回实体。
func (h *handler) exportQuery(ctx context.Context, spec *tableSpec, clause string, args []any,
	page web.PageDomain, cols []exportCol, transform func(values []any), prepare func(dest any)) ([][]any, error) {
	dest := newSliceOf(spec.prototype)
	if _, err := h.list(ctx, listQuery{
		SelectSQL: spec.selectSQL + spec.selectSuffix,
		FromSQL:   spec.from(),
		Where:     &whereClause{clause: clause, args: args},
		OrderBy:   orderFor(spec.orderBy, page),
		Page:      page,
	}, dest); err != nil {
		return nil, err
	}
	if prepare != nil {
		prepare(dest)
	}
	dicts := make(map[string]map[string]string)
	for _, col := range cols {
		if col.Dict == "" {
			continue
		}
		if _, ok := dicts[col.Dict]; ok {
			continue
		}
		m, err := h.dictValueLabel(ctx, col.Dict)
		if err != nil {
			return nil, err
		}
		dicts[col.Dict] = m
	}
	return buildExportRows(dest, cols, dicts, transform), nil
}

// writeExport 生成 xlsx 并按 Java 的附件流返回。
func (h *handler) writeExport(c *gin.Context, sheet string, cols []exportCol, rows [][]any,
	fileName string, envelope bool) {
	data, err := buildWorkbook(sheet, cols, rows)
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
			raw := fieldValueAny(rowValue, index, col.Field)
			value := plainValue(raw)
			if col.Exp != "" {
				value = convertByExp(dictKey(value), col.Exp)
			}
			if col.Dict != "" {
				if label, ok := dicts[col.Dict][dictKey(raw)]; ok {
					value = label
				} else if col.BlankOnMiss {
					value = ""
				}
			}
			switch {
			case col.Money:
				value = moneyText(raw)
			case col.JavaDate:
				if t, ok := timeValue(raw); ok {
					value = javaDateText(t)
				} else {
					value = ""
				}
			case col.Stamp:
				if t, ok := timeValue(raw); ok {
					value = stampText(t)
				} else {
					value = ""
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

// timeValue 取出日期字段里的 time.Time（含指针形态），零值/空值算没有。
func timeValue(v any) (time.Time, bool) {
	switch x := v.(type) {
	case *web.DateTime:
		if x == nil || x.IsZero() {
			return time.Time{}, false
		}
		return x.Time, true
	case web.DateTime:
		if x.IsZero() {
			return time.Time{}, false
		}
		return x.Time, true
	case *dateOnly:
		if x == nil || x.IsZero() {
			return time.Time{}, false
		}
		return x.Time, true
	case dateOnly:
		if x.IsZero() {
			return time.Time{}, false
		}
		return x.Time, true
	}
	return time.Time{}, false
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
