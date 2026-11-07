// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/CommonUtil.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/controller/BaseController.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDictDataServiceImpl.java
// 类/职责: 本模块公共设施 —— 字符串工具、动态 WHERE 构造、分页查询、字典映射、审计字段取值
// 对应 Go 文件: internal/modules/manager/support.go
//
// DIFF: Java 的 PageHelper 通过 ThreadLocal + MyBatis 拦截器隐式改写 SQL（startPage/getDataTable），
// Go 没有隐式拦截：handler 显式读取 PageDomain，显式执行 COUNT，再显式拼 LIMIT/OFFSET。
// DIFF: Java 的 MyBatis 动态 SQL（<if test="x != null">）在 Go 里由 whereClause 的方法逐条显式追加，
// 所有值一律走 ? 占位符，列名只来自本包内写死的常量，绝不拼接客户端输入。
package manager

import (
	"context"
	"fmt"
	"reflect"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// handler 汇总 manager 模块各控制器的依赖（对应 Spring 注入的 Service/Mapper）。
type handler struct {
	app *app.App
}

func newHandler(a *app.App) *handler { return &handler{app: a} }

// ---------------------------------------------------------------------------
// com.ruoyi.common.utils.CommonUtil
// ---------------------------------------------------------------------------

// strOf 对应 Java 的 String 语义：nil / 未选中的列 == null -> ""。
//
// DIFF: Go 的实体字段用 *string 表达「Java 侧可能是 null」，
// 因此这些工具函数接受 any，行为与 Java 的 String 工具一致。
func strOf(v any) string {
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
	case []byte:
		return string(x)
	default:
		return fmt.Sprint(v)
	}
}

// strPtr 取字符串指针，用于给 *string 字段赋值。
func strPtr(s string) *string { return &s }

// isNull 对应 CommonUtil.isNull：null -> ""，否则 toString().trim()。
func isNull(v any) string { return strings.TrimSpace(strOf(v)) }

// isNotBlank 对应 CommonUtil.isNotBlank（StringUtils.isNotBlank）。
func isNotBlank(v any) bool { return strings.TrimSpace(strOf(v)) != "" }

// isBlank 对应 CommonUtil.isBlank（StringUtils.isBlank）。
func isBlank(v any) bool { return strings.TrimSpace(strOf(v)) == "" }

// deleteEnd 对应 CommonUtil.deleteEnd：去掉末尾一个逗号。
func deleteEnd(v any) string { return strings.TrimSuffix(strings.TrimSpace(strOf(v)), ",") }

