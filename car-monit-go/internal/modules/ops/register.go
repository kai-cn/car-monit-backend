// JAVA 对照: Spring 组件扫描自动注册 @RestController
// 类/职责: ops 模块路由注册入口（缓存/服务器/登录日志/操作日志/在线用户/通用上传下载/模板/测试）
// 对应 Go 文件: internal/modules/ops/register.go
//
// DIFF: Go 没有注解扫描，模块在 init() 里把 Register 交给 router 注册表。
package ops

import "car-monit-go/internal/router"

func init() { router.RegisterModule(Register) }

// Register 挂载 ops 模块的全部控制器。
func Register(reg *router.Registry) {
	newCacheRoutes(reg.Authed, reg.App)
	newServerRoutes(reg.Authed, reg.App)
	newCommonRoutes(reg, reg.App)
	newDownTemplateRoutes(reg.Authed, reg.App)
	newTestRoutes(reg.Authed)
	newLogininforRoutes(reg.Authed, reg.App)
	newOnlineRoutes(reg.Authed, reg.App)
	newOperLogRoutes(reg.Authed, reg.App)
}
