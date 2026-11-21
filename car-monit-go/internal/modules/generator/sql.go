// JAVA 对照: ruoyi-generator/src/main/resources/mapper/generator/GenTableMapper.xml
// JAVA 对照: ruoyi-generator/src/main/resources/mapper/generator/GenTableColumnMapper.xml
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableMapper.java
// JAVA 对照: ruoyi-generator/src/main/java/com/ruoyi/generator/mapper/GenTableColumnMapper.java
// 类/职责: 代码生成两张表的 SQL 访问层（动态列插入 / 动态 <set> 更新 / JOIN 分组）
// 对应 Go 文件: internal/modules/generator/sql.go
//
// DIFF: MyBatis 的 <if>/<set>/<foreach> 在这里展开成字符串拼接；参数全部走 `?`，
// 不使用 GORM 的链式 API —— 生成器的列投影逐条不同（16/14/23/28 列），用 raw SQL
// 才能和 XML 一一对照。
// DIFF: PageHelper 在 Java 里是"调用 startPage 就必分页（默认 1/10）"；本工程统一用
// web.PageDomain.HasPage（pageNum+pageSize 同时存在才分页），见 internal/modules/system/common.go
// 的 queryPaged。生成器沿用工程约定。
package generator

import (
	"context"
	"database/sql"
	"fmt"
	"strconv"
	"strings"
	"time"

	"gorm.io/gorm"

	"car-monit-go/internal/platform/sqlx"
	"car-monit-go/internal/web"
)

// ---------------------------------------------------------------------------
// SQL 片段（逐字对应 XML）
// ---------------------------------------------------------------------------

// selectGenTableVO 对应 <sql id="selectGenTableVo">（20 列）。
const selectGenTableVO = "select table_id, table_name, table_comment, sub_table_name, sub_table_fk_name, " +
	"class_name, tpl_category, package_name, module_name, business_name, function_name, function_author, " +
	"gen_type, gen_path, options, create_by, create_time, update_by, update_time, remark from gen_table"

// joinTableColumns 对应 selectGenTableById / selectGenTableByName 的 t. 投影（16 列，无审计列）。
var joinTableColumns = []string{
	"table_id", "table_name", "table_comment", "sub_table_name", "sub_table_fk_name",
	"class_name", "tpl_category", "package_name", "module_name", "business_name",
	"function_name", "function_author", "gen_type", "gen_path", "options", "remark",
}

// allTableColumns 对应 selectGenTableAll 的 t. 投影（14 列，再少 gen_type / gen_path）。
var allTableColumns = []string{
	"table_id", "table_name", "table_comment", "sub_table_name", "sub_table_fk_name",
	"class_name", "tpl_category", "package_name", "module_name", "business_name",
	"function_name", "function_author", "options", "remark",
}

// joinColumnColumns 对应 JOIN 语句的 c. 投影（23 列，无 table_id、无审计列）。
var joinColumnColumns = []string{
	"column_id", "column_name", "column_comment", "column_type", "java_type", "java_field",
	"is_pk", "is_increment", "is_required", "is_insert", "is_edit", "is_list", "is_query",
	"query_type", "html_type", "dict_type", "field_map_string", "link_table_id",
	"single_selection", "multiple_selections", "dialog_search_column_ids",
	"dialog_list_column_ids", "sort",
}

// selectGenTableColumnVO 对应 <sql id="selectGenTableColumnVo">（28 列，6 个关列表在前）。
const selectGenTableColumnVO = "select field_map_string, link_table_id, single_selection, multiple_selections, " +
	"dialog_search_column_ids, dialog_list_column_ids, column_id, table_id, column_name, column_comment, " +
	"column_type, java_type, java_field, is_pk, is_increment, is_required, is_insert, is_edit, is_list, " +
	"is_query, query_type, html_type, dict_type, sort, create_by, create_time, update_by, update_time " +
	"from gen_table_column"

// dbTableListHead 对应 selectDbTableList 的固定部分（无 order by，见 XML）。
const dbTableListHead = `select table_name, table_comment, create_time, update_time from information_schema.tables
		where table_schema = (select database())
		AND table_name NOT LIKE 'qrtz_%' AND table_name NOT LIKE 'gen_%'
		AND table_name NOT IN (select table_name from gen_table)`

// dbTableListByNamesHead 对应 selectDbTableListByNames 的固定部分（小写 and，照抄）。
const dbTableListByNamesHead = `select table_name, table_comment, create_time, update_time from information_schema.tables
		where table_name NOT LIKE 'qrtz_%' and table_name NOT LIKE 'gen_%' and table_schema = (select database())
		and table_name in`

