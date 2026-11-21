// JAVA 对照: com/ruoyi/common/utils/SecurityUtils.java（getUserId/getEpsId/getTenantId/getUserRealName）
// JAVA 对照: com/ruoyi/common/utils/StringUtils.java:getUUID
// JAVA 对照: com/ruoyi/common/utils/PageUtils.java（startPage）
// 类/职责: service 公共依赖、动态 SQL 拼装、分页、当前操作人快照
// 对应 Go 文件: internal/modules/flow/sqlutil.go
//
// DIFF: Java 通过 SecurityUtils 读取 ThreadLocal 登录态；Go 由 handler 构造 actor 显式传入 service。
// DIFF: PageHelper 在 ThreadLocal 中拦截 SQL；Go 显式追加 ORDER BY + LIMIT/OFFSET 并单独做 COUNT。
// DIFF: Mapper 中的 ${tableName} / ${backCol1} 是字符串拼接，Go 侧加标识符白名单校验，避免注入。
package flow

import (
	"context"
	"errors"
	"fmt"
	"reflect"
	"regexp"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/config"
	"car-monit-go/internal/model"
	"car-monit-go/internal/platform/conv"
	"car-monit-go/internal/web"
)

// Service 汇总 flow 模块的数据库访问（对应 7 个 ServiceImpl + 7 个 Mapper 的能力）。
type Service struct {
	db  *gorm.DB
	cfg *config.Config
}

func NewService(a *app.App) *Service {
	return &Service{db: a.DB, cfg: a.Cfg}
}

// actor 对应 SecurityUtils 读取的当前登录用户字段。
type actor struct {
	UserID   int64
	EpsID    int64
	TenantID int64
	RealName string
}

func actorFrom(c *gin.Context) actor {
	lu := auth.CurrentUser(c)
	a := actor{EpsID: -1, RealName: "用户"}
	if lu == nil || lu.User == nil {
		return a
	}
	a.UserID = lu.User.UserID
	a.EpsID = lu.User.DeptID
	a.TenantID = model.Int64Val(lu.User.TenantID)
	a.RealName = model.Str(lu.User.NickName)
	return a
}

func strPtr(v string) *string { return conv.Str(v) }
func i64Ptr(v int64) *int64   { return conv.Int64(v) }

func strVal(v *string) string {
	if v == nil {
		return ""
	}
	return *v
}

func i64Val(v *int64) int64 {
	if v == nil {
		return 0
	}
	return *v
}

// newUUID 对应 StringUtils.getUUID()：去掉 "-" 的 UUID。
func newUUID() string { return strings.ReplaceAll(uuid.NewString(), "-", "") }

// colset 对应 MyBatis 的 <trim prefix="SET"/("(") + <if test="x != null">。
type colset struct {
	cols []string
	vals []any
}

func (c *colset) add(col string, v any) {
	if v == nil {
		return
	}
	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Ptr, reflect.Interface, reflect.Map, reflect.Slice:
		if rv.IsNil() {
			return
		}
	}
	c.cols = append(c.cols, col)
	c.vals = append(c.vals, v)
}

func (c *colset) empty() bool { return len(c.cols) == 0 }

func (c *colset) insert(ctx context.Context, db *gorm.DB, table string) error {
	if c.empty() {
		return errors.New("没有可插入的字段")
	}
	marks := make([]string, len(c.cols))
	for i := range marks {
		marks[i] = "?"
	}
	sql := "insert into " + table + " (" + strings.Join(c.cols, ", ") + ") values (" + strings.Join(marks, ", ") + ")"
	return db.WithContext(ctx).Exec(sql, c.vals...).Error
}

func (c *colset) update(ctx context.Context, db *gorm.DB, table, id string) error {
	if c.empty() {
		return errors.New("没有可更新的字段")
	}
	sets := make([]string, len(c.cols))
	for i, col := range c.cols {
		sets[i] = col + " = ?"
	}
	args := append(append([]any{}, c.vals...), id)
	sql := "update " + table + " set " + strings.Join(sets, ", ") + " where ID = ?"
	return db.WithContext(ctx).Exec(sql, args...).Error
}

// pageSQL 对应 PageHelper：追加排序与分页。
// pageSQL 对应 PageHelper：追加排序与分页。total 用于 reasonable 越界钳位（页码超出总页数回到末页）。
func pageSQL(base string, args []any, pd web.PageDomain, defaultOrder string, total int64) (string, []any) {
	q := base + " order by " + pd.OrderByWithDefault(defaultOrder)
	if pd.HasPage {
		q += " limit ? offset ?"
		lim, off := pd.LimitOffset(total)
		args = append(args, lim, off)
	}
	return q, args
}

func countRows(ctx context.Context, db *gorm.DB, base, where string, args []any) (int64, error) {
	var total int64
	sql := "select count(1) from " + base + " where 1 = 1" + where
	if err := db.WithContext(ctx).Raw(sql, args...).Row().Scan(&total); err != nil {
		return 0, err
	}
	return total, nil
}

var identifierPattern = regexp.MustCompile(`^[A-Za-z0-9_]+$`)

// safeIdentifier 校验 Mapper 里 ${} 拼接的表名。
func safeIdentifier(name string) (string, error) {
	if !identifierPattern.MatchString(name) {
		return "", fmt.Errorf("非法的表名: %s", name)
	}
	return name, nil
}

// nowDateTime 对应 DateUtils.getTimestamp()。
func nowDateTime() *web.DateTime {
	d := web.NewDateTime(time.Now())
	return &d
}
