// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableService.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/service/impl/GenTableServiceImpl.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableColumnService.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/service/impl/GenTableColumnServiceImpl.java
// 类/职责: 代码生成业务层 — 初始化顺序 / 预览 / 下载 / 写文件 / 同步表结构
// 对应 Go 文件: internal/modules/generator/service.go
//
// DIFF: Java 通过 SecurityUtils.getUsername() 从 SecurityContext 取当前用户；Go 由
// handler 把 auth.CurrentUsername(c) 显式传入。
// DIFF: Java 的 @Transactional 由 Spring 代理；Go 侧没有事务包装（与工程内其它模块一致），
// 批量操作中途失败时已执行的语句不会回滚。
//
// 三个 generatorCode / previewCode 的初始化顺序**各不相同**（Python 迁移已逐字核对）：
//
//	previewCode                                filter -> richText -> upload -> dict -> link
//	generatorCode(String)（自定义路径）          dict -> richText -> filter -> link -> upload
//	generatorCode(String, ZipOutputStream)      dict -> upload -> richText -> link -> filter
//
// 顺序会影响 initLinkTableInfo 里读到的 dictTypeCamelCase / 过滤后的列集合，不能合并。
package generator

import (
	"archive/zip"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"car-monit-go/internal/app"
	"car-monit-go/internal/web"
)

// errNullMessage 对应 Java NullPointerException：GlobalExceptionHandler 取
// getMessage() 得到 null，最终响应 {"msg":null,"code":500}。
var errNullMessage = errors.New("java.lang.NullPointerException")

// errNoSuchElement 对应 Optional.get() 空集合时的 NoSuchElementException("No value present")。
var errNoSuchElement = errors.New("No value present")

// genTableService 对应 GenTableServiceImpl（同时承载 IGenTableColumnService 的透传方法）。
type genTableService struct {
	cfg         genConfig
	mybatisPlus bool
	engine      *velocityEngine
	tables      *genTableMapper
	columns     *genTableColumnMapper
}

func newGenTableService(a *app.App) *genTableService {
	return &genTableService{
		cfg:         loadGenConfig(a.Cfg.ConfigFile),
		mybatisPlus: a.Cfg.GeneratorCode.MybatisPlus.Enable,
		engine:      newVelocityEngine(templateRoot(a.Cfg.ConfigFile)),
		tables:      newGenTableMapper(a.DB),
		columns:     newGenTableColumnMapper(a.DB),
	}
}

// ---------------------------------------------------------------------------
// 读
// ---------------------------------------------------------------------------

// selectGenTableList 对应 selectGenTableList（/list、/all/list 共用）。
func (s *genTableService) selectGenTableList(ctx context.Context, filter *GenTable, pd web.PageDomain) ([]*GenTable, int64, error) {
	return s.tables.selectGenTableList(ctx, filter, pd)
}

// selectDbTableList 对应 selectDbTableList。
func (s *genTableService) selectDbTableList(ctx context.Context, filter *GenTable, pd web.PageDomain) ([]*GenTable, int64, error) {
	return s.tables.selectDbTableList(ctx, filter, pd)
}

// selectDbTableListByNames 对应 selectDbTableListByNames。
func (s *genTableService) selectDbTableListByNames(ctx context.Context, tableNames []string) ([]*GenTable, error) {
	return s.tables.selectDbTableListByNames(ctx, tableNames)
}

// selectGenTableAll 对应 selectGenTableAll。
func (s *genTableService) selectGenTableAll(ctx context.Context) ([]*GenTable, error) {
	return s.tables.selectGenTableAll(ctx)
}

// selectGenTableByID 对应 selectGenTableById：查表 + 用 options 回填树/菜单字段。
func (s *genTableService) selectGenTableByID(ctx context.Context, tableID int64) (*GenTable, error) {
	table, err := s.tables.selectGenTableByID(ctx, &tableID)
	if err != nil {
		return nil, err
	}
	if table == nil {
		// JAVA 对照: setTableFromOptions(null) -> NPE
		return nil, errNullMessage
	}
	if err := s.setTableFromOptions(table); err != nil {
		return nil, err
	}
	return table, nil
}