// dbColumnSQL 对应 selectDbTableColumnsByName（三个 case when 的字面量混用照抄）。
const dbColumnSQL = `select column_name, (case when (is_nullable = 'no' && column_key != 'PRI') then '1' else null end) as is_required, ` +
	`(case when column_key = 'PRI' then '1' else '0' end) as is_pk, ordinal_position as sort, column_comment, ` +
	`(case when extra = 'auto_increment' then '1' else '0' end) as is_increment, column_type
		from information_schema.columns where table_schema = (select database()) and table_name = (?)
		order by ordinal_position`

// insertGenTableColumns 对应 insertGenTable 的动态列（顺序即 XML 顺序）。
// bool 为 true 时要求"非 null 且非空串"，false 只要求非 null。
var insertGenTableColumns = []struct {
	name        string
	requireText bool
}{
	{"table_name", false},
	{"table_comment", true},
	{"class_name", true},
	{"tpl_category", true},
	{"package_name", true},
	{"module_name", true},
	{"business_name", true},
	{"function_name", true},
	{"function_author", true},
	{"gen_type", true},
	{"gen_path", true},
	{"remark", true},
	{"create_by", true},
}

// updateGenTableColumns 对应 updateGenTable 的 <set> 分支（顺序即 XML 顺序）。
var updateGenTableColumns = []struct {
	name        string
	requireText bool
}{
	{"table_name", false},
	{"table_comment", true},
	{"sub_table_name", false},
	{"sub_table_fk_name", false},
	{"class_name", true},
	{"function_author", true},
	{"gen_type", true},
	{"gen_path", true},
	{"tpl_category", true},
	{"package_name", true},
	{"module_name", true},
	{"business_name", true},
	{"function_name", true},
	{"options", true},
	{"update_by", true},
	{"remark", false},
}

// insertGenTableColumnFields 对应 insertGenTableColumn 的动态列。
var insertGenTableColumnFields = []struct {
	name        string
	requireText bool
}{
	{"table_id", true},
	{"link_table_id", true},
	{"single_selection", true},
	{"multiple_selections", true},
	{"dialog_search_column_ids", true},
	{"dialog_list_column_ids", true},
	{"field_map_string", true},
	{"column_name", true},
	{"column_comment", true},
	{"column_type", true},
	{"java_type", true},
	{"java_field", true},
	{"is_pk", true},
	{"is_increment", true},
	{"is_required", true},
	{"is_insert", true},
	{"is_edit", true},
	{"is_list", true},
	{"is_query", true},
	{"query_type", true},
	{"html_type", true},
	{"dict_type", true},
	{"sort", false},
	{"create_by", true},
}

// updateGenTableColumnAlways 对应 updateGenTableColumn 里 12 个无条件列（NULL 也写）。
var updateGenTableColumnAlways = []string{
	"column_comment", "java_type", "java_field", "is_insert", "is_edit", "is_list",
	"is_query", "is_required", "query_type", "html_type", "dict_type", "sort",
}

// updateGenTableColumnOptional 对应 updateGenTableColumn 里 6 个关列表（!= null and != ”）。
var updateGenTableColumnOptional = []string{
	"link_table_id", "single_selection", "multiple_selections",
	"dialog_search_column_ids", "dialog_list_column_ids", "field_map_string",
}

// ---------------------------------------------------------------------------
// 行扫描
// ---------------------------------------------------------------------------

// queryMaps 执行查询并把每一行转成 列名 -> 值 的 map。
// NULL 保持 nil；文本列（[]byte）转 string；其余保持驱动给的 int64/float64/time.Time。
func queryMaps(ctx context.Context, db *gorm.DB, query string, args ...any) ([]map[string]any, error) {
	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}
	rows, err := sqlDB.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer func() { _ = rows.Close() }()

	columns, err := rows.Columns()
	if err != nil {
		return nil, err
	}
	out := make([]map[string]any, 0)
	for rows.Next() {
		values := make([]any, len(columns))
		targets := make([]any, len(columns))
		for i := range values {
			targets[i] = &values[i]
		}
		if err := rows.Scan(targets...); err != nil {
			return nil, err
		}
		row := make(map[string]any, len(columns))
		for i, name := range columns {
			value := values[i]
			if raw, ok := value.([]byte); ok {
				value = string(raw)
			}
			// information_schema 的列名在 MySQL 里常是大写，统一转小写便于按列名取值。
			row[strings.ToLower(name)] = value
		}
		out = append(out, row)
	}
	return out, rows.Err()
}

// execSQL 执行写语句并返回结果。
func execSQL(ctx context.Context, db *gorm.DB, query string, args ...any) (sql.Result, error) {
	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}
	return sqlDB.ExecContext(ctx, query, args...)
}