// splitCSV 对应 Java 的 String.split(",")：丢弃结果中的尾部空串。
//
// DIFF: Java 的 split 用正则且默认 limit=0（去掉尾部空串），Go 的 strings.Split 保留空串，
// 因此这里手工裁剪，保证 "a," -> ["a"]、"a,,b" -> ["a","","b"] 与 Java 一致。
func splitCSV(s string) []string {
	parts := strings.Split(s, ",")
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

// newUUID 对应 StringUtils.getUUID()：32 位无连字符 UUID。
func newUUID() string { return strings.ReplaceAll(uuid.NewString(), "-", "") }

// newUUIDDashed 对应 Java 的 UUID.randomUUID().toString()。
//
// JAVA 对照: ExcelUtil.encodingFilename 用随机 UUID（带横杠）拼文件名，
// 而实体主键用的是 MP 的 IdType.UUID（32 位无横杠），两者形态不同。
func newUUIDDashed() string { return uuid.NewString() }

// appendQuery 在原始查询串后追加一个 k=v（用于补齐控制器里的默认值）。
func appendQuery(raw, kv string) string {
	if raw == "" {
		return kv
	}
	return raw + "&" + kv
}

// ---------------------------------------------------------------------------
// 登录用户上下文（对应 SecurityUtils）
// ---------------------------------------------------------------------------

// currentUserID 对应 SecurityUtils.getUserId()。
func currentUserID(c *gin.Context) int64 { return auth.CurrentUserID(c) }

// currentEpsID 对应 SecurityUtils.getEpsId() —— Java 里返回的是 user.getDeptId()。
func currentEpsID(c *gin.Context) int64 {
	if lu := auth.CurrentUser(c); lu != nil && lu.User != nil {
		return lu.User.DeptID
	}
	return -1
}

// currentTenantID 对应 SecurityUtils.getTenantId()。
func currentTenantID(c *gin.Context) int64 {
	if lu := auth.CurrentUser(c); lu != nil && lu.User != nil {
		return model.Int64Val(lu.User.TenantID)
	}
	return -1
}

// ---------------------------------------------------------------------------
// MyBatis 动态 SQL 的显式替身
// ---------------------------------------------------------------------------

// whereClause 对应 mapper XML 里那一串 <if test="..."> 条件。
type whereClause struct {
	clause string
	args   []any
}

// newWhere 以基础条件（含 "WHERE" 关键字）开启一个条件构造器。
func newWhere(base string) *whereClause {
	return &whereClause{clause: base}
}

// raw 追加一段原样 SQL 片段（片段本身是本包写死的常量）。
func (w *whereClause) raw(clause string, args ...any) {
	w.clause += " AND " + clause
	w.args = append(w.args, args...)
}

// eq 对应 <if test="x != null and x != ”"> and col = #{x}</if>。
func (w *whereClause) eq(column, value string) {
	if value != "" {
		w.raw(column+" = ?", value)
	}
}

// like 对应 ... and col like concat('%', #{x}, '%')。
func (w *whereClause) like(column, value string) {
	if value != "" {
		w.raw(column+" LIKE CONCAT('%', ?, '%')", value)
	}
}

// eqPtrInt 对应 Long 类型的 <if test="x != null">（Long 可为 null，故用指针）。
func (w *whereClause) eqPtrInt(column string, value *int64) {
	if value != nil {
		w.raw(column+" = ?", *value)
	}
}

// eqPtrFloat 对应 BigDecimal 类型的 <if test="x != null">。
func (w *whereClause) eqPtrFloat(column string, value *float64) {
	if value != nil {
		w.raw(column+" = ?", *value)
	}
}

// SQL 返回拼好的 WHERE 片段。
func (w *whereClause) SQL() string { return w.clause }

// Args 返回占位符参数。
func (w *whereClause) Args() []any { return w.args }

// ---------------------------------------------------------------------------
// 分页查询
// ---------------------------------------------------------------------------

// listQuery 描述一条分页列表 SQL（对应 mapper 的 selectXxxList）。
type listQuery struct {
	// SelectSQL 是 SELECT 之后的列清单（含别名）。
	SelectSQL string
	// FromSQL 是 FROM 及其后的 JOIN。
	FromSQL string
	// Where 是 WHERE 片段。
	Where *whereClause
	// OrderBy 是排序子句（不含 "ORDER BY"）。只允许本包内常量或 web.PageDomain.OrderBy 的产物。
	OrderBy string
	// Page 来自 web.Page(c)。
	Page web.PageDomain
}

// list 执行分页查询，返回 total（对应 PageInfo.getTotal / list.size()）。
//
// DIFF: Java 由 PageHelper 在拦截器里生成 count 语句；这里显式拼 COUNT(1)，JOIN 与 WHERE 与主查询完全一致。
func (h *handler) list(ctx context.Context, q listQuery, dest any) (int64, error) {
	if err := q.Page.StartPageError(); err != nil {
		return 0, err
	}
	base := q.FromSQL + q.Where.SQL()
	var total int64
	if q.Page.HasPage {
		countSQL := "SELECT COUNT(1) " + base
		if err := h.app.DB.WithContext(ctx).Raw(countSQL, q.Where.Args()...).Scan(&total).Error; err != nil {
			return 0, err
		}
	} else {
		// DIFF: Java 未传 pageNum/pageSize 时 PageHelper 不分页，TableDataInfo.total 取 list.size()。
		total = 0
	}

	if q.Page.SkipQuery(total) {
		return total, nil
	}

	sqlStr := "SELECT " + q.SelectSQL + " " + base
	if q.OrderBy != "" {
		sqlStr += " ORDER BY " + q.OrderBy
	}
	args := q.Where.Args()
	if q.Page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		lim, off := q.Page.LimitOffset(total)
		args = append(args, lim, off)
	}
	if err := h.app.DB.WithContext(ctx).Raw(sqlStr, args...).Scan(dest).Error; err != nil {
		return 0, err
	}
	if !q.Page.HasPage {
		total = sliceLen(dest)
	}
	return total, nil
}

// sliceLen 返回 dest 指向的切片长度（dest 必须是 *[]T）。
func sliceLen(dest any) int64 {
	v := reflect.ValueOf(dest)
	if v.Kind() == reflect.Ptr && !v.IsNil() && v.Elem().Kind() == reflect.Slice {
		return int64(v.Elem().Len())
	}
	return 0
}

// ---------------------------------------------------------------------------
// 字典（对应 ISysDictDataService.selectDictDataMap / selectDictDataLaleMap）
// ---------------------------------------------------------------------------