// selectGenTableColumnListByTableID 对应 selectGenTableColumnListByTableId。
func (s *genTableService) selectGenTableColumnListByTableID(ctx context.Context, tableID *int64) ([]*GenTableColumn, error) {
	return s.columns.selectGenTableColumnListByTableID(ctx, tableID)
}

// selectGenTableColumnList 对应 selectGenTableColumnList。
func (s *genTableService) selectGenTableColumnList(ctx context.Context, q *GenTableColumn) ([]*GenTableColumn, error) {
	return s.columns.selectGenTableColumnList(ctx, q)
}

// selectGenTableColumnListByColumnIDs 对应 selectGenTableColumnListByTableColumnIds(String)：
// 空串 -> nil（Java 的 CollectionUtils.isEmpty(idList) 直接 return null）。
func (s *genTableService) selectGenTableColumnListByColumnIDs(ctx context.Context, ids string) ([]*GenTableColumn, error) {
	idList := stringToList(ids)
	if len(idList) == 0 {
		return nil, nil
	}
	return s.columns.selectGenTableColumnListByColumnIDs(ctx, idList)
}

// stringToList 对应 StringUtils.stringToList：split(",")，无 trim，空串 -> 空列表。
func stringToList(ids string) []string {
	if ids == "" {
		return nil
	}
	return splitJava(ids, ",")
}

// ---------------------------------------------------------------------------
// 写
// ---------------------------------------------------------------------------

// updateGenTable 对应 @Transactional updateGenTable。
func (s *genTableService) updateGenTable(ctx context.Context, table *GenTable) error {
	// JAVA 对照: JSON.toJSONString(genTable.getParams())
	options, err := fastjsonString(table.Params)
	if err != nil {
		return err
	}
	table.Options = &options
	affected, err := s.tables.updateGenTable(ctx, table)
	if err != nil {
		return err
	}
	if affected > 0 {
		if table.Columns == nil {
			// JAVA 对照: for (GenTableColumn ... : null) -> NPE
			return errNullMessage
		}
		for _, column := range table.Columns {
			if _, err := s.columns.updateGenTableColumn(ctx, column); err != nil {
				return err
			}
		}
	}
	return nil
}

// deleteGenTableByIDs 对应 @Transactional deleteGenTableByIds。
func (s *genTableService) deleteGenTableByIDs(ctx context.Context, tableIDs []int64) error {
	if _, err := s.tables.deleteGenTableByIDs(ctx, tableIDs); err != nil {
		return err
	}
	if _, err := s.columns.deleteGenTableColumnByTableIDs(ctx, tableIDs); err != nil {
		return err
	}
	return nil
}

// importGenTable 对应 @Transactional importGenTable(List<GenTable>)：
// 任何异常都包成 "导入失败：" + message（NPE 的 message 是 "null"）。
func (s *genTableService) importGenTable(ctx context.Context, tableList []*GenTable, operName string) error {
	if err := s.doImportGenTable(ctx, tableList, operName); err != nil {
		return web.NewServiceError("导入失败：%s", javaExceptionMessage(err))
	}
	return nil
}

func (s *genTableService) doImportGenTable(ctx context.Context, tableList []*GenTable, operName string) error {
	for _, table := range tableList {
		tableName := strVal(table.TableName)
		initTable(s.cfg, table, operName)
		affected, err := s.tables.insertGenTable(ctx, table)
		if err != nil {
			return err
		}
		if affected > 0 {
			genTableColumns, err := s.columns.selectDbTableColumnsByName(ctx, tableName)
			if err != nil {
				return err
			}
			for _, column := range genTableColumns {
				initColumnField(column, table)
				if _, err := s.columns.insertGenTableColumn(ctx, column); err != nil {
					return err
				}
			}
		}
	}
	return nil
}

// javaExceptionMessage 对应 Java e.getMessage() 参与拼接时的样子（NPE -> "null"）。
func javaExceptionMessage(err error) string {
	if errors.Is(err, errNullMessage) {
		return "null"
	}
	return err.Error()
}

// ---------------------------------------------------------------------------
// 预览 / 生成
// ---------------------------------------------------------------------------

