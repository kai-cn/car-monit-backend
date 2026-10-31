// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/util/VelocityUtils.java
// 类/职责: 模板上下文 / 模板清单 / 输出文件名
// 对应 Go 文件: internal/modules/generator/velocity_utils.go
//
// DIFF: Java 用 fastjson2 解析 gen_table.options；Go 用 encoding/json，
// 非法 JSON 同样报错（500），空串/缺失按 null 处理。
package generator

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

// prepareContext 对应 VelocityUtils.prepareContext。
func prepareContext(table *GenTable) (*velocityContext, error) {
	packageName := strVal(table.PackageName)
	ctx := newVelocityContext()
	ctx.Put("tplCategory", derefString(table.TplCategory))
	ctx.Put("tableName", derefString(table.TableName))
	functionName := strVal(table.FunctionName)
	if functionName == "" {
		functionName = defaultFunctionName
	}
	ctx.Put("functionName", functionName)
	ctx.Put("ClassName", derefString(table.ClassName))
	ctx.Put("className", uncapitalize(strVal(table.ClassName)))
	ctx.Put("moduleName", derefString(table.ModuleName))
	ctx.Put("BusinessName", capitalize(strVal(table.BusinessName)))
	ctx.Put("businessName", derefString(table.BusinessName))
	ctx.Put("basePackage", getPackagePrefix(packageName))
	ctx.Put("packageName", packageName)
	ctx.Put("author", derefString(table.FunctionAuthor))
	ctx.Put("datetime", time.Now().Format("2006-01-02"))
	ctx.Put("pkColumn", table.PkColumn)
	ctx.Put("importList", getImportList(table).ToList())
	ctx.Put("permissionPrefix", getPermissionPrefix(strVal(table.ModuleName), strVal(table.BusinessName)))
	ctx.Put("columns", table.Columns)
	ctx.Put("table", table)
	ctx.Put("dictionaryListKeySuffix", derefString(table.DictionaryListKeySuffix))
	ctx.Put("dictionaryInfoList", table.DictionaryInfoList)
	ctx.Put("dictionaryInfoString", derefString(table.DictionaryInfoString))
	ctx.Put("uploadInfo", table.UploadInfo)
	ctx.Put("richTextInfo", table.RichTextInfo)
	ctx.Put("columnDialogInfo", table.ColumnDialogInfo)
	ctx.Put("filterColumnList", table.FilterColumnList)

	if err := setMenuVelocityContext(ctx, table); err != nil {
		return nil, err
	}
	if strVal(table.TplCategory) == tplTree {
		if err := setTreeVelocityContext(ctx, table); err != nil {
			return nil, err
		}
	}
	if strVal(table.TplCategory) == tplSub {
		if err := setSubVelocityContext(ctx, table); err != nil {
			return nil, err
		}
	}
	return ctx, nil
}

// setMenuVelocityContext 对应 VelocityUtils.setMenuVelocityContext。
func setMenuVelocityContext(ctx *velocityContext, table *GenTable) error {
	params, err := parseJSONObject(table.Options)
	if err != nil {
		return err
	}
	ctx.Put("parentMenuId", getParentMenuID(params))
	return nil
}

// setTreeVelocityContext 对应 VelocityUtils.setTreeVelocityContext。
func setTreeVelocityContext(ctx *velocityContext, table *GenTable) error {
	params, err := parseJSONObject(table.Options)
	if err != nil {
		return err
	}
	if params == nil {
		return fmt.Errorf("velocity: 树表缺少 options")
	}
	ctx.Put("treeCode", getTreeCode(params))
	ctx.Put("treeParentCode", getTreeParentCode(params))
	ctx.Put("treeName", getTreeName(params))
	ctx.Put("expandColumn", int64(getExpandColumn(table, params)))
	if value, ok := params[treeParentCode]; ok {
		ctx.Put("tree_parent_code", jsonToString(value))
	}
	if value, ok := params[treeName]; ok {
		ctx.Put("tree_name", jsonToString(value))
	}
	return nil
}