type dictDataRow struct {
	DictValue string `gorm:"column:dict_value"`
	DictLabel string `gorm:"column:dict_label"`
}

// dictValueLabel 对应 SysDictDataServiceImpl.selectDictDataMap：dictValue -> dictLabel。
func (h *handler) dictValueLabel(ctx context.Context, dictType string) (map[string]string, error) {
	rows, err := h.loadDict(ctx, dictType)
	if err != nil {
		return nil, err
	}
	m := make(map[string]string, len(rows))
	for _, r := range rows {
		m[r.DictValue] = r.DictLabel
	}
	return m, nil
}

// dictLabelValue 对应 SysDictDataServiceImpl.selectDictDataLaleMap：dictLabel -> dictValue。
func (h *handler) dictLabelValue(ctx context.Context, dictType string) (map[string]string, error) {
	rows, err := h.loadDict(ctx, dictType)
	if err != nil {
		return nil, err
	}
	m := make(map[string]string, len(rows))
	for _, r := range rows {
		m[r.DictLabel] = r.DictValue
	}
	return m, nil
}

// loadDict 对应 SysDictDataMapper.selectDictDataList(dictType)（order by dict_sort asc）。
func (h *handler) loadDict(ctx context.Context, dictType string) ([]dictDataRow, error) {
	var rows []dictDataRow
	err := h.app.DB.WithContext(ctx).
		Table("sys_dict_data").
		Select("dict_value, dict_label").
		Where("dict_type = ?", dictType).
		Order("dict_sort ASC").
		Scan(&rows).Error
	return rows, err
}

// ---------------------------------------------------------------------------
// 审计字段（对应 MyBatisPlusHandlerConfig 的自动填充）
// ---------------------------------------------------------------------------

// auditNow 返回当前时间，对应 DateUtils.getTimestamp()。
func auditNow() time.Time { return time.Now() }

// orderFor 对应 PageHelper 的 orderBy：请求里带了 orderByColumn 时，
// PageHelper 会用客户端排序**覆盖** mapper XML 里的 order by；没带才用服务端默认排序。
func orderFor(defaultOrder string, page web.PageDomain) string {
	if o := page.OrderBy(); o != "" {
		return o
	}
	return defaultOrder
}

// withInsertAudit 对应 insertFill：create_by / create_time / eps_id / tenant_id。
//
// JAVA 对照: MyBatisPlusHandlerConfig#insertFill —— tenantId 的守卫写的是 `if (epsId == null)`
// （复制粘贴 bug）：调用方传了 epsId 时 Java 不填 tenant_id，这里一并复刻。
// DIFF: update_by/update_time 属于 updateFill（Java 实体上标注 FieldFill.UPDATE），
// insert 时不填，两列保持 NULL。
func (h *handler) withInsertAudit(c *gin.Context, cols map[string]any) {
	now := auditNow()
	if _, ok := cols["create_time"]; !ok {
		cols["create_time"] = now
	}
	if _, ok := cols["create_by"]; !ok {
		cols["create_by"] = currentUserID(c)
	}
	originalEps := cols["eps_id"]
	if _, ok := cols["eps_id"]; !ok {
		cols["eps_id"] = currentEpsID(c)
	}
	if originalEps == nil {
		if _, ok := cols["tenant_id"]; !ok {
			cols["tenant_id"] = currentTenantID(c)
		}
	}
	if _, ok := cols["del_flag"]; !ok {
		cols["del_flag"] = "0"
	}
}

// withUpdateAudit 对应 updateFill：update_by / update_time。
func withUpdateAudit(c *gin.Context, cols map[string]any) {
	now := auditNow()
	if _, ok := cols["update_time"]; !ok {
		cols["update_time"] = now
	}
	if _, ok := cols["update_by"]; !ok {
		cols["update_by"] = currentUserID(c)
	}
}

// pickColumns 把请求体 JSON 的键（驼峰）翻译成列名，未列入白名单的键直接丢弃。
//
// DIFF: MyBatis-Plus 的 updateById/insert 只写“非 null”属性；这里用「请求体里出现过」代替
// 「Java 侧非 null」，语义一致（未传 = 不改）。
func pickColumns(body map[string]any, allowed map[string]string) map[string]any {
	cols := make(map[string]any, len(body))
	for key, value := range body {
		column, ok := allowed[key]
		if !ok {
			continue
		}
		cols[column] = value
	}
	return cols
}

// insertRow 执行 INSERT（对应 BaseMapper.insert），返回主键。
func (h *handler) insertRow(ctx context.Context, table string, cols map[string]any) error {
	return insertRowTx(h.app.DB.WithContext(ctx), table, cols)
}