// orderedStringMap 复刻 LinkedHashMap<String,String> 的 JSON 键序（模板列表序）。
type orderedStringMap struct {
	keys   []string
	values map[string]string
}

func newOrderedStringMap() *orderedStringMap {
	return &orderedStringMap{values: map[string]string{}}
}

func (m *orderedStringMap) Set(key, value string) {
	if _, ok := m.values[key]; !ok {
		m.keys = append(m.keys, key)
	}
	m.values[key] = value
}

func (m *orderedStringMap) MarshalJSON() ([]byte, error) {
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, key := range m.keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		encodedKey, err := marshalNoEscape(key)
		if err != nil {
			return nil, err
		}
		encodedValue, err := marshalNoEscape(m.values[key])
		if err != nil {
			return nil, err
		}
		buf.Write(encodedKey)
		buf.WriteByte(':')
		buf.Write(encodedValue)
	}
	buf.WriteByte('}')
	return buf.Bytes(), nil
}

// previewCode 对应 previewCode(Long tableId)。
func (s *genTableService) previewCode(ctx context.Context, tableID int64) (*orderedStringMap, error) {
	table, err := s.tables.selectGenTableByID(ctx, &tableID)
	if err != nil {
		return nil, err
	}
	if table == nil {
		// JAVA 对照: initFilterColumnInfo(null) -> NPE（getColumns()）
		return nil, errNullMessage
	}
	s.initFilterColumnInfo(table)
	s.initRichTextInfo(table)
	s.initUploadInfo(table)
	s.dictionaryKeyToCamelCase(table)
	if err := s.initLinkTableInfo(ctx, table); err != nil {
		return nil, err
	}
	if err := s.setSubTable(ctx, table); err != nil {
		return nil, err
	}
	if err := s.setPkColumn(table); err != nil {
		return nil, err
	}
	vctx, err := prepareContext(table)
	if err != nil {
		return nil, err
	}
	dataMap := newOrderedStringMap()
	for _, name := range getTemplateList(table.TplCategory, s.isMybatisPlus()) {
		template, err := s.engine.getTemplate(name)
		if err != nil {
			return nil, err
		}
		rendered, err := template.merge(vctx)
		if err != nil {
			return nil, err
		}
		dataMap.Set(name, rendered)
	}
	return dataMap, nil
}

// downloadCode 对应 downloadCode(String) / downloadCode(String[])：返回 zip 字节流。
func (s *genTableService) downloadCode(ctx context.Context, tableNames []string) ([]byte, error) {
	var buffer bytes.Buffer
	archive := zip.NewWriter(&buffer)
	seen := map[string]bool{}
	for _, tableName := range tableNames {
		if err := s.generatorCodeToZip(ctx, tableName, archive, seen); err != nil {
			return nil, err
		}
	}
	if err := archive.Close(); err != nil {
		return nil, err
	}
	return buffer.Bytes(), nil
}

// generatorCodeToZip 对应 private generatorCode(String tableName, ZipOutputStream zip)。
func (s *genTableService) generatorCodeToZip(ctx context.Context, tableName string, archive *zip.Writer, seen map[string]bool) error {
	table, err := s.tables.selectGenTableByName(ctx, &tableName)
	if err != nil {
		return err
	}
	if table == nil {
		return errNullMessage
	}
	s.dictionaryKeyToCamelCase(table)
	s.initUploadInfo(table)
	s.initRichTextInfo(table)
	if err := s.initLinkTableInfo(ctx, table); err != nil {
		return err
	}
	s.initFilterColumnInfo(table)
	if err := s.setSubTable(ctx, table); err != nil {
		return err
	}
	if err := s.setPkColumn(table); err != nil {
		return err
	}
	vctx, err := prepareContext(table)
	if err != nil {
		return err
	}
	for _, name := range getTemplateList(table.TplCategory, s.isMybatisPlus()) {
		template, err := s.engine.getTemplate(name)
		if err != nil {
			return err
		}
		rendered, err := template.merge(vctx)
		if err != nil {
			return err
		}
		fileName := getFileName(name, table)
		// JAVA 对照: ZipOutputStream.putNextEntry 重复条目抛 ZipException（IOException）
		// -> catch 后只记日志，跳过该模板。
		if seen[fileName] {
			continue
		}
		seen[fileName] = true
		writer, err := archive.Create(fileName)
		if err != nil {
			continue
		}
		if _, err := writer.Write([]byte(rendered)); err != nil {
			return err
		}
	}
	return nil
}

