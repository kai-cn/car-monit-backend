// JAVA 对照: Spring MVC @RestController 扫描 + SecurityConfig 过滤器链
// 类/职责: 路由装配与模块注册表
// 对应 Go 文件: internal/router/router.go
//
// DIFF: Spring 靠注解扫描自动注册 URL；Go 用显式注册函数。
// 各业务模块在自己的包里提供 Register(reg *Registry)，在 init 中调用 router.RegisterModule，
// 由 cmd/server/main.go 以空导入（_ "car-monit-go/internal/modules/xxx"）触发注册。
package router

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/handler"
	"car-monit-go/internal/middleware"
)

// Registry 暴露根引擎与“已登录”分组，模块按需选择挂载点。
//   - reg.Engine：匿名可访问（如 /system/file/view/**、/system/notice/view/**）
//   - reg.Authed：经过 JWT 认证的接口
type Registry struct {
	Engine *gin.Engine
	Authed *gin.RouterGroup
	App    *app.App
}

// ModuleRegister 业务模块的路由注册函数。
type ModuleRegister func(reg *Registry)

var modules []ModuleRegister

// RegisterModule 供模块包 init() 调用；可重复调用，按注册顺序挂载。
func RegisterModule(fn ModuleRegister) {
	modules = append(modules, fn)
}

// Setup 构建 gin 引擎：全局中间件 -> 匿名端点 -> 认证端点 -> 业务模块。
func Setup(a *app.App) *gin.Engine {
	engine := gin.New()
	engine.Use(
		middleware.TraceID(a),
		middleware.Recovery(a),
		middleware.CORS(),
		middleware.XSS(a),
	)
	engine.NoRoute(middleware.NoRoute)

	authH := handler.NewAuthHandler(a)

	// JAVA 对照: SecurityConfig 中的 permitAll 端点
	engine.GET("/", authH.Index)
	engine.GET("/healthz", handler.Health(a))
	engine.GET("/captchaImage", authH.CaptchaImage)
	engine.POST("/login", authH.Login)
	// JAVA 对照: Spring Security LogoutFilter（logoutUrl "/logout"）
	engine.POST("/logout", authH.Logout)

	authed := engine.Group("")
	authed.Use(middleware.Auth(a))
	authed.GET("/getInfo", authH.GetInfo)
	authed.GET("/getRouters", authH.GetRouters)

	reg := &Registry{Engine: engine, Authed: authed, App: a}
	for _, fn := range modules {
		fn(reg)
	}
	return engine
}
