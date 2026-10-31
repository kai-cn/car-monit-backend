// JAVA 对照: Spring 组件扫描自动注册 @RestController
// 类/职责: systemaux 模块路由注册入口（参数/字典/公告/首页菜单/升级/个人中心/文件）
// 对应 Go 文件: internal/modules/systemaux/register.go
//
// DIFF: Go 没有注解扫描，模块在 init() 里把 Register 交给 router 注册表。
package systemaux

import "car-monit-go/internal/router"

func init() { router.RegisterModule(Register) }

// Register 挂载 systemaux 模块的全部控制器。
func Register(reg *router.Registry) {
	registerConfig(reg)
	registerDict(reg)
	registerNotice(reg)
	registerIndexMenu(reg)
	registerUpgrade(reg)
	registerProfile(reg)
	registerFile(reg)
}