// generatorCode 对应 generatorCode(String)：写入 genPath，跳过 4 类模板。
func (s *genTableService) generatorCode(ctx context.Context, tableName string) error {
	table, err := s.tables.selectGenTableByName(ctx, &tableName)
	if err != nil {
		return err
	}
	if table == nil {
		return errNullMessage
	}
	s.dictionaryKeyToCamelCase(table)
	s.initRichTextInfo(table)
	s.initFilterColumnInfo(table)
	if err := s.initLinkTableInfo(ctx, table); err != nil {
		return err
	}
	s.initUploadInfo(table)
	if err := s.setSubTable(ctx, table); err != nil {
		return err
	}
	if err := s.setPkColumn(table); err != nil {
		return err
	}
	vctx, err := prepareContext(table)
	if err != nil {
		return err
	}
	for _, name := range getTemplateList(table.TplCategory, s.isMybatisPlus()) {
		if containsAny(name, "sql.vm", "api.js.vm", "index.vue.vm", "index-tree.vue.vm") {
			continue
		}
		template, err := s.engine.getTemplate(name)
		if err != nil {
			return err
		}
		rendered, err := template.merge(vctx)
		if err != nil {
			return err
		}
		path := s.getGenPath(table, name)
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			return web.NewServiceError("渲染模板失败，表名：%s", strVal(table.TableName))
		}
		if err := os.WriteFile(path, []byte(rendered), 0o644); err != nil {
			return web.NewServiceError("渲染模板失败，表名：%s", strVal(table.TableName))
		}
	}
	return nil
}

// synchDb 对应 @Transactional synchDb(String tableName)。
func (s *genTableService) synchDb(ctx context.Context, tableName string) error {
	table, err := s.tables.selectGenTableByName(ctx, &tableName)
	if err != nil {
		return err
	}
	if table == nil || table.Columns == nil {
		return errNullMessage
	}
	tableColumnNames := make([]string, 0, len(table.Columns))
	for _, column := range table.Columns {
		tableColumnNames = append(tableColumnNames, strVal(column.ColumnName))
	}
	dbTableColumns, err := s.columns.selectDbTableColumnsByName(ctx, tableName)
	if err != nil {
		return err
	}
	if len(dbTableColumns) == 0 {
		return web.NewServiceError("同步数据失败，原表结构不存在")
	}
	dbColumnNames := make([]string, 0, len(dbTableColumns))
	for _, column := range dbTableColumns {
		dbColumnNames = append(dbColumnNames, strVal(column.ColumnName))
	}
	for _, column := range dbTableColumns {
		if !arraysContains(tableColumnNames, strVal(column.ColumnName)) {
			initColumnField(column, table)
			if _, err := s.columns.insertGenTableColumn(ctx, column); err != nil {
				return err
			}
		}
	}
	var deleted []*GenTableColumn
	for _, column := range table.Columns {
		if !arraysContains(dbColumnNames, strVal(column.ColumnName)) {
			deleted = append(deleted, column)
		}
	}
	if len(deleted) > 0 {
		if _, err := s.columns.deleteGenTableColumns(ctx, deleted); err != nil {
			return err
		}
	}
	return nil
}

// ---------------------------------------------------------------------------
// 校验 / 公开工具
// ---------------------------------------------------------------------------

// validateEdit 对应 validateEdit：**只校验树表**。
// TLP_SUB 分支嵌在树表分支内部，永远不成立（Java 原文如此，照抄）。
func (s *genTableService) validateEdit(table *GenTable) error {
	if strVal(table.TplCategory) != tplTree {
		return nil
	}
	options, err := fastjsonString(table.Params)
	if err != nil {
		return err
	}
	params, err := parseJSONObject(&options)
	if err != nil {
		return err
	}
	if stringValue(params, treeCode) == "" {
		return web.NewServiceError("树编码字段不能为空")
	}
	if stringValue(params, treeParentCode) == "" {
		return web.NewServiceError("树父编码字段不能为空")
	}
	if stringValue(params, treeName) == "" {
		return web.NewServiceError("树名称字段不能为空")
	}
	return nil
}