// setSubVelocityContext 对应 VelocityUtils.setSubVelocityContext。
func setSubVelocityContext(ctx *velocityContext, table *GenTable) error {
	subTable := table.SubTable
	if subTable == nil {
		return fmt.Errorf("velocity: 主子表未加载子表")
	}
	subTableFkClassName := convertToCamelCase(strVal(table.SubTableFkName))
	ctx.Put("subTable", subTable)
	ctx.Put("subTableName", derefString(table.SubTableName))
	ctx.Put("subTableFkName", derefString(table.SubTableFkName))
	ctx.Put("subTableFkClassName", subTableFkClassName)
	ctx.Put("subTableFkclassName", uncapitalize(subTableFkClassName))
	ctx.Put("subClassName", derefString(subTable.ClassName))
	ctx.Put("subclassName", uncapitalize(strVal(subTable.ClassName)))
	ctx.Put("subImportList", getImportList(subTable).ToList())
	return nil
}

// getTemplateList 对应 VelocityUtils.getTemplateList。
func getTemplateList(tplCategory *string, mybatisPlus bool) []string {
	vm := "vm"
	if mybatisPlus {
		vm = "vmplus"
	}
	templates := []string{
		vm + "/java/domain.java.vm",
		vm + "/java/mapper.java.vm",
		vm + "/java/service.java.vm",
		vm + "/java/serviceImpl.java.vm",
		vm + "/java/controller.java.vm",
		vm + "/xml/mapper.xml.vm",
		vm + "/sql/sql.vm",
		vm + "/js/api.js.vm",
	}
	switch strVal(tplCategory) {
	case tplCrud:
		templates = append(templates, vm+"/vue/index.vue.vm", vm+"/vue/index-form.vue.vm")
	case tplTree:
		templates = append(templates, vm+"/vue/index-tree.vue.vm")
	case tplSub:
		templates = append(templates, vm+"/vue/index.vue.vm", vm+"/java/sub-domain.java.vm")
	}
	return templates
}

// getFileName 对应 VelocityUtils.getFileName。
func getFileName(template string, table *GenTable) string {
	fileName := ""
	packageName := strVal(table.PackageName)
	moduleName := strVal(table.ModuleName)
	className := strVal(table.ClassName)
	businessName := strVal(table.BusinessName)

	javaPath := projectPath + "/" + strings.ReplaceAll(packageName, ".", "/")
	mapperPath := mybatisPath + "/" + moduleName
	vuePath := "vue"

	if strings.Contains(template, "domain.java.vm") {
		fileName = fmt.Sprintf("%s/domain/%s.java", javaPath, className)
	}
	if strings.Contains(template, "sub-domain.java.vm") && strVal(table.TplCategory) == tplSub {
		fileName = fmt.Sprintf("%s/domain/%s.java", javaPath, strVal(table.SubTable.ClassName))
	} else if strings.Contains(template, "mapper.java.vm") {
		fileName = fmt.Sprintf("%s/mapper/%sMapper.java", javaPath, className)
	} else if strings.Contains(template, "service.java.vm") {
		fileName = fmt.Sprintf("%s/service/I%sService.java", javaPath, className)
	} else if strings.Contains(template, "serviceImpl.java.vm") {
		fileName = fmt.Sprintf("%s/service/impl/%sServiceImpl.java", javaPath, className)
	} else if strings.Contains(template, "controller.java.vm") {
		fileName = fmt.Sprintf("%s/controller/%sController.java", javaPath, className)
	} else if strings.Contains(template, "mapper.xml.vm") {
		fileName = fmt.Sprintf("%s/%sMapper.xml", mapperPath, className)
	} else if strings.Contains(template, "sql.vm") {
		fileName = businessName + "Menu.sql"
	} else if strings.Contains(template, "api.js.vm") {
		fileName = fmt.Sprintf("%s/api/%s/%s.js", vuePath, moduleName, businessName)
	} else if strings.Contains(template, "index.vue.vm") {
		fileName = fmt.Sprintf("%s/views/%s/%s/index.vue", vuePath, moduleName, businessName)
	} else if strings.Contains(template, "index-form.vue.vm") {
		fileName = fmt.Sprintf("%s/views/%s/%s/index-form.vue", vuePath, moduleName, businessName)
	} else if strings.Contains(template, "index-tree.vue.vm") {
		fileName = fmt.Sprintf("%s/views/%s/%s/index.vue", vuePath, moduleName, businessName)
	}
	return fileName
}

