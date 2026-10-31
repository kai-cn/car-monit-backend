// JAVA 对照: com/ruoyi/common/core/controller/BaseController.java
// JAVA 对照: com/ruoyi/common/utils/StringUtils.java（split/isEmpty/trim）
// 类/职责: flow 模块 handler 公共设施 —— 参数绑定、路径 ids 拆分、分页查询
// 对应 Go 文件: internal/modules/flow/handler.go
//
// DIFF: Java 控制器把 Service 结果直接返回，异常交给 @RestControllerAdvice；
// Go 显式返回 AjaxResult，业务校验用 web.ErrorMsg，数据库错误用 web.ErrorResult。
package flow

import (
	"context"
	"reflect"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/web"
)

// handler 汇总 7 个 flow 控制器共用的依赖（对应 Spring 注入的 Service）。
type handler struct {
	app *app.App
	svc *Service
}

func newHandler(a *app.App) *handler { return &handler{app: a, svc: NewService(a)} }

// bindQuery 对应 Spring 把 query string 绑定到实体（无 @RequestBody）。
func bindQuery(c *gin.Context, dest any) error {
	if err := c.ShouldBindQuery(dest); err != nil {
		return web.NewServiceError("请求参数解析异常：%s", err.Error())
	}
	return nil
}

// bindBody 对应 @RequestBody。
func bindBody(c *gin.Context, dest any) error {
	if err := c.ShouldBindJSON(dest); err != nil {
		return web.NewServiceError("请求参数解析异常：%s", err.Error())
	}
	return nil
}

// splitIDs 对应 @PathVariable String[] ids：逗号分隔，丢弃尾部空串。
func splitIDs(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	for len(parts) > 0 && parts[len(parts)-1] == "" {
		parts = parts[:len(parts)-1]
	}
	return parts
}

// ptrTrim 对应 StringUtils.trim(String)：nil 归一为空串。
func ptrTrim(v *string) string {
	if v == nil {
		return ""
	}
	return strings.TrimSpace(*v)
}

// JAVA 对照: com/ruoyi/common/utils/PageUtils.java + PageInfo.getTotal()
// queryList 执行一条列表 SQL：分页时显式 COUNT + LIMIT/OFFSET，不分页时 total 取行数。
//
// DIFF: PageHelper 在拦截器里隐式生成 count 与 limit；这里显式拼装。
func queryList(ctx context.Context, db *gorm.DB, selectSQL, fromSQL, cond, order string,
	args []any, pd web.PageDomain, dest any) (int64, error) {
	if pd.HasPage {
		total, err := countRows(ctx, db, fromSQL, cond, args)
		if err != nil {
			return 0, err
		}
		sqlStr, sqlArgs := pageSQL("select "+selectSQL+" from "+fromSQL+" where 1 = 1"+cond, args, pd, order)
		if err := db.WithContext(ctx).Raw(sqlStr, sqlArgs...).Scan(dest).Error; err != nil {
			return 0, err
		}
		return total, nil
	}
	sqlStr, sqlArgs := pageSQL("select "+selectSQL+" from "+fromSQL+" where 1 = 1"+cond, args, pd, order)
	if err := db.WithContext(ctx).Raw(sqlStr, sqlArgs...).Scan(dest).Error; err != nil {
		return 0, err
	}
	return sliceLen(dest), nil
}

// sliceLen 返回 dest 指向的切片长度（dest 必须是 *[]T）。
func sliceLen(dest any) int64 {
	v := reflect.ValueOf(dest)
	if v.Kind() == reflect.Ptr && !v.IsNil() && v.Elem().Kind() == reflect.Slice {
		return int64(v.Elem().Len())
	}
	return 0
}

// orEmpty 用于把可能为 nil 的字符串安全取出来。
func orEmpty(v *string) string {
	if v == nil {
		return ""
	}
	return *v
}

// isNull 对应 CommonUtil.isNull：null -> ""，否则 toString().trim()。
func isNull(s string) string { return strings.TrimSpace(s) }