// stringValue 对应 JSONObject.getString：缺失 / null -> ""。
func stringValue(params map[string]any, key string) string {
	if params == nil {
		return ""
	}
	value := jsonToString(params[key])
	if value == nil {
		return ""
	}
	return *value
}

// setPkColumn 对应 setPkColumn：第一个 isPk 的列，否则第 0 列（主子表同样处理子表）。
func (s *genTableService) setPkColumn(table *GenTable) error {
	if table.Columns == nil {
		return errNullMessage
	}
	for _, column := range table.Columns {
		if column.IsPrimaryKey() {
			table.PkColumn = column
			break
		}
	}
	if table.PkColumn == nil {
		if len(table.Columns) == 0 {
			// JAVA 对照: List.get(0) -> IndexOutOfBoundsException
			return errors.New("Index 0 out of bounds for length 0")
		}
		table.PkColumn = table.Columns[0]
	}
	if strVal(table.TplCategory) == tplSub {
		subTable := table.SubTable
		if subTable == nil || subTable.Columns == nil {
			return errNullMessage
		}
		for _, column := range subTable.Columns {
			if column.IsPrimaryKey() {
				subTable.PkColumn = column
				break
			}
		}
		if subTable.PkColumn == nil {
			if len(subTable.Columns) == 0 {
				return errors.New("Index 0 out of bounds for length 0")
			}
			subTable.PkColumn = subTable.Columns[0]
		}
	}
	return nil
}

// setSubTable 对应 setSubTable。
func (s *genTableService) setSubTable(ctx context.Context, table *GenTable) error {
	if subTableName := strVal(table.SubTableName); subTableName != "" {
		subTable, err := s.tables.selectGenTableByName(ctx, &subTableName)
		if err != nil {
			return err
		}
		table.SubTable = subTable
	}
	return nil
}

// setTableFromOptions 对应 setTableFromOptions。
func (s *genTableService) setTableFromOptions(table *GenTable) error {
	params, err := parseJSONObject(table.Options)
	if err != nil {
		return err
	}
	if params != nil {
		table.TreeCode = jsonToString(params[treeCode])
		table.TreeParentCode = jsonToString(params[treeParentCode])
		table.TreeName = jsonToString(params[treeName])
		table.ParentMenuID = jsonToString(params[parentMenuID])
		table.ParentMenuName = jsonToString(params[parentMenuName])
	}
	return nil
}

// getGenPath 对应 static getGenPath：genPath == "/" 时落到进程工作目录下的 src/。
func (s *genTableService) getGenPath(table *GenTable, template string) string {
	fileName := getFileName(template, table)
	genPath := "null"
	if table.GenPath != nil {
		genPath = *table.GenPath
	}
	if genPath == "/" {
		// JAVA 对照: System.getProperty("user.dir")
		workingDir, err := os.Getwd()
		if err != nil {
			workingDir = "."
		}
		return workingDir + string(os.PathSeparator) + "src" + string(os.PathSeparator) + fileName
	}
	return genPath + string(os.PathSeparator) + fileName
}

// isMybatisPlus 对应 @Value("${generator-code.mybatis-plus.enable:false}")。
func (s *genTableService) isMybatisPlus() bool { return s.mybatisPlus }

// ---------------------------------------------------------------------------
// 私有：初始化
// ---------------------------------------------------------------------------

// initFilterColumnInfo 对应 initFilterColumnInfo。
func (s *genTableService) initFilterColumnInfo(table *GenTable) {
	if len(table.Columns) == 0 {
		return
	}
	filtered := make([]*GenTableColumn, 0, len(table.Columns))
	for _, column := range table.Columns {
		if strVal(column.JavaField) == "" {
			continue
		}
		// 过滤 id 为 String 类型的字段
		if columnPrimaryKey == strVal(column.JavaField) && stringClassKey == strVal(column.JavaType) {
			continue
		}
		if arraysContains(filterColumnNameList, strVal(column.JavaField)) {
			continue
		}
		filtered = append(filtered, column)
	}
	table.FilterColumnList = filtered
}

