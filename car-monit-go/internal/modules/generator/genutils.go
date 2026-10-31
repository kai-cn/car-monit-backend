// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/util/GenUtils.java
// 类/职责: 表/列初始化与 Java 命名推导
// 对应 Go 文件: internal/modules/generator/genutils.go
//
// DIFF: Java 静态方法直接读 GenConfig 的静态字段；Go 把 genConfig 显式传入，
// 便于测试与多实例（值与 configs/generator.yml 一致）。
package generator

import (
	"strconv"
	"strings"
)

// initTable 对应 GenUtils.initTable。
func initTable(cfg genConfig, table *GenTable, operName string) {
	table.ClassName = strPtr(convertClassName(cfg, strVal(table.TableName)))
	table.PackageName = strPtr(cfg.PackageName)
	table.ModuleName = strPtr(getModuleName(cfg.PackageName))
	table.BusinessName = strPtr(getBusinessName(strVal(table.TableName)))
	table.FunctionName = strPtr(replaceTextJava(strVal(table.TableComment)))
	table.FunctionAuthor = strPtr(cfg.Author)
	table.CreateBy = strPtr(operName)
}

// initColumnField 对应 GenUtils.initColumnField。
func initColumnField(column *GenTableColumn, table *GenTable) {
	dataType := getDbType(strVal(column.ColumnType))
	columnName := strVal(column.ColumnName)
	column.TableID = table.TableID
	column.CreateBy = table.CreateBy
	column.JavaField = strPtr(toCamelCase(columnName))
	column.JavaType = strPtr(typeString)

	switch {
	case arraysContains(columnTypeStr, dataType) || arraysContains(columnTypeText, dataType):
		columnLength := getColumnLength(strVal(column.ColumnType))
		htmlType := htmlInput
		if columnLength >= 500 || arraysContains(columnTypeText, dataType) {
			htmlType = htmlTextarea
		}
		column.HtmlType = strPtr(htmlType)
	case arraysContains(columnTypeTime, dataType):
		column.JavaType = strPtr(typeDate)
		column.HtmlType = strPtr(htmlDatetime)
	case arraysContains(columnTypeNumber, dataType):
		column.HtmlType = strPtr(htmlInput)
		parts := splitJavaComma(substringBetween(strVal(column.ColumnType), "(", ")"))
		if len(parts) == 2 && atoiOrZero(parts[1]) > 0 {
			column.JavaType = strPtr(typeBigDecimal)
		} else if len(parts) == 1 && atoiOrZero(parts[0]) <= 10 {
			column.JavaType = strPtr(typeInteger)
		} else {
			column.JavaType = strPtr(typeLong)
		}
	}

	column.IsInsert = strPtr(require)

	if !arraysContains(columnNameNotEdit, columnName) && !column.IsPrimaryKey() {
		column.IsEdit = strPtr(require)
	}
	if !arraysContains(columnNameNotList, columnName) && !column.IsPrimaryKey() {
		column.IsList = strPtr(require)
	}
	if !arraysContains(columnNameNotQuery, columnName) && !column.IsPrimaryKey() {
		column.IsQuery = strPtr(require)
	}

	if endsWithIgnoreCase(columnName, "name") {
		column.QueryType = strPtr(queryLike)
	}
	switch {
	case endsWithIgnoreCase(columnName, "status"):
		column.HtmlType = strPtr(htmlRadio)
	case endsWithIgnoreCase(columnName, "type") || endsWithIgnoreCase(columnName, "sex"):
		column.HtmlType = strPtr(htmlSelect)
	case endsWithIgnoreCase(columnName, "image"):
		column.HtmlType = strPtr(htmlImageUpload)
	case endsWithIgnoreCase(columnName, "file"):
		column.HtmlType = strPtr(htmlFileUpload)
	case endsWithIgnoreCase(columnName, "content"):
		column.HtmlType = strPtr(htmlEditor)
	}
}

func arraysContains(values []string, target string) bool {
	for _, value := range values {
		if value == target {
			return true
		}
	}
	return false
}

func endsWithIgnoreCase(s, suffix string) bool {
	return strings.HasSuffix(strings.ToLower(s), strings.ToLower(suffix))
}

// getModuleName 对应 GenUtils.getModuleName（包名最后一个点之后）。
func getModuleName(packageName string) string {
	return packageName[strings.LastIndex(packageName, ".")+1:]
}

// getBusinessName 对应 GenUtils.getBusinessName（表名最后一个下划线之后）。
func getBusinessName(tableName string) string {
	return tableName[strings.LastIndex(tableName, "_")+1:]
}

// convertClassName 对应 GenUtils.convertClassName。
func convertClassName(cfg genConfig, tableName string) string {
	if cfg.AutoRemovePre && cfg.TablePrefix != "" {
		tableName = replaceFirstByPrefix(tableName, splitJava(cfg.TablePrefix, ","))
	}
	return convertToCamelCase(tableName)
}

// replaceFirstByPrefix 对应 GenUtils.replaceFirst（Java String.replaceFirst 是正则）。
func replaceFirstByPrefix(text string, searchList []string) string {
	for _, search := range searchList {
		if strings.HasPrefix(text, search) {
			return replaceFirstJava(text, search)
		}
	}
	return text
}

// getDbType 对应 GenUtils.getDbType。
func getDbType(columnType string) string {
	if idx := strings.Index(columnType, "("); idx > 0 {
		return columnType[:idx]
	}
	return columnType
}

// getColumnLength 对应 GenUtils.getColumnLength。
func getColumnLength(columnType string) int {
	if idx := strings.Index(columnType, "("); idx > 0 {
		if length := substringBetween(columnType, "(", ")"); length != nil {
			return atoiOrZero(*length)
		}
	}
	return 0
}

func atoiOrZero(s string) int {
	v, err := strconv.Atoi(strings.TrimSpace(s))
	if err != nil {
		return 0
	}
	return v
}
