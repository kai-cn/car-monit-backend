// JAVA 对照: Spring 组件扫描自动注册 GenController
// 类/职责: generator 模块路由注册（/tool/gen/**）
// 对应 Go 文件: internal/modules/generator/register.go
//
// DIFF: Java 由 @PreAuthorize / @Log 注解声明权限与操作日志；Go 在注册处显式挂中间件。
// 注册顺序照抄 Spring 的字面量优先规则：/{talbleId} 放在最后，否则 /list、/all/list、
// /db/list、/batchGenCode 会被它吃掉。
// DIFF: 三个没有 @PreAuthorize 的映射（/all/list、/getColumnList、/getAllColumnList）
// 在 Java 里落到 anyRequest().authenticated()，这里同样只要求登录。
package generator

import (
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
)

func init() { router.RegisterModule(Register) }

// Register 挂载 /tool/gen 下的全部端点。
func Register(reg *router.Registry) {
	h := newGenHandler(reg.App)
	group := reg.Authed.Group("/tool/gen")

	group.GET("/list", middleware.Perm("tool:gen:list"), h.genList)
	group.GET("/all/list", h.getAllGenerateTableList)
	group.GET("/db/list", middleware.Perm("tool:gen:list"), h.dataList)
	group.GET("/column/:talbleId", middleware.Perm("tool:gen:list"), h.columnList)
	group.POST("/getColumnList", h.getColumnList)
	group.POST("/getAllColumnList", h.getAllColumnList)

	group.POST("/importTable",
		middleware.Perm("tool:gen:list"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessImport),
		h.importTableSave)
	group.PUT("",
		middleware.Perm("tool:gen:edit"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessUpdate),
		h.editSave)
	group.DELETE("/:tableIds",
		middleware.Perm("tool:gen:remove"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessDelete),
		h.remove)

	group.GET("/preview/:tableId", middleware.Perm("tool:gen:preview"), h.preview)
	group.GET("/download/:tableName",
		middleware.Perm("tool:gen:code"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessGenCode),
		h.download)
	group.GET("/genCode/:tableName",
		middleware.Perm("tool:gen:code"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessGenCode),
		h.genCode)
	group.GET("/synchDb/:tableName",
		middleware.Perm("tool:gen:edit"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessUpdate),
		h.synchDb)
	group.GET("/batchGenCode",
		middleware.Perm("tool:gen:code"),
		middleware.OperLog(reg.App, "代码生成", middleware.BusinessGenCode),
		h.batchGenCode)

	// 必须最后：/{talbleId} 会匹配所有单段 GET。
	group.GET("/:talbleId", middleware.Perm("tool:gen:query"), h.getInfo)
}