// initRichTextInfo 对应 initRichTextInfo（字段名是 columnList，不是 richTextColumnList）。
func (s *genTableService) initRichTextInfo(table *GenTable) {
	if len(table.Columns) == 0 {
		return
	}
	editorColumns := make([]*GenTableColumn, 0)
	for _, column := range table.Columns {
		if strVal(column.HtmlType) == htmlEditor {
			editorColumns = append(editorColumns, column)
		}
	}
	info := &GenerateRichTextInfo{}
	if len(editorColumns) > 0 {
		count := int64(len(editorColumns))
		info.RichTextCount = &count
		info.ColumnList = editorColumns
	} else {
		zero := int64(0)
		info.RichTextCount = &zero
	}
	table.RichTextInfo = info
}

// initUploadInfo 对应 initUploadInfo（字段名 uploadFiledNames 是 Java 原文笔误）。
func (s *genTableService) initUploadInfo(table *GenTable) {
	if len(table.Columns) == 0 {
		return
	}
	uploadColumns := make([]*GenTableColumn, 0)
	fieldNames := make([]string, 0)
	for _, column := range table.Columns {
		if strVal(column.HtmlType) == htmlFileUpload {
			uploadColumns = append(uploadColumns, column)
			fieldNames = append(fieldNames, strVal(column.JavaField))
		}
	}
	info := &GenerateUploadInfo{}
	if len(uploadColumns) > 0 {
		count := int64(len(uploadColumns))
		names := strings.Join(fieldNames, ",")
		info.UploadCount = &count
		info.UploadColumn = uploadColumns
		info.UploadFiledNames = &names
	} else {
		zero := int64(0)
		info.UploadCount = &zero
	}
	table.UploadInfo = info
}

// initLinkTableInfo 对应 initLinkTableInfo。
func (s *genTableService) initLinkTableInfo(ctx context.Context, table *GenTable) error {
	if len(table.Columns) == 0 {
		return nil
	}
	linkTableColumns := make([]*GenTableColumn, 0)
	for _, column := range table.Columns {
		if column.LinkTableID != nil && strings.TrimSpace(strVal(column.FieldMapString)) != "" {
			linkTableColumns = append(linkTableColumns, column)
		}
	}
	if err := s.initDialogQueryShowData(ctx, linkTableColumns); err != nil {
		return err
	}

	checkboxColumns := make([]*GenTableColumn, 0)
	radioColumns := make([]*GenTableColumn, 0)
	allFields := make([]*LinkTableField, 0)
	allCustomFields := make([]*LinkTableField, 0)
	allTableFields := make([]*LinkTableField, 0)

	for _, column := range linkTableColumns {
		if strVal(column.SingleSelection) == "1" {
			radioColumns = append(radioColumns, column)
		}
		if strVal(column.MultipleSelections) == "1" {
			checkboxColumns = append(checkboxColumns, column)
		}
		fieldList, err := parseLinkTableFields(column.FieldMapString)
		if err != nil {
			return err
		}
		tableFields := make([]*LinkTableField, 0)
		customFields := make([]*LinkTableField, 0)
		for _, field := range fieldList {
			switch strVal(field.FieldType) {
			case linkTableFieldTypeTable:
				tableFields = append(tableFields, field)
			case linkTableFieldTypeCustomField:
				customFields = append(customFields, field)
			}
		}
		if len(tableFields) > 0 {
			column.TableFieldList = tableFields
			allTableFields = append(allTableFields, tableFields...)
			allFields = append(allFields, tableFields...)
		}
		if len(customFields) > 0 {
			column.CustomFieldList = customFields
			allCustomFields = append(allCustomFields, customFields...)
			allFields = append(allFields, customFields...)
		}
		column.GenerateLinkTableFlag = strPtr("1")
		// JAVA 对照: stream().filter(...).findFirst().get() —— 找不到即 NoSuchElementException
		var major *LinkTableField
		for _, field := range tableFields {
			if column.ColumnID != nil && field.CurrentTableFileID != nil && *column.ColumnID == *field.CurrentTableFileID {
				major = field
				break
			}
		}
		if major == nil {
			return errNoSuchElement
		}
		column.MajorLinkFieldInfo = major
	}

	if err := s.initTableFieldInfo(ctx, allTableFields); err != nil {
		return err
	}
	if err := s.initLinkTableFieldInfo(ctx, allFields); err != nil {
		return err
	}

	dialog := &GenColumnDialog{}
	dialog.DialogColumnList = linkTableColumns
	dialogNumber := int64(len(linkTableColumns))
	dialog.DialogNumber = &dialogNumber
	dialog.CheckBoxColumnList = checkboxColumns
	checkboxNumber := int64(len(checkboxColumns))
	dialog.CheckboxNumber = &checkboxNumber
	dialog.RadioColumnList = radioColumns
	radioNumber := int64(len(radioColumns))
	dialog.RadioNumber = &radioNumber
	dialog.TableFieldList = allTableFields
	dialog.CustomFieldList = allCustomFields
	dialog.FieldList = allFields
	table.ColumnDialogInfo = dialog
	return nil
}

