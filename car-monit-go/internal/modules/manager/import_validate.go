// JAVA 对照: com.ruoyi.web.util.ImportUtil#importExcel + ImportSysUtil#getErrorBO + ImportEntity
// 类/职责: Excel 导入的通用逐列校验（规则 1..8）与错误对象形状
// 对应 Go 文件: internal/modules/manager/import_validate.go
package manager

import (
	"regexp"
	"strings"
)

// JAVA 对照: ImportErrorEntity 只有 rowNo/colName/message 三个字段被序列化出去。
type importError struct {
	RowNum  int    `json:"rowNo"`
	ColName string `json:"colName"`
	Message string `json:"message"`
}

// importErrorAt 对应 importUtil.getErrorBO(index+1, col, msg)：
// getErrorBO 内部又 row+1，所以首条数据（index 0）报的是 rowNo 2，与表格行号无关。
func importErrorAt(index int, colName, message string) importError {
	return importError{RowNum: index + 2, ColName: colName, Message: message}
}

// importCol 对应 ImportEntity 的 (colName, valadRes)。valadRes 用逗号分隔多个规则。
type importCol struct {
	Name  string
	Rules string
}

// JAVA 对照: ImportUtil 里的 5 个正则 + 数值正则。Java 用 Pattern.matches（全串匹配），
// 所以 Go 这边给没锚点的 eLtime2 补上 ^$；Java 的 elTimeYM 里 \- \/ \. 在 Go 里写成裸字符。
var (
	ruleDecimal  = regexp.MustCompile(`^(-?\d+)(\.\d+)?$`)
	ruleInteger  = regexp.MustCompile(`^[0-9]*$`)
	ruleDate     = regexp.MustCompile(`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`)
	ruleIDCard   = regexp.MustCompile(`^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X|x)$`)
	ruleYearMon  = regexp.MustCompile(`^\d{4}(-|/|\.)\d{1,2}$`)
	ruleNumber   = regexp.MustCompile(`^(-|\+)?\d+(\.\d+)?$`)
	ruleDateTime = regexp.MustCompile(`^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$`)
)

// collectImportRows 对应 dataRtnExcel07/08 的读行段：从首个数据行开始，遇到终止行就停。
func collectImportRows(rows [][]string) [][]string {
	out := make([][]string, 0, len(rows))
	for _, row := range rows {
		if endOfImportSheet(row) {
			break
		}
		out = append(out, row)
	}
	return out
}

// importColNames 取模板表头，对应 Java 用 gzList 拼 colsName 供 colVdaExcel07/08 校验。
func importColNames(cols []importCol) []string {
	out := make([]string, len(cols))
	for i, col := range cols {
		out[i] = col.Name
	}
	return out
}

// importCells 对应 getCellFormatValue08 + isNull：按列位取值，缺列当空串，两侧都 trim。
func importCells(row []string, n int) []string {
	out := make([]string, n)
	for i := range out {
		if i < len(row) {
			out[i] = strings.TrimSpace(row[i])
		}
	}
	return out
}

// endOfImportSheet 对应 dataRtnExcel07/08 的两条提前收尾：首格是 break/结束，
// 或者这一行根本没有 <row> 元素（POI 的 getRow(i) 为 null，取 getLastCellNum 抛 NPE 后 break）。
// 注意「有行但全是空格」不算收尾：POI 会把它当一行数据送去校验，报一串「不能为空」。
func endOfImportSheet(row []string) bool {
	if len(row) == 0 {
		return true
	}
	first := strings.TrimSpace(row[0])
	return first == "break" || first == "结束"
}

// validateImportRow 对应 ImportUtil.importExcel 的校验段：
// 规则 1 必填；其余只在值非空时检查，且按 if/else-if 链只报第一条命中的错。
func validateImportRow(errList *[]importError, cols []importCol, index int, vals []string) {
	for i, col := range cols {
		value := ""
		if i < len(vals) {
			value = strings.TrimSpace(vals[i])
		}
		if strings.TrimSpace(col.Rules) == "" {
			continue
		}
		for _, rule := range strings.Split(col.Rules, ",") {
			if rule == "1" && value == "" {
				*errList = append(*errList, importErrorAt(index, col.Name, "不能为空"))
			}
			if value == "" {
				continue
			}
			switch rule {
			case "2":
				if !ruleDecimal.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "不是小数"))
				}
			case "3":
				if !ruleInteger.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "不是正整数"))
				}
			case "4":
				if !ruleDate.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "日期格式（年-月-日）不正确"))
				}
			case "5":
				if !ruleIDCard.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "身份证号码不正确"))
				}
			case "6":
				if !ruleYearMon.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "日期格式（年-月）不正确"))
				}
			case "7":
				if !ruleNumber.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "不是数值"))
				}
			case "8":
				if !ruleDateTime.MatchString(value) {
					*errList = append(*errList, importErrorAt(index, col.Name, "日期格式（年月日时分秒）不正确"))
				}
			}
		}
	}
}

// carInfoImportCols 对应 CarInfoController.initList()，属性顺序即列顺序。
var carInfoImportCols = []importCol{
	{Name: "车牌颜色", Rules: "1"},
	{Name: "车牌号", Rules: "1"},
	{Name: "车型", Rules: "1"},
	{Name: "车种", Rules: ""},
	{Name: "轴数", Rules: "3"},
	{Name: "逃费类型", Rules: "1"},
	{Name: "逃费金额（元）", Rules: "2"},
	{Name: "备注", Rules: ""},
}

// exceptImportCols 对应 CarExceptRecordController.initListTwo()。
// 空表头是模板里的合并单元格残留，Java 照样拿它当 colName 报错。
var exceptImportCols = []importCol{
	{Name: "序号", Rules: ""},
	{Name: "出口收费站", Rules: ""},
	{Name: "出口时间", Rules: "1,8"},
	{Name: "通行PASSID", Rules: ""},
	{Name: "车牌", Rules: "1"},
	{Name: "交易车型", Rules: ""},
	{Name: "车种", Rules: ""},
	{Name: "入口站", Rules: ""},
	{Name: "入口时间", Rules: "1,8"},
	{Name: "漏交通行费类型", Rules: ""},
	{Name: "", Rules: "1"}, // escapedType
	{Name: "交易金额", Rules: ""},
	{Name: "", Rules: ""},
	{Name: "", Rules: "1,2"}, // chargeAmount
	{Name: "应交金额", Rules: ""},
	{Name: "", Rules: ""},
	{Name: "", Rules: "1,2"}, // totalAmount
	{Name: "实际追交金额", Rules: ""},
	{Name: "", Rules: ""},
	{Name: "", Rules: ""},
	{Name: "备注", Rules: ""},
}
