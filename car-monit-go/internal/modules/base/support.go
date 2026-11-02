// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/CommonUtil.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/controller/BaseController.java
// 类/职责: base 模块公共设施 —— 字符串工具、动态 WHERE 构造、分页查询、查询日志
// 对应 Go 文件: internal/modules/base/support.go
//
// DIFF: Java 的 PageHelper 通过 ThreadLocal + MyBatis 拦截器隐式改写 SQL（startPage/getDataTable），
// Go 没有隐式拦截：handler 显式读取 PageDomain，显式执行 COUNT，再显式拼 LIMIT/OFFSET。
// DIFF: MyBatis 的 <if test="x != null and x != ”"> 由 buildWhere 逐条显式追加，
// 参数一律走 ? 占位符，列名只来自本包写死的常量。
package base

import (
	"context"
	"fmt"
	"reflect"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// handler 汇总 base 模块各控制器的依赖（对应 Spring 注入的 Service/Mapper）。
type handler struct {
	app *app.App
}

func newHandler(a *app.App) *handler { return &handler{app: a} }

// 雪花号状态（对应 MyBatis-Plus IdWorker 的 synchronized 生成器）。
var (
	snowflakeMu         sync.Mutex
	lastSnowflakeMillis int64 = -1
	snowflakeSeq        int64
)

// ---------------------------------------------------------------------------
// com.ruoyi.common.utils.CommonUtil
// ---------------------------------------------------------------------------

// isNull 对应 CommonUtil.isNull：null -> ""，否则 toString().trim()。
func isNull(v any) string {
	switch x := v.(type) {
	case nil:
		return ""
	case string:
		return strings.TrimSpace(x)
	case *string:
		if x == nil {
			return ""
		}
		return strings.TrimSpace(*x)
	case *int64:
		if x == nil {
			return ""
		}
		return strconv.FormatInt(*x, 10)
	case *int:
		if x == nil {
			return ""
		}
		return strconv.Itoa(*x)
	case *float64:
		if x == nil {
			return ""
		}
		return strconv.FormatFloat(*x, 'f', -1, 64)
	default:
		return strings.TrimSpace(fmt.Sprint(x))
	}
}

// strOf 把可空字符串取成普通字符串（nil -> ""）。
func strOf(v any) string { return isNull(v) }

// strPtr 生成可空字符串指针。
func strPtr(s string) *string { return &s }

// isNotBlank 对应 CommonUtil.isNotBlank（StringUtils.isNotBlank）。
func isNotBlank(v any) bool { return isNull(v) != "" }

// isBlank 对应 CommonUtil.isBlank（StringUtils.isBlank）。
func isBlank(v any) bool { return isNull(v) == "" }

// deleteEnd 对应 CommonUtil.deleteEnd：去掉末尾一个逗号。
func deleteEnd(v any) string { return strings.TrimSuffix(isNull(v), ",") }

// splitCSV 对应 Java 的 String.split(",")：丢弃结果中的尾部空串。
func splitCSV(s string) []string {
	parts := strings.Split(s, ",")
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

// newUUID 对应 MyBatis-Plus IdWorker.get32UUID()：32 位无连字符 UUID。
func newUUID() string { return strings.ReplaceAll(uuid.NewString(), "-", "") }

// newUUIDDashed 对应 Java 的 UUID.randomUUID().toString()（ExcelUtil 文件名用带横杠形态）。
func newUUIDDashed() string { return uuid.NewString() }

// nextSnowflakeID 对应 MyBatis-Plus IdWorker.nextId()（全局 id-type: ASSIGN_ID）。
//
// DIFF: 位宽与 MP 一致（41 位毫秒 | 22 位序列，datacenter/worker 固定 0）；
// 具体数值不可比（时间相关），只保证 19 位、单实例内单调递增。
func nextSnowflakeID() string {
	const epoch = int64(1288834974657)
	snowflakeMu.Lock()
	defer snowflakeMu.Unlock()
	now := time.Now().UnixMilli()
	if now < lastSnowflakeMillis {
		now = lastSnowflakeMillis
	}
	if now == lastSnowflakeMillis {
		snowflakeSeq = (snowflakeSeq + 1) & 0xFFF
		if snowflakeSeq == 0 {
			for now <= lastSnowflakeMillis {
				now = time.Now().UnixMilli()
			}
		}
	} else {
		snowflakeSeq = 0
	}
	lastSnowflakeMillis = now
	return strconv.FormatInt(((now-epoch)<<22)|snowflakeSeq, 10)
}

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
	// OrderBy 是排序子句（不含 "ORDER BY"）。
	OrderBy string
	// Page 来自 web.Page(c)。
	Page web.PageDomain
}

// list 执行分页查询，返回 total（对应 PageInfo.getTotal / list.size()）。
//
// DIFF: Java 由 PageHelper 在拦截器里生成 count 语句；这里显式拼 COUNT(1)，
// JOIN 与 WHERE 与主查询完全一致。
func (h *handler) list(ctx context.Context, q listQuery, dest any) (int64, error) {
	baseSQL := q.FromSQL + q.Where.SQL()
	var total int64
	if q.Page.HasPage {
		countSQL := "SELECT COUNT(1) " + baseSQL
		if err := h.app.DB.WithContext(ctx).Raw(countSQL, q.Where.Args()...).Scan(&total).Error; err != nil {
			return 0, err
		}
	}

	sqlStr := "SELECT " + q.SelectSQL + " " + baseSQL
	if q.OrderBy != "" {
		sqlStr += " ORDER BY " + q.OrderBy
	}
	args := q.Where.Args()
	if q.Page.HasPage {
		sqlStr += " LIMIT ? OFFSET ?"
		args = append(args, q.Page.Limit(), q.Page.Offset())
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
// 字典（对应 ISysDictDataService.selectDictDataMap）
// ---------------------------------------------------------------------------

type dictDataRow struct {
	DictValue string `gorm:"column:dict_value"`
	DictLabel string `gorm:"column:dict_label"`
}

// dictValueLabel 对应 SysDictDataServiceImpl.selectDictDataMap：dictValue -> dictLabel。
func (h *handler) dictValueLabel(ctx context.Context, dictType string) (map[string]string, error) {
	var rows []dictDataRow
	err := h.app.DB.WithContext(ctx).
		Table("sys_dict_data").
		Select("dict_value, dict_label").
		Where("dict_type = ?", dictType).
		Order("dict_sort ASC").
		Scan(&rows).Error
	if err != nil {
		return nil, err
	}
	m := make(map[string]string, len(rows))
	for _, r := range rows {
		m[r.DictValue] = r.DictLabel
	}
	return m, nil
}

// ---------------------------------------------------------------------------
// 审计字段（对应 MyBatisPlusHandlerConfig 的自动填充）
// ---------------------------------------------------------------------------

// insertAudit 对应 insertFill：create_time / create_by / eps_id / tenant_id。
//
// JAVA 对照: MyBatisPlusHandlerConfig#insertFill —— tenantId 的守卫条件是「调用方未传 epsId」。
// DIFF: Java 由 MetaObjectHandler 在 insert 时自动填；Go 在拼 INSERT 前显式调用。
func (h *handler) insertAudit(c *gin.Context, cols map[string]any) {
	now := time.Now()
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
	// update_by/update_time 不在此处填：Java 的 updateFill 只在 UPDATE 时触发，
	// insert 后这两列保持 NULL（BasePlusEntity 上标注的是 FieldFill.UPDATE）。
}

// updateAudit 对应 updateFill：update_by / update_time。
func updateAudit(c *gin.Context, cols map[string]any) {
	now := time.Now()
	if _, ok := cols["update_time"]; !ok {
		cols["update_time"] = now
	}
	if _, ok := cols["update_by"]; !ok {
		cols["update_by"] = currentUserID(c)
	}
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
// 请求体
// ---------------------------------------------------------------------------

// bindJSON 解析 @RequestBody。
func bindJSON(c *gin.Context, dest any) error { return c.ShouldBindJSON(dest) }

// jsonBody 读取 @RequestBody 为 map（对应 Jackson 反序列化成实体后再取非 null 字段）。
func jsonBody(c *gin.Context) (map[string]any, error) {
	body := map[string]any{}
	if err := c.ShouldBindJSON(&body); err != nil {
		return nil, err
	}
	return body, nil
}

// bodyString 读取请求体里的字符串字段（null/缺失 -> ""）。
func bodyString(body map[string]any, key string) string {
	v, ok := body[key]
	if !ok || v == nil {
		return ""
	}
	switch x := v.(type) {
	case string:
		return strings.TrimSpace(x)
	case float64:
		return strconv.FormatFloat(x, 'f', -1, 64)
	default:
		return strings.TrimSpace(toString(x))
	}
}

// bodyInt 读取请求体里的整数字段，缺失 / null -> nil。
func bodyInt(body map[string]any, key string) *int64 {
	v, ok := body[key]
	if !ok || v == nil {
		return nil
	}
	switch x := v.(type) {
	case float64:
		n := int64(x)
		return &n
	case int:
		n := int64(x)
		return &n
	case int64:
		n := x
		return &n
	case string:
		if strings.TrimSpace(x) == "" {
			return nil
		}
		n, err := strconv.ParseInt(strings.TrimSpace(x), 10, 64)
		if err != nil {
			return nil
		}
		return &n
	default:
		return nil
	}
}

// toString 对应 String.valueOf（nil -> ""）。
func toString(v any) string {
	if v == nil {
		return ""
	}
	return strings.TrimSpace(fmt.Sprint(v))
}

// parseInt64 解析整数（对应 Integer.parseInt / Long.parseLong 的宽松版本）。
func parseInt64(s string) (int64, error) {
	return strconv.ParseInt(strings.TrimSpace(s), 10, 64)
}

// ---------------------------------------------------------------------------
// 查询日志（对应 ICarQueryLogService.queryLog）
// ---------------------------------------------------------------------------

// writeQueryLog 对应 ICarQueryLogService.queryLog：插入一条 car_query_log。
//
// JAVA 对照: CarQueryLogServiceImpl#queryLog —— userId 取登录用户、userIp 取登录 IP。
// DIFF: Java 用 SecurityUtils.getUserRealName()；Go 用当前登录用户的 nick_name。
func (h *handler) writeQueryLog(c *gin.Context, condition, modelType, menuPoint string) {
	userID := auth.CurrentUserID(c)
	cols := map[string]any{
		"id": newUUID(), "user_id": strconv.FormatInt(userID, 10),
		"user_name": auth.CurrentUsername(c), "user_ip": auth.ClientIP(c),
		"model_type": modelType, "menu_point": menuPoint,
		"query_condition": condition, "del_flag": "0",
		"create_by": userID, "create_time": time.Now(),
	}
	if err := h.app.DB.WithContext(c.Request.Context()).Table("car_query_log").Create(cols).Error; err != nil {
		h.app.Log.Warn("写入查询日志失败", "err", err)
	}
}