// insertRowTx 是 insertRow 的事务版本：调用方已在 db.Transaction 内时使用，保证同一事务。
func insertRowTx(tx *gorm.DB, table string, cols map[string]any) error {
	return tx.Table(table).Create(cols).Error
}

// mpNonNullCols 对应 MyBatis-Plus 的默认字段策略 NOT_NULL：null 属性不进 INSERT/UPDATE 的列清单，
// 于是新增时取库里的默认值、更新时保持旧值。Go 侧用 nil 指针表达「Java 侧是 null」，需要先剔掉。
func mpNonNullCols(cols map[string]any) map[string]any {
	out := make(map[string]any, len(cols))
	for name, value := range cols {
		if value == nil {
			continue
		}
		rv := reflect.ValueOf(value)
		if rv.Kind() == reflect.Ptr && rv.IsNil() {
			continue
		}
		out[name] = value
	}
	return out
}

// updateRow 执行 UPDATE ... WHERE id = ?（对应 BaseMapper.updateById），返回受影响行数。
//
// JAVA 对照: 实体上的 @TableLogic 会让 MP 在 updateById 时追加 del_flag = '0'。
func (h *handler) updateRow(ctx context.Context, table, id string, cols map[string]any) (int64, error) {
	return updateRowTx(h.app.DB.WithContext(ctx), table, id, cols)
}

// updateRowTx 是 updateRow 的事务版本。
func updateRowTx(tx *gorm.DB, table, id string, cols map[string]any) (int64, error) {
	if len(cols) == 0 {
		return 0, nil
	}
	res := tx.Table(table).Where("id = ? AND del_flag = '0'", id).Updates(cols)
	return res.RowsAffected, res.Error
}

// softDeleteByIDs 对应 mapper 里的 deleteXxxByIds：update ... set del_flag = '1' where id in (...)。
func (h *handler) softDeleteByIDs(ctx context.Context, table string, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	tx := h.app.DB.WithContext(ctx).Table(table).Where("id IN ? AND del_flag = '0'", ids).Update("del_flag", "1")
	return tx.RowsAffected, tx.Error
}

// bindJSON 解析 @RequestBody。
func bindJSON(c *gin.Context, dest any) error {
	return c.ShouldBindJSON(dest)
}

// ---------------------------------------------------------------------------
// 查询参数覆盖
// ---------------------------------------------------------------------------

// 控制器里常见的「入参规整」（如 carNo 为空时补 -1、sectionCode 含 all 时清空）
// 不能靠改写 URL 实现：gin 会把第一次 c.Query 的解析结果缓存在 context 里。
// 这里用显式覆盖表，配合 queryParam 读取。

const queryOverridesKey = "manager_query_overrides"

// setQueryOverride 覆盖（value 为空串表示「视作没传」）某个查询参数。
func setQueryOverride(c *gin.Context, name, value string) {
	m, ok := c.Get(queryOverridesKey)
	table, _ := m.(map[string]string)
	if !ok || table == nil {
		table = map[string]string{}
	}
	table[name] = value
	c.Set(queryOverridesKey, table)
}

// queryParam 对应 queryParam 语义：先查覆盖表，再退回原始 query。
func queryParam(c *gin.Context, name string) string {
	if m, ok := c.Get(queryOverridesKey); ok {
		if table, ok2 := m.(map[string]string); ok2 {
			if v, ok3 := table[name]; ok3 {
				return strings.TrimSpace(v)
			}
		}
	}
	return strings.TrimSpace(c.Query(name))
}

// jsonBody 读取 @RequestBody 为 map，用于「只更新请求里出现的字段」。
func jsonBody(c *gin.Context) (map[string]any, error) {
	body := map[string]any{}
	if err := c.ShouldBindJSON(&body); err != nil {
		return nil, err
	}
	return body, nil
}

// notWorkbookMsg 是 ImportSysUtil 走 POI 分支时，非工作簿内容的消息。
const notWorkbookMsg = "No valid entries or contents found, this is not a valid OOXML (Office Open XML) file"

// ole2IsNotXSSFMsg 是 ImportSysUtil 用 XSSFWorkbook 读到老 .xls 时 POI 的消息。
const ole2IsNotXSSFMsg = "The supplied data appears to be in the OLE2 Format. " +
	"You are calling the part of POI that deals with OOXML (Office Open XML) Documents. " +
	"You need to call a different part of POI to process this data (eg HSSF instead of XSSF)"
