// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java:509-526,634-656,1383-1403
// JAVA 对照: com/ruoyi/common/annotation/Excel.java
// 类/职责: Excel 导出子集 — exportExcel(List, sheetName) / encodingFilename / getAbsoluteFile
// 对应 Go 文件: internal/modules/ops/excel.go
//
// DIFF: Java 用 Apache POI 逐行写单元格并套用 ExcelUtil 的完整样式（标题行高、边框、统计行、
// 列宽按内容自适应）；Go 侧只保证 **表头文案、列顺序、单元格取值、文件名规则** 与 Java 一致，
// 样式用 excelize 做近似（灰色表头 + 加粗居中 + 细边框），不做统计行。
// DIFF: 日期列在 Java 里写成带 dataFormat 的日期单元格；这里写成已格式化的字符串
// （"yyyy-MM-dd HH:mm:ss"），显示效果相同，但单元格类型是文本。
// DIFF: Java 的 `exportExcel()` 把文件写到 RuoYiConfig.getDownloadPath() 并返回
// AjaxResult.success(filename)（文件名落在 msg），前端再调 /common/download 取文件；
// Go 侧保留同一套两段式流程，filename 规则完全一致（UUID_工作表名.xlsx）。
package ops

import (
	"os"
	"path/filepath"
	"time"

	"github.com/google/uuid"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/app"
	"car-monit-go/internal/excelx"
	"car-monit-go/internal/web"
)

// excelColumn 对应 @Excel(name, width)。
type excelColumn struct {
	Name  string
	Width float64
}

const (
	excelDefaultWidth = 16 // Excel.width() 默认值附近；Java 注释默认 16
	excelDateWidth    = 30 // 日期列 @Excel(width = 30)
)

// exportExcel 等价 ExcelUtil.exportExcel(List, sheetName)：落盘并返回文件名。
func exportExcel(a *app.App, sheetName string, columns []excelColumn, rows [][]any) (*web.AjaxResult, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()

	// Java 用 sheetName 作为唯一工作表名。
	if err := f.SetSheetName("Sheet1", sheetName); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}

	headerStyle, err := f.NewStyle(&excelize.Style{
		Font:      &excelize.Font{Bold: true},
		Alignment: &excelize.Alignment{Horizontal: "center", Vertical: "center"},
		Border: []excelize.Border{
			{Type: "left", Color: "000000", Style: 1},
			{Type: "top", Color: "000000", Style: 1},
			{Type: "bottom", Color: "000000", Style: 1},
			{Type: "right", Color: "000000", Style: 1},
		},
		Fill: excelize.Fill{Type: "pattern", Pattern: 1, Color: []string{"D0D0D0"}},
	})
	if err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}

	for i, col := range columns {
		cell, err := excelize.CoordinatesToCellName(i+1, 1)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		if err := f.SetCellValue(sheetName, cell, col.Name); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		if err := f.SetCellStyle(sheetName, cell, cell, headerStyle); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		width := col.Width
		if width <= 0 {
			width = excelDefaultWidth
		}
		if colName, err := excelize.ColumnNumberToName(i + 1); err == nil {
			_ = f.SetColWidth(sheetName, colName, colName, width)
		}
	}

	for r, row := range rows {
		for i, value := range row {
			cell, err := excelize.CoordinatesToCellName(i+1, r+2)
			if err != nil {
				return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
			}
			if err := f.SetCellValue(sheetName, cell, excelx.UtilCell(value)); err != nil {
				return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
			}
		}
	}

	filename := encodingFilename(sheetName)
	path := a.Cfg.RuoYi.DownloadPath() + filename
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if err := f.SaveAs(path); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	// Java: AjaxResult.success(String filename) -> 文件名进 msg。
	return web.SuccessMsg(filename), nil
}

// encodingFilename 对应 ExcelUtil.encodingFilename：UUID_工作表名.xlsx。
func encodingFilename(sheetName string) string {
	return uuid.NewString() + "_" + sheetName + ".xlsx"
}

// excelDate 把 DateTime 格式化成 Java 的 yyyy-MM-dd HH:mm:ss；nil 输出空串。
func excelDate(dt *web.DateTime) string {
	if dt == nil || dt.IsZero() {
		return ""
	}
	return dt.Format("2006-01-02 15:04:05")
}

// excelTime 同上，入参是 time.Time（服务器监控等场景）。
func excelTime(t time.Time) string {
	if t.IsZero() {
		return ""
	}
	return t.Format("2006-01-02 15:04:05")
}

// convertByExp 对应 ExcelUtil.convertByExp（readConverterExp="0=成功,1=失败"）：
// 命中给文案，未命中给空串 —— Java 的 convertByExp 兜底是 stripEnd("")，不是原值。
func convertByExp(value int, exp map[int]string) string {
	return exp[value]
}

// BusinessType 中文文案（BizType.OTHER 等）。
// JAVA 对照: com/ruoyi/common/enums/BusinessType.java
var businessTypeLabels = map[int]string{
	0: "其它",
	1: "新增",
	2: "修改",
	3: "删除",
	4: "授权",
	5: "导出",
	6: "导入",
	7: "强退",
	8: "生成代码",
	9: "清空数据",
}

// operatorTypeLabels 对应 @Excel(readConverterExp = "0=其它,1=后台用户,2=手机端用户")。
var operatorTypeLabels = map[int]string{
	0: "其它",
	1: "后台用户",
	2: "手机端用户",
}

// operStatusLabels 对应 @Excel(name = "状态", readConverterExp = "0=正常,1=异常")。
var operStatusLabels = map[int]string{
	0: "正常",
	1: "异常",
}

// loginStatusLabels 对应 @Excel(name = "登录状态", readConverterExp = "0=成功,1=失败")。
var loginStatusLabels = map[int]string{
	0: "成功",
	1: "失败",
}
