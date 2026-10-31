// JAVA 对照: Spring 组件扫描 + @RequestMapping 汇总
// 类/职责: system 模块路由总装配
// 对应 Go 文件: internal/modules/system/register.go
//
// DIFF: Java 由容器反射发现五个 @RestController；Go 需要显式 init 注册，
// 由 main.go 的空导入触发。
package system

import "car-monit-go/internal/router"

func init() { router.RegisterModule(Register) }

// Register 装配 /system/user|role|menu|dept|post 五组路由。
func Register(reg *router.Registry) {
	svc := newService(reg.App)
	registerUser(reg, svc)
	registerRole(reg, svc)
	registerMenu(reg, svc)
	registerDept(reg, svc)
	registerPost(reg, svc)
}