// queryPagedTables 按工程统一分页约定执行查询（HasPage 才 COUNT + LIMIT）。
func queryPagedTables(ctx context.Context, db *gorm.DB, pd web.PageDomain, base string, args []any, orderBy string) ([]map[string]any, int64, error) {
	if err := pd.StartPageError(); err != nil {
		return nil, 0, err
	}
	query := base
	if orderBy != "" {
		query += "\n\t\t" + orderBy
	}
	if !pd.HasPage {
		rows, err := queryMaps(ctx, db, query, args...)
		if err != nil {
			return nil, 0, err
		}
		return rows, int64(len(rows)), nil
	}
	var total int64
	countRows, err := queryMaps(ctx, db, "select count(0) from ("+base+") table_count", args...)
	if err != nil {
		return nil, 0, err
	}
	if len(countRows) > 0 {
		total = rowInt64(countRows[0], "count(0)")
	}
	if pd.SkipQuery(total) {
		return []map[string]any{}, total, nil
	}
	query += " limit ? offset ?"
	lim, off := pd.LimitOffset(total)
	pagedArgs := append(append([]any{}, args...), lim, off)
	rows, err := queryMaps(ctx, db, query, pagedArgs...)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

// rowString 读取文本列：NULL -> nil。
func rowString(row map[string]any, key string) *string {
	value, ok := row[key]
	if !ok || value == nil {
		return nil
	}
	var text string
	switch v := value.(type) {
	case string:
		text = v
	case []byte:
		text = string(v)
	case time.Time:
		text = v.Format("2006-01-02 15:04:05")
	case int64:
		text = strconv.FormatInt(v, 10)
	case float64:
		text = formatJavaDouble(v)
	case bool:
		text = "false"
		if v {
			text = "true"
		}
	default:
		text = fmt.Sprint(v)
	}
	return &text
}

// rowInt64 读取整数列：NULL / 缺失 -> 0。
func rowInt64(row map[string]any, key string) int64 {
	value, ok := row[key]
	if !ok || value == nil {
		return 0
	}
	switch v := value.(type) {
	case int64:
		return v
	case int:
		return int64(v)
	case float64:
		return int64(v)
	case string:
		parsed, _ := strconv.ParseInt(v, 10, 64)
		return parsed
	case []byte:
		parsed, _ := strconv.ParseInt(string(v), 10, 64)
		return parsed
	}
	return 0
}

// rowInt64Ptr 读取可空整数列。
func rowInt64Ptr(row map[string]any, key string) *int64 {
	if value, ok := row[key]; !ok || value == nil {
		return nil
	}
	v := rowInt64(row, key)
	return &v
}

// rowDateTime 读取时间列：NULL -> nil。
func rowDateTime(row map[string]any, key string) *web.DateTime {
	value, ok := row[key]
	if !ok || value == nil {
		return nil
	}
	switch v := value.(type) {
	case time.Time:
		d := web.NewDateTime(v)
		return &d
	case string:
		if parsed, err := web.ParseDate(v); err == nil {
			d := web.NewDateTime(parsed)
			return &d
		}
	case []byte:
		if parsed, err := web.ParseDate(string(v)); err == nil {
			d := web.NewDateTime(parsed)
			return &d
		}
	}
	return nil
}

// sqlValue 把可空文本转成 database/sql 参数。
func sqlValue(value *string) any {
	if value == nil {
		return nil
	}
	return *value
}

// sqlIntValue 把可空整数转成 database/sql 参数。
func sqlIntValue(value *int64) any {
	if value == nil {
		return nil
	}
	return *value
}

// placeholders 生成 n 个逗号分隔的 ?。
func placeholders(n int) string { return sqlx.Placeholders(n) }

// ---------------------------------------------------------------------------
// GenTableMapper
// ---------------------------------------------------------------------------

// genTableMapper 对应 interface GenTableMapper。
type genTableMapper struct {
	db *gorm.DB
}

func newGenTableMapper(db *gorm.DB) *genTableMapper { return &genTableMapper{db: db} }

// buildGenTableConditions 对应 selectGenTableList / selectDbTableList 共用的 <where>。
func buildGenTableConditions(filter *GenTable) ([]string, []any) {
	var conditions []string
	var args []any
	if filter == nil {
		return conditions, args
	}
	if filter.TableName != nil && *filter.TableName != "" {
		conditions = append(conditions, "lower(table_name) like lower(concat('%', ?, '%'))")
		args = append(args, *filter.TableName)
	}
	if filter.TableComment != nil && *filter.TableComment != "" {
		conditions = append(conditions, "lower(table_comment) like lower(concat('%', ?, '%'))")
		args = append(args, *filter.TableComment)
	}
	// JAVA 对照: <if test="params.beginTime != null and params.beginTime != ''">
	// date_format 的 %y%m%d（两位年份）是 XML 原文，照抄。
	if begin := paramString(filter.Params, "beginTime"); begin != "" {
		conditions = append(conditions, "date_format(create_time,'%y%m%d') >= date_format(?,'%y%m%d')")
		args = append(args, begin)
	}
	if end := paramString(filter.Params, "endTime"); end != "" {
		conditions = append(conditions, "date_format(create_time,'%y%m%d') <= date_format(?,'%y%m%d')")
		args = append(args, end)
	}
	return conditions, args
}

// paramString 对应 OGNL 的 params.xxx：缺失 / null / 空串都当作不参与条件。
func paramString(params map[string]any, key string) string {
	if params == nil {
		return ""
	}
	value, ok := params[key]
	if !ok || value == nil {
		return ""
	}
	if text, ok := value.(string); ok {
		return text
	}
	return fmt.Sprint(value)
}

// selectGenTableList 对应 selectGenTableList（表头条件 + 写死 ORDER BY create_time DESC）。
func (m *genTableMapper) selectGenTableList(ctx context.Context, filter *GenTable, pd web.PageDomain) ([]*GenTable, int64, error) {
	base := selectGenTableVO
	conditions, args := buildGenTableConditions(filter)
	if len(conditions) > 0 {
		base += "\n\t\twhere " + strings.Join(conditions, " and ")
	}
	order := pd.OrderBy()
	if order == "" {
		order = "ORDER BY create_time DESC"
	} else {
		order = "ORDER BY " + order
	}
	rows, total, err := queryPagedTables(ctx, m.db, pd, base, args, order)
	if err != nil {
		return nil, 0, err
	}
	tables := make([]*GenTable, 0, len(rows))
	for _, row := range rows {
		table := mapGenTable(row)
		table.Columns = placeholderColumns(table)
		tables = append(tables, table)
	}
	return tables, total, nil
}

// selectDbTableList 对应 selectDbTableList（固定 3 个过滤 + <if>，无 order by）。
func (m *genTableMapper) selectDbTableList(ctx context.Context, filter *GenTable, pd web.PageDomain) ([]*GenTable, int64, error) {
	base := dbTableListHead
	conditions, args := buildGenTableConditions(filter)
	if len(conditions) > 0 {
		base += "\n\t\t\tAND " + strings.Join(conditions, " AND ")
	}
	rows, total, err := queryPagedTables(ctx, m.db, pd, base, args, pd.OrderBy())
	if err != nil {
		return nil, 0, err
	}
	tables := make([]*GenTable, 0, len(rows))
	for _, row := range rows {
		table := mapGenTable(row)
		table.Columns = placeholderColumns(table)
		tables = append(tables, table)
	}
	return tables, total, nil
}

// selectDbTableListByNames 对应 selectDbTableListByNames（空数组拼出 in ()，MySQL 报错）。
func (m *genTableMapper) selectDbTableListByNames(ctx context.Context, tableNames []string) ([]*GenTable, error) {
	args := make([]any, 0, len(tableNames))
	for _, name := range tableNames {
		args = append(args, name)
	}
	query := dbTableListByNamesHead + " (" + placeholders(len(tableNames)) + ")"
	rows, err := queryMaps(ctx, m.db, query, args...)
	if err != nil {
		return nil, err
	}
	tables := make([]*GenTable, 0, len(rows))
	for _, row := range rows {
		tables = append(tables, mapGenTable(row))
	}
	return tables, nil
}

// selectGenTableAll 对应 selectGenTableAll（JOIN，无 where，order by c.sort）。
func (m *genTableMapper) selectGenTableAll(ctx context.Context) ([]*GenTable, error) {
	query := buildJoinSQL(allTableColumns, nil)
	rows, err := queryMaps(ctx, m.db, query)
	if err != nil {
		return nil, err
	}
	tables := groupJoinedRows(rows, allTableColumns)
	for _, table := range tables {
		if len(table.Columns) == 0 {
			table.Columns = placeholderColumns(table)
		}
	}
	return tables, nil
}

// selectGenTableByID 对应 selectGenTableById。
func (m *genTableMapper) selectGenTableByID(ctx context.Context, tableID *int64) (*GenTable, error) {
	query := buildJoinSQL(joinTableColumns, strPtr("t.table_id = ?"))
	rows, err := queryMaps(ctx, m.db, query, sqlIntValue(tableID))
	if err != nil {
		return nil, err
	}
	tables := groupJoinedRows(rows, joinTableColumns)
	if len(tables) == 0 {
		return nil, nil
	}
	return tables[0], nil
}

// selectGenTableByName 对应 selectGenTableByName。
func (m *genTableMapper) selectGenTableByName(ctx context.Context, tableName *string) (*GenTable, error) {
	query := buildJoinSQL(joinTableColumns, strPtr("t.table_name = ?"))
	rows, err := queryMaps(ctx, m.db, query, sqlValue(tableName))
	if err != nil {
		return nil, err
	}
	tables := groupJoinedRows(rows, joinTableColumns)
	if len(tables) > 1 {
		// JAVA 对照: selectOne 遇到多行抛 TooManyResultsException -> 500
		return nil, fmt.Errorf("selectGenTableByName 返回了多行")
	}
	if len(tables) == 0 {
		return nil, nil
	}
	return tables[0], nil
}

// insertGenTable 对应 insertGenTable（动态列 + sysdate() 的 create_time）。
func (m *genTableMapper) insertGenTable(ctx context.Context, table *GenTable) (int64, error) {
	columns := make([]string, 0, len(insertGenTableColumns)+1)
	marks := make([]string, 0, len(insertGenTableColumns)+1)
	args := make([]any, 0, len(insertGenTableColumns)+1)
	add := func(name string, value any, present bool) {
		if !present {
			return
		}
		columns = append(columns, name)
		marks = append(marks, "?")
		args = append(args, value)
	}
	for _, field := range insertGenTableColumns {
		value := genTableColumnValue(table, field.name)
		present := value != nil
		if present && field.requireText {
			if text, ok := value.(string); ok && text == "" {
				present = false
			}
		}
		add(field.name, value, present)
	}
	columns = append(columns, "create_time")
	marks = append(marks, "sysdate()")

	query := "insert into gen_table (" + strings.Join(columns, ",") + ") values (" + strings.Join(marks, ",") + ")"
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	// JAVA 对照: useGeneratedKeys="true" keyProperty="tableId"
	if id, err := result.LastInsertId(); err == nil && id > 0 {
		table.TableID = &id
	}
	affected, err := result.RowsAffected()
	if err != nil {
		return 0, err
	}
	return affected, nil
}

// updateGenTable 对应 updateGenTable；update_time = sysdate() 无条件。
func (m *genTableMapper) updateGenTable(ctx context.Context, table *GenTable) (int64, error) {
	sets := make([]string, 0, len(updateGenTableColumns)+1)
	args := make([]any, 0, len(updateGenTableColumns)+2)
	for _, field := range updateGenTableColumns {
		value := genTableColumnValue(table, field.name)
		if value == nil {
			continue
		}
		if field.requireText {
			if text, ok := value.(string); ok && text == "" {
				continue
			}
		}
		sets = append(sets, field.name+" = ?")
		args = append(args, value)
	}
	sets = append(sets, "update_time = sysdate()")
	query := "update gen_table set " + strings.Join(sets, ", ") + " where table_id = ?"
	args = append(args, sqlIntValue(table.TableID))
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// deleteGenTableByIDs 对应 deleteGenTableByIds（<foreach collection="array">）。
func (m *genTableMapper) deleteGenTableByIDs(ctx context.Context, tableIDs []int64) (int64, error) {
	query := "delete from gen_table where table_id in (" + placeholders(len(tableIDs)) + ")"
	args := make([]any, 0, len(tableIDs))
	for _, id := range tableIDs {
		args = append(args, id)
	}
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// ---------------------------------------------------------------------------
// GenTableColumnMapper
// ---------------------------------------------------------------------------

// genTableColumnMapper 对应 interface GenTableColumnMapper。
type genTableColumnMapper struct {
	db *gorm.DB
}

func newGenTableColumnMapper(db *gorm.DB) *genTableColumnMapper {
	return &genTableColumnMapper{db: db}
}

// selectGenTableColumnListByTableID 对应 selectGenTableColumnListByTableId。
func (m *genTableColumnMapper) selectGenTableColumnListByTableID(ctx context.Context, tableID *int64) ([]*GenTableColumn, error) {
	query := selectGenTableColumnVO + "\n        where table_id = ?\n        order by sort"
	rows, err := queryMaps(ctx, m.db, query, sqlIntValue(tableID))
	if err != nil {
		return nil, err
	}
	return mapColumns(rows), nil
}

// selectGenTableColumnList 对应 selectGenTableColumnList（三个 <if> + ORDER BY sort）。
func (m *genTableColumnMapper) selectGenTableColumnList(ctx context.Context, q *GenTableColumn) ([]*GenTableColumn, error) {
	var conditions []string
	var args []any
	if q.TableID != nil {
		conditions = append(conditions, "table_id = ?")
		args = append(args, *q.TableID)
	}
	if q.ColumnName != nil && *q.ColumnName != "" {
		conditions = append(conditions, "`column_name` LIKE CONCAT('%', ?, '%%')")
		args = append(args, *q.ColumnName)
	}
	if q.JavaField != nil && *q.JavaField != "" {
		conditions = append(conditions, "java_field LIKE CONCAT('%', ?, '%%')")
		args = append(args, *q.JavaField)
	}
	query := selectGenTableColumnVO
	if len(conditions) > 0 {
		query += "\n        where " + strings.Join(conditions, " and ")
	}
	query += "\n        ORDER BY sort"
	rows, err := queryMaps(ctx, m.db, query, args...)
	if err != nil {
		return nil, err
	}
	return mapColumns(rows), nil
}

// selectGenTableColumnListByColumnIDs 对应 selectGenTableColumnListByTableColumnIds。
func (m *genTableColumnMapper) selectGenTableColumnListByColumnIDs(ctx context.Context, columnIDs []string) ([]*GenTableColumn, error) {
	query := selectGenTableColumnVO + "\n        where column_id in (" + placeholders(len(columnIDs)) + ")\n        order by sort"
	args := make([]any, 0, len(columnIDs))
	for _, id := range columnIDs {
		args = append(args, id)
	}
	rows, err := queryMaps(ctx, m.db, query, args...)
	if err != nil {
		return nil, err
	}
	return mapColumns(rows), nil
}

// insertGenTableColumn 对应 insertGenTableColumn。
func (m *genTableColumnMapper) insertGenTableColumn(ctx context.Context, column *GenTableColumn) (int64, error) {
	columns := make([]string, 0, len(insertGenTableColumnFields)+1)
	marks := make([]string, 0, len(insertGenTableColumnFields)+1)
	args := make([]any, 0, len(insertGenTableColumnFields)+1)
	for _, field := range insertGenTableColumnFields {
		value := genTableColumnFieldValue(column, field.name)
		if value == nil {
			continue
		}
		if field.requireText {
			if text, ok := value.(string); ok && text == "" {
				continue
			}
		}
		columns = append(columns, field.name)
		marks = append(marks, "?")
		args = append(args, value)
	}
	columns = append(columns, "create_time")
	marks = append(marks, "sysdate()")

	query := "insert into gen_table_column (" + strings.Join(columns, ",") + ") values (" + strings.Join(marks, ",") + ")"
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	// JAVA 对照: useGeneratedKeys="true" keyProperty="columnId"
	if id, err := result.LastInsertId(); err == nil && id > 0 {
		column.ColumnID = &id
	}
	return result.RowsAffected()
}

// updateGenTableColumn 对应 updateGenTableColumn（12 个无条件列 + 6 个可选列）。
func (m *genTableColumnMapper) updateGenTableColumn(ctx context.Context, column *GenTableColumn) (int64, error) {
	sets := make([]string, 0, len(updateGenTableColumnAlways)+len(updateGenTableColumnOptional)+2)
	args := make([]any, 0, len(updateGenTableColumnAlways)+len(updateGenTableColumnOptional)+3)
	for _, name := range updateGenTableColumnAlways {
		sets = append(sets, name+" = ?")
		args = append(args, genTableColumnFieldValue(column, name))
	}
	for _, name := range updateGenTableColumnOptional {
		value := genTableColumnFieldValue(column, name)
		if value == nil {
			continue
		}
		if text, ok := value.(string); ok && text == "" {
			continue
		}
		sets = append(sets, name+" = ?")
		args = append(args, value)
	}
	sets = append(sets, "update_by = ?", "update_time = sysdate()")
	args = append(args, sqlValue(column.UpdateBy))
	query := "update gen_table_column set " + strings.Join(sets, ", ") + " where column_id = ?"
	args = append(args, sqlIntValue(column.ColumnID))
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// deleteGenTableColumns 对应 deleteGenTableColumns（按实体里的 columnId 删）。
func (m *genTableColumnMapper) deleteGenTableColumns(ctx context.Context, columns []*GenTableColumn) (int64, error) {
	query := "delete from gen_table_column where column_id in (" + placeholders(len(columns)) + ")"
	args := make([]any, 0, len(columns))
	for _, column := range columns {
		args = append(args, sqlIntValue(column.ColumnID))
	}
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// deleteGenTableColumnByTableIDs 对应 deleteGenTableColumnByIds（where table_id in ...）。
func (m *genTableColumnMapper) deleteGenTableColumnByTableIDs(ctx context.Context, tableIDs []int64) (int64, error) {
	query := "delete from gen_table_column where table_id in (" + placeholders(len(tableIDs)) + ")"
	args := make([]any, 0, len(tableIDs))
	for _, id := range tableIDs {
		args = append(args, id)
	}
	result, err := execSQL(ctx, m.db, query, args...)
	if err != nil {
		return 0, err
	}
	return result.RowsAffected()
}

// selectDbTableColumnsByName 对应 selectDbTableColumnsByName。
func (m *genTableColumnMapper) selectDbTableColumnsByName(ctx context.Context, tableName string) ([]*GenTableColumn, error) {
	rows, err := queryMaps(ctx, m.db, dbColumnSQL, tableName)
	if err != nil {
		return nil, err
	}
	columns := make([]*GenTableColumn, 0, len(rows))
	for _, row := range rows {
		columns = append(columns, &GenTableColumn{
			ColumnName:    rowString(row, "column_name"),
			IsRequired:    rowString(row, "is_required"),
			IsPk:          rowString(row, "is_pk"),
			Sort:          rowInt64Ptr(row, "sort"),
			ColumnComment: rowString(row, "column_comment"),
			IsIncrement:   rowString(row, "is_increment"),
			ColumnType:    rowString(row, "column_type"),
		})
	}
	return columns, nil
}

// ---------------------------------------------------------------------------
// 行 -> 领域对象
// ---------------------------------------------------------------------------

// mapGenTable 对应 resultMap="GenTableResult"（columns 保持 nil —— 单表查询没有 c.*）。
// placeholderColumns 复刻 MyBatis <collection> 在没有对应列时仍造出 1 个空元素的行为：
// 该元素只带回审计列与 table_id，其余为 null。
func placeholderColumns(table *GenTable) []*GenTableColumn {
	return []*GenTableColumn{{
		CreateBy:   table.CreateBy,
		CreateTime: table.CreateTime,
		UpdateBy:   table.UpdateBy,
		UpdateTime: table.UpdateTime,
		TableID:    table.TableID,
	}}
}

func mapGenTable(row map[string]any) *GenTable {
	return &GenTable{
		CreateBy:       rowString(row, "create_by"),
		CreateTime:     rowDateTime(row, "create_time"),
		UpdateBy:       rowString(row, "update_by"),
		UpdateTime:     rowDateTime(row, "update_time"),
		Remark:         rowString(row, "remark"),
		TableID:        rowInt64Ptr(row, "table_id"),
		TableName:      rowString(row, "table_name"),
		TableComment:   rowString(row, "table_comment"),
		SubTableName:   rowString(row, "sub_table_name"),
		SubTableFkName: rowString(row, "sub_table_fk_name"),
		ClassName:      rowString(row, "class_name"),
		TplCategory:    rowString(row, "tpl_category"),
		PackageName:    rowString(row, "package_name"),
		ModuleName:     rowString(row, "module_name"),
		BusinessName:   rowString(row, "business_name"),
		FunctionName:   rowString(row, "function_name"),
		FunctionAuthor: rowString(row, "function_author"),
		GenType:        rowString(row, "gen_type"),
		GenPath:        rowString(row, "gen_path"),
		Options:        rowString(row, "options"),
	}
}

// mapGenTableJoined 对应 JOIN 查询的 t. 投影（同样没有审计列）。
func mapGenTableJoined(row map[string]any, tableColumns []string) *GenTable {
	table := mapGenTable(row)
	_ = tableColumns
	if _, ok := row["create_by"]; !ok {
		table.CreateBy = nil
	}
	if _, ok := row["create_time"]; !ok {
		table.CreateTime = nil
	}
	if _, ok := row["update_by"]; !ok {
		table.UpdateBy = nil
	}
	if _, ok := row["update_time"]; !ok {
		table.UpdateTime = nil
	}
	if _, ok := row["gen_type"]; !ok {
		table.GenType = nil
	}
	if _, ok := row["gen_path"]; !ok {
		table.GenPath = nil
	}
	return table
}

// buildJoinSQL 对应三条 LEFT JOIN 语句共用的拼装。
func buildJoinSQL(tableColumns []string, condition *string) string {
	selectList := make([]string, 0, len(tableColumns)+len(joinColumnColumns))
	for _, name := range tableColumns {
		selectList = append(selectList, "t."+name)
	}
	for _, name := range joinColumnColumns {
		selectList = append(selectList, "c."+name)
	}
	query := "SELECT " + strings.Join(selectList, ", ") + "\n\t\tFROM gen_table t\n\t\tLEFT JOIN gen_table_column c ON t.table_id = c.table_id"
	if condition != nil {
		query += "\n\t\twhere " + *condition
	}
	return query + " order by c.sort"
}

// groupJoinedRows 把 JOIN 行按 table_id 聚成 GenTable + columns。
// JAVA 对照: MyBatis <collection> 只在 column_id / column_name 至少一个非空时创建元素。
func groupJoinedRows(rows []map[string]any, tableColumns []string) []*GenTable {
	tables := make([]*GenTable, 0)
	index := make(map[int64]int)
	for _, row := range rows {
		key := rowInt64(row, "table_id")
		position, ok := index[key]
		if !ok {
			table := mapGenTableJoined(row, tableColumns)
			table.Columns = make([]*GenTableColumn, 0)
			tables = append(tables, table)
			position = len(tables) - 1
			index[key] = position
		}
		if row["column_id"] == nil && row["column_name"] == nil {
			continue
		}
		tables[position].Columns = append(tables[position].Columns, mapJoinedColumn(row))
	}
	return tables
}

// mapJoinedColumn 对应 JOIN 语句里的 c. 投影映射。
func mapJoinedColumn(row map[string]any) *GenTableColumn {
	return &GenTableColumn{
		ColumnID:              rowInt64Ptr(row, "column_id"),
		TableID:               rowInt64Ptr(row, "table_id"),
		ColumnName:            rowString(row, "column_name"),
		ColumnComment:         rowString(row, "column_comment"),
		ColumnType:            rowString(row, "column_type"),
		JavaType:              rowString(row, "java_type"),
		JavaField:             rowString(row, "java_field"),
		IsPk:                  rowString(row, "is_pk"),
		IsIncrement:           rowString(row, "is_increment"),
		IsRequired:            rowString(row, "is_required"),
		IsInsert:              rowString(row, "is_insert"),
		IsEdit:                rowString(row, "is_edit"),
		IsList:                rowString(row, "is_list"),
		IsQuery:               rowString(row, "is_query"),
		QueryType:             rowString(row, "query_type"),
		HtmlType:              rowString(row, "html_type"),
		DictType:              rowString(row, "dict_type"),
		FieldMapString:        rowString(row, "field_map_string"),
		LinkTableID:           rowInt64Ptr(row, "link_table_id"),
		SingleSelection:       rowString(row, "single_selection"),
		MultipleSelections:    rowString(row, "multiple_selections"),
		DialogSearchColumnIDs: rowString(row, "dialog_search_column_ids"),
		DialogListColumnIDs:   rowString(row, "dialog_list_column_ids"),
		Sort:                  rowInt64Ptr(row, "sort"),
	}
}

// mapColumns 对应 resultMap="GenTableColumnResult"（单表投影，含审计列）。
func mapColumns(rows []map[string]any) []*GenTableColumn {
	columns := make([]*GenTableColumn, 0, len(rows))
	for _, row := range rows {
		column := mapJoinedColumn(row)
		column.TableID = rowInt64Ptr(row, "table_id")
		column.CreateBy = rowString(row, "create_by")
		column.CreateTime = rowDateTime(row, "create_time")
		column.UpdateBy = rowString(row, "update_by")
		column.UpdateTime = rowDateTime(row, "update_time")
		columns = append(columns, column)
	}
	return columns
}

// genTableColumnValue 按列名读取 GenTable 字段（对应 XML 里的 #{属性名}）。
func genTableColumnValue(table *GenTable, name string) any {
	switch name {
	case "table_name":
		return sqlValue(table.TableName)
	case "table_comment":
		return sqlValue(table.TableComment)
	case "sub_table_name":
		return sqlValue(table.SubTableName)
	case "sub_table_fk_name":
		return sqlValue(table.SubTableFkName)
	case "class_name":
		return sqlValue(table.ClassName)
	case "tpl_category":
		return sqlValue(table.TplCategory)
	case "package_name":
		return sqlValue(table.PackageName)
	case "module_name":
		return sqlValue(table.ModuleName)
	case "business_name":
		return sqlValue(table.BusinessName)
	case "function_name":
		return sqlValue(table.FunctionName)
	case "function_author":
		return sqlValue(table.FunctionAuthor)
	case "gen_type":
		return sqlValue(table.GenType)
	case "gen_path":
		return sqlValue(table.GenPath)
	case "options":
		return sqlValue(table.Options)
	case "remark":
		return sqlValue(table.Remark)
	case "create_by":
		return sqlValue(table.CreateBy)
	case "update_by":
		return sqlValue(table.UpdateBy)
	}
	return nil
}

// genTableColumnFieldValue 按列名读取 GenTableColumn 字段（对应 XML 里的 #{属性名}）。
func genTableColumnFieldValue(column *GenTableColumn, name string) any {
	switch name {
	case "table_id":
		return sqlIntValue(column.TableID)
	case "column_id":
		return sqlIntValue(column.ColumnID)
	case "link_table_id":
		return sqlIntValue(column.LinkTableID)
	case "single_selection":
		return sqlValue(column.SingleSelection)
	case "multiple_selections":
		return sqlValue(column.MultipleSelections)
	case "dialog_search_column_ids":
		return sqlValue(column.DialogSearchColumnIDs)
	case "dialog_list_column_ids":
		return sqlValue(column.DialogListColumnIDs)
	case "field_map_string":
		return sqlValue(column.FieldMapString)
	case "column_name":
		return sqlValue(column.ColumnName)
	case "column_comment":
		return sqlValue(column.ColumnComment)
	case "column_type":
		return sqlValue(column.ColumnType)
	case "java_type":
		return sqlValue(column.JavaType)
	case "java_field":
		return sqlValue(column.JavaField)
	case "is_pk":
		return sqlValue(column.IsPk)
	case "is_increment":
		return sqlValue(column.IsIncrement)
	case "is_required":
		return sqlValue(column.IsRequired)
	case "is_insert":
		return sqlValue(column.IsInsert)
	case "is_edit":
		return sqlValue(column.IsEdit)
	case "is_list":
		return sqlValue(column.IsList)
	case "is_query":
		return sqlValue(column.IsQuery)
	case "query_type":
		return sqlValue(column.QueryType)
	case "html_type":
		return sqlValue(column.HtmlType)
	case "dict_type":
		return sqlValue(column.DictType)
	case "sort":
		return sqlIntValue(column.Sort)
	case "create_by":
		return sqlValue(column.CreateBy)
	case "update_by":
		return sqlValue(column.UpdateBy)
	}
	return nil
}