// getPackagePrefix 对应 VelocityUtils.getPackagePrefix。
func getPackagePrefix(packageName string) string {
	lastIndex := strings.LastIndex(packageName, ".")
	if lastIndex == -1 {
		return packageName
	}
	return packageName[:lastIndex]
}

// getImportList 对应 VelocityUtils.getImportList（HashSet，迭代顺序为桶序）。
func getImportList(table *GenTable) *javaHashSet {
	imports := newJavaHashSet()
	if table.SubTable != nil {
		imports.Add("java.util.List")
	}
	for _, column := range table.Columns {
		if column.IsSuperColumn() {
			continue
		}
		switch strVal(column.JavaType) {
		case typeDate:
			imports.Add("java.util.Date")
			imports.Add("com.fasterxml.jackson.annotation.JsonFormat")
		case typeBigDecimal:
			imports.Add("java.math.BigDecimal")
		}
	}
	return imports
}

// getPermissionPrefix 对应 VelocityUtils.getPermissionPrefix。
func getPermissionPrefix(moduleName, businessName string) string {
	return moduleName + ":" + businessName
}

// getParentMenuID 对应 VelocityUtils.getParentMenuId。
func getParentMenuID(params map[string]any) any {
	if len(params) > 0 {
		if value, ok := params[parentMenuID]; ok {
			return jsonToString(value)
		}
	}
	return defaultParentMenuID
}

func getTreeCode(params map[string]any) any {
	if value, ok := params[treeCode]; ok {
		return optionalToCamelCase(jsonToString(value))
	}
	return ""
}

func getTreeParentCode(params map[string]any) any {
	if value, ok := params[treeParentCode]; ok {
		return optionalToCamelCase(jsonToString(value))
	}
	return ""
}

func getTreeName(params map[string]any) any {
	if value, ok := params[treeName]; ok {
		return optionalToCamelCase(jsonToString(value))
	}
	return ""
}

func optionalToCamelCase(value *string) any {
	if value == nil {
		return nil
	}
	return toCamelCase(*value)
}

// getExpandColumn 对应 VelocityUtils.getExpandColumn。
func getExpandColumn(table *GenTable, params map[string]any) int {
	treeNameValue := jsonToString(params[treeName])
	treeName := ""
	if treeNameValue != nil {
		treeName = *treeNameValue
	}
	num := 0
	for _, column := range table.Columns {
		if !column.List() {
			continue
		}
		num++
		if strVal(column.ColumnName) == treeName {
			break
		}
	}
	return num
}

// ---------------------------------------------------------------------------
// options JSON
// ---------------------------------------------------------------------------

// parseJSONObject 对应 fastjson2 JSONObject.parseObject：
// null / 空串 / 非对象 -> nil；非法 JSON -> error。
func parseJSONObject(options *string) (map[string]any, error) {
	if options == nil || *options == "" {
		return nil, nil
	}
	var parsed any
	if err := json.Unmarshal([]byte(*options), &parsed); err != nil {
		return nil, err
	}
	if object, ok := parsed.(map[string]any); ok {
		return object, nil
	}
	return nil, nil
}

// jsonToString 对应 JSONObject.getString：缺失 -> nil，非字符串走 toString。
func jsonToString(value any) *string {
	if value == nil {
		return nil
	}
	switch v := value.(type) {
	case string:
		return &v
	case bool:
		out := "false"
		if v {
			out = "true"
		}
		return &out
	case float64:
		out := formatJavaDouble(v)
		if v == float64(int64(v)) {
			out = fmt.Sprintf("%d", int64(v))
		}
		return &out
	}
	out := fmt.Sprint(value)
	return &out
}

func derefString(value *string) any {
	if value == nil {
		return nil
	}
	return *value
}
