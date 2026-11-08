// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/{SysUserController,SysRoleController,SysMenuController,SysDeptController,SysPostController}.java
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/{SysUserServiceImpl,SysRoleServiceImpl,SysMenuServiceImpl,SysDeptServiceImpl,SysPostServiceImpl}.java
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/controller/BaseController.java:50-150
// 类/职责: 系统管理模块（用户/角色/菜单/部门/岗位）的公共装配、常量与查询辅助
// 对应 Go 文件: internal/modules/system/common.go
//
// DIFF: Java 的 Controller/Service/Mapper 三层由 Spring + MyBatis 拼装；
// Go 侧统一为一个包内的 service（含全部 @Service 方法与 Mapper SQL），
// handler 只做参数绑定与响应封装，SQL 全部参数化。
package system

import (
	"context"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/model"
	"car-monit-go/internal/service/menusvc"
	"car-monit-go/internal/web"
)

// JAVA 对照: com/ruoyi/common/constant/UserConstants.java:82-95
const (
	uniqueOld    = "0" // UserConstants.UNIQUE_OLD
	notUniqueOld = "1" // UserConstants.NOT_UNIQUE_OLD

	userTypeOrg = "1" // 机构用户

	deptNormal  = "0"
	deptDisable = "1"

	statusNormal   = "0"
	statusDisabled = "1"

	// JAVA 对照: Constants.PROCUREMENT_MANAGER_ROLE_KEY
	procurementManagerRoleKey = "cgjl_manager"
	// JAVA 对照: UserConstants.DEFAULT_PWD
	defaultPwd = "Sys@cg0624!"

	// JAVA 对照: SysUserServiceImpl.importUser -> configService.selectConfigByKey
	initPasswordConfigKey = "sys.user.initPassword"
)

// service 汇总五个 Controller 依赖的 @Service Bean。
// JAVA 对照: @Autowired private ISysUserService / ISysRoleService / ISysMenuService /
// ISysDeptService / ISysPostService / TokenService / SysPermissionService
type service struct {
	app   *app.App
	menus *menusvc.Service
}

func newService(a *app.App) *service {
	return &service{app: a, menus: menusvc.New(a.DB)}
}

func (s *service) db(ctx context.Context) *gorm.DB { return s.app.DB.WithContext(ctx) }

// currentUser 对应 SecurityUtils.getLoginUser().getUser()。
func currentUser(c *gin.Context) *model.SysUser {
	if lu := auth.CurrentUser(c); lu != nil {
		return lu.User
	}
	return nil
}

// currentTenantID 对应 SecurityUtils.getTenantId()（未登录返回 -1）。
func currentTenantID(c *gin.Context) int64 {
	if u := currentUser(c); u != nil {
		return model.Int64Val(u.TenantID)
	}
	return -1
}

// currentDeptID 对应 SecurityUtils.getEpsId()（未登录返回 -1）。
func currentDeptID(c *gin.Context) int64 {
	if u := currentUser(c); u != nil {
		return u.DeptID
	}
	return -1
}

// queryInt64 读取可选整型查询参数；Java 的包装类型 null 语义用 *int64 表达。
func queryInt64(c *gin.Context, key string) *int64 {
	raw := strings.TrimSpace(c.Query(key))
	if raw == "" {
		return nil
	}
	v, err := strconv.ParseInt(raw, 10, 64)
	if err != nil {
		return nil
	}
	return &v
}

// queryInt 读取可选 int 查询参数。
func queryInt(c *gin.Context, key string) *int {
	v := queryInt64(c, key)
	if v == nil {
		return nil
	}
	n := int(*v)
	return &n
}

// queryBool 对应 Spring 对 Boolean 的绑定（true/false，缺省 false）。
func queryBool(c *gin.Context, key string) bool {
	switch strings.ToLower(strings.TrimSpace(c.Query(key))) {
	case "true", "1", "yes", "on":
		return true
	}
	return false
}

// queryStr 去掉首尾空白，等价 CommonUtil.isNull(...)。
func queryStr(c *gin.Context, key string) string {
	return strings.TrimSpace(c.Query(key))
}

// parseIDList 对应 Spring 对 Long[] 路径参数的绑定（"1,2,3"）。
func parseIDList(raw string) ([]int64, error) {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return nil, web.NewServiceError("参数格式错误")
	}
	parts := strings.Split(raw, ",")
	out := make([]int64, 0, len(parts))
	for _, p := range parts {
		v, err := strconv.ParseInt(strings.TrimSpace(p), 10, 64)
		if err != nil {
			return nil, web.NewServiceError("参数格式错误：%s", p)
		}
		out = append(out, v)
	}
	return out, nil
}

// placeholders 生成 "?,?,?"。
func placeholders(n int) string {
	if n <= 0 {
		return ""
	}
	return strings.TrimSuffix(strings.Repeat("?,", n), ",")
}

// encodePassword 对应 SecurityUtils.encryptPassword（BCryptPasswordEncoder，strength=10）。
func encodePassword(plain string) (string, error) {
	b, err := bcrypt.GenerateFromPassword([]byte(plain), bcrypt.DefaultCost)
	if err != nil {
		return "", web.WrapServiceError(err, "密码加密失败")
	}
	return string(b), nil
}

// beginTime/endTime 对应 BaseEntity.params["beginTime"/"endTime"]。
func queryParamsTime(c *gin.Context, key string) string {
	if v := strings.TrimSpace(c.Query("params[" + key + "]")); v != "" {
		return v
	}
	return strings.TrimSpace(c.Query("params." + key))
}

// now 对应 Java 的 sysdate() / new Date()。
func now() web.DateTime { return web.NewDateTime(time.Now()) }

// nonNilSlice 保证 JSON 输出 [] 而不是 null（Java 侧 List 不会返回 null）。
func nonNilSlice[T any](in []T) []T {
	if in == nil {
		return make([]T, 0)
	}
	return in
}

// queryPaged 统一实现 PageHelper 的“可选分页”：
//   - pd.HasPage 时执行 COUNT + LIMIT/OFFSET（对应 PageHelper.startPage）
//   - 否则一次性返回全部（对应未调用 startPage 的场景）
//
// JAVA 对照: com/ruoyi/common/utils/PageUtils.java:startPage + PageInfo.getTotal()
// DIFF: Java PageHelper 通过 ThreadLocal 改写 SQL；Go 显式拼接 limit/offset。
func queryPaged[T any](ctx context.Context, db *gorm.DB, pd web.PageDomain, base string, args []any, orderBy string) ([]T, int64, error) {
	if err := pd.StartPageError(); err != nil {
		return nil, 0, err
	}
	sql := base
	if orderBy != "" {
		sql += " order by " + orderBy
	}
	rows := make([]T, 0)
	var total int64
	if pd.HasPage {
		if err := db.WithContext(ctx).Raw("select count(1) from ("+base+") t", args...).Scan(&total).Error; err != nil {
			return nil, 0, err
		}
		if pd.SkipQuery(total) {
			return rows, total, nil
		}
		sql += " limit ? offset ?"
		lim, off := pd.LimitOffset(total)
		args = append(append([]any{}, args...), lim, off)
	}
	if err := db.WithContext(ctx).Raw(sql, args...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !pd.HasPage {
		total = int64(len(rows))
	}
	return rows, total, nil
}

// orderByOr 复刻 PageHelper 对客户端 orderByColumn 的处理：客户端给了就覆盖默认排序。
func orderByOr(pd web.PageDomain, fallback string) string {
	if v := pd.OrderBy(); v != "" {
		return v
	}
	return fallback
}