// initTableFieldInfo 对应 initTableFieldInfo。
func (s *genTableService) initTableFieldInfo(ctx context.Context, fields []*LinkTableField) error {
	if len(fields) == 0 {
		return nil
	}
	ids := make([]string, 0, len(fields))
	for _, field := range fields {
		ids = append(ids, javaStringValue(field.CurrentTableFileID))
	}
	columnList, err := s.selectGenTableColumnListByColumnIDStrings(ctx, ids)
	if err != nil {
		return err
	}
	if len(columnList) == 0 {
		return nil
	}
	byID := make(map[int64]*GenTableColumn, len(columnList))
	for _, column := range columnList {
		if column.ColumnID != nil {
			byID[*column.ColumnID] = column
		}
	}
	for _, field := range fields {
		if field.CurrentTableFileID == nil {
			continue
		}
		if column, ok := byID[*field.CurrentTableFileID]; ok {
			field.TableFileInfo = column
		}
	}
	return nil
}

// initLinkTableFieldInfo 对应 initLinkTableFieldInfo。
func (s *genTableService) initLinkTableFieldInfo(ctx context.Context, fields []*LinkTableField) error {
	if len(fields) == 0 {
		return nil
	}
	ids := make([]string, 0, len(fields))
	for _, field := range fields {
		ids = append(ids, javaStringValue(field.LinkTableFieldID))
	}
	columnList, err := s.selectGenTableColumnListByColumnIDStrings(ctx, ids)
	if err != nil {
		return err
	}
	if len(columnList) == 0 {
		return nil
	}
	byID := make(map[int64]*GenTableColumn, len(columnList))
	for _, column := range columnList {
		if column.ColumnID != nil {
			byID[*column.ColumnID] = column
		}
	}
	for _, field := range fields {
		if field.LinkTableFieldID == nil {
			continue
		}
		if column, ok := byID[*field.LinkTableFieldID]; ok {
			field.LinkTableFieldInfo = column
		}
	}
	return nil
}

// selectGenTableColumnListByColumnIDStrings 对应
// selectGenTableColumnListByTableColumnIdList(List<Long>)：空 -> nil，元素 String.valueOf。
func (s *genTableService) selectGenTableColumnListByColumnIDStrings(ctx context.Context, ids []string) ([]*GenTableColumn, error) {
	if len(ids) == 0 {
		return nil, nil
	}
	return s.columns.selectGenTableColumnListByColumnIDs(ctx, ids)
}

// javaStringValue 对应 String.valueOf(Object)：null -> "null"，Long -> 十进制。
func javaStringValue(value *int64) string {
	if value == nil {
		return "null"
	}
	return fmt.Sprintf("%d", *value)
}

// initDialogQueryShowData 对应 initDialogQueryShowData。
func (s *genTableService) initDialogQueryShowData(ctx context.Context, linkTableColumns []*GenTableColumn) error {
	if len(linkTableColumns) == 0 {
		return nil
	}
	for _, column := range linkTableColumns {
		if ids := strVal(column.DialogSearchColumnIDs); ids != "" {
			list, err := s.selectGenTableColumnListByColumnIDs(ctx, ids)
			if err != nil {
				return err
			}
			column.DialogSearchColumnList = list
		}
		if ids := strVal(column.DialogListColumnIDs); ids != "" {
			list, err := s.selectGenTableColumnListByColumnIDs(ctx, ids)
			if err != nil {
				return err
			}
			column.DialogShowColumnList = list
		}
		linkTable, err := s.tables.selectGenTableByID(ctx, column.LinkTableID)
		if err != nil {
			return err
		}
		if linkTable == nil {
			// JAVA 对照: setPkColumn(null) -> NPE
			return errNullMessage
		}
		if err := s.setPkColumn(linkTable); err != nil {
			return err
		}
		column.LinkTable = linkTable
	}
	return nil
}

// dictionaryKeyToCamelCase 对应 dictionaryKeyToCamelCase。
func (s *genTableService) dictionaryKeyToCamelCase(table *GenTable) {
	if table == nil || len(table.Columns) == 0 {
		return
	}
	dictionaryInfoList := make([]*DictionaryInfo, 0)
	for _, column := range table.Columns {
		if strVal(column.DictType) == "" {
			continue
		}
		camel := toCamelCase(strVal(column.DictType))
		column.DictTypeCamelCase = &camel
		dictionaryInfoList = append(dictionaryInfoList, &DictionaryInfo{
			DictionaryKey:          column.DictType,
			DictionaryKeyCamelCase: &camel,
		})
	}
	if len(dictionaryInfoList) > 0 {
		table.DictionaryInfoList = dictionaryInfoList
		keys := make([]string, 0, len(dictionaryInfoList))
		for _, info := range dictionaryInfoList {
			keys = append(keys, strVal(info.DictionaryKey))
		}
		joined := strings.Join(keys, ",")
		table.DictionaryInfoString = &joined
	}
	suffix := generateCodeDictionaryListKeySuffix
	table.DictionaryListKeySuffix = &suffix
}

// ---------------------------------------------------------------------------
// JSON 辅助
// ---------------------------------------------------------------------------

// containsAny 对应 StringUtils.containsAny（空 needles 不参与匹配）。
func containsAny(text string, values ...string) bool {
	for _, value := range values {
		if value != "" && strings.Contains(text, value) {
			return true
		}
	}
	return false
}

// parseLinkTableFields 对应 JSON.parseArray(text, LinkTableField.class)：
// null / 空串 / 非数组 -> 空列表。
func parseLinkTableFields(text *string) ([]*LinkTableField, error) {
	if text == nil || *text == "" {
		return nil, nil
	}
	var raw []json.RawMessage
	if err := json.Unmarshal([]byte(*text), &raw); err != nil {
		return nil, err
	}
	fields := make([]*LinkTableField, 0, len(raw))
	for _, item := range raw {
		field := &LinkTableField{}
		if len(item) > 0 && item[0] == '{' {
			if err := json.Unmarshal(item, field); err != nil {
				return nil, err
			}
		}
		fields = append(fields, field)
	}
	return fields, nil
}

// fastjsonString 对应 JSON.toJSONString(Object)：
// 紧凑格式、不转义非 ASCII、缺失为 "null"、Map 里的 null 值被省略（fastjson2 默认）。
// DIFF: fastjson2 对 Map 按插入序输出，Go 的 encoding/json 对 map 按键排序；
// options 只被 parseObject 回读，键序不影响行为。
func fastjsonString(value any) (string, error) {
	if value == nil {
		return "null", nil
	}
	if params, ok := value.(map[string]any); ok {
		cleaned := make(map[string]any, len(params))
		for key, item := range params {
			if item == nil {
				continue
			}
			cleaned[key] = item
		}
		value = cleaned
	}
	encoded, err := marshalNoEscape(value)
	if err != nil {
		return "", err
	}
	return string(encoded), nil
}

// marshalNoEscape 等价 Jackson/fastjson2 的字符串转义（不把 < > & 变成 \u003c）。
func marshalNoEscape(value any) ([]byte, error) {
	var buf bytes.Buffer
	encoder := json.NewEncoder(&buf)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(value); err != nil {
		return nil, err
	}
	return bytes.TrimSuffix(buf.Bytes(), []byte("\n")), nil
}
