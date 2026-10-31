// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/*.java
// 类/职责: flow 模块路由总装配（7 个控制器，55 个映射）
// 对应 Go 文件: internal/modules/flow/register.go
//
// DIFF: Spring 反射发现 @RestController；Go 显式注册。权限点、@Log 标题、HTTP 方法照抄，
// 其中 Java 里被注释掉的 @PreAuthorize 一律不挂（只有 listAll 与 flowname 全网关）。
package flow

import (
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
)

func init() { router.RegisterModule(Register) }

// Register 装配 /flow/** 全部路由。
func Register(reg *router.Registry) {
	h := newHandler(reg.App)
	auth := reg.Authed

	// ---------------------------------------------------------------- 我的申请
	auth.GET("/flow/applyinfo/list", h.applyInfoList)
	auth.GET("/flow/applyinfo/listAll", middleware.Perm("flow:applyinfo:list"), h.applyInfoListAll)
	auth.GET("/flow/applyinfo/export",
		middleware.OperLog(reg.App, "我的申请", middleware.BusinessExport), h.applyInfoExport)
	auth.GET("/flow/applyinfo/:id", h.applyInfoGet)
	auth.POST("/flow/applyinfo",
		middleware.OperLog(reg.App, "我的申请", middleware.BusinessInsert), h.applyInfoSave)
	auth.PUT("/flow/applyinfo",
		middleware.OperLog(reg.App, "我的申请", middleware.BusinessUpdate), h.applyInfoSave)
	auth.DELETE("/flow/applyinfo/:ids",
		middleware.OperLog(reg.App, "我的申请", middleware.BusinessDelete), h.applyInfoDelete)

	// ---------------------------------------------------------------- 流程_当前节点
	auth.GET("/flow/currentnode/list", h.currentNodeList)
	auth.GET("/flow/currentnode/export",
		middleware.OperLog(reg.App, "流程_当前节点", middleware.BusinessExport), h.currentNodeExport)
	// 两段路径的静态段放在 /:id 之前，避免后续扩展踩坑。
	auth.GET("/flow/currentnode/getInfoByBillId/:billOid", h.currentNodeGetByBillID)
	auth.GET("/flow/currentnode/:id", h.currentNodeGet)
	auth.POST("/flow/currentnode",
		middleware.OperLog(reg.App, "流程_当前节点", middleware.BusinessInsert), h.currentNodeSave)
	auth.PUT("/flow/currentnode",
		middleware.OperLog(reg.App, "流程_当前节点", middleware.BusinessUpdate), h.currentNodeSave)
	auth.DELETE("/flow/currentnode/:ids",
		middleware.OperLog(reg.App, "流程_当前节点", middleware.BusinessDelete), h.currentNodeDelete)
	auth.PUT("/flow/currentnode/saveFlowAuit", h.currentNodeAudit)
	auth.POST("/flow/currentnode/submitReturn", h.currentNodeSubmitReturn)
	auth.POST("/flow/currentnode/submitEntrustFlow", h.currentNodeSubmitEntrust)

	// ---------------------------------------------------------------- 审核历史记录
	auth.GET("/flow/flowlist/list", h.flowListList)
	auth.GET("/flow/flowlist/listnew", h.flowListNew)
	auth.GET("/flow/flowlist/export",
		middleware.OperLog(reg.App, "审核历史记录", middleware.BusinessExport), h.flowListExport)
	auth.GET("/flow/flowlist/:id", h.flowListGet)
	auth.POST("/flow/flowlist",
		middleware.OperLog(reg.App, "审核历史记录", middleware.BusinessInsert), h.flowListSave)
	auth.PUT("/flow/flowlist",
		middleware.OperLog(reg.App, "审核历史记录", middleware.BusinessUpdate), h.flowListSave)
	auth.DELETE("/flow/flowlist/:ids",
		middleware.OperLog(reg.App, "审核历史记录", middleware.BusinessDelete), h.flowListDelete)

	// ---------------------------------------------------------------- 系统消息处理人
	auth.GET("/flow/messagedispose/list", h.messageDisposeList)
	auth.GET("/flow/messagedispose/export",
		middleware.OperLog(reg.App, "系统消息处理人", middleware.BusinessExport), h.messageDisposeExport)
	auth.GET("/flow/messagedispose/:id", h.messageDisposeGet)
	auth.POST("/flow/messagedispose",
		middleware.OperLog(reg.App, "系统消息处理人", middleware.BusinessInsert), h.messageDisposeSave)
	auth.PUT("/flow/messagedispose",
		middleware.OperLog(reg.App, "系统消息处理人", middleware.BusinessUpdate), h.messageDisposeSave)
	auth.DELETE("/flow/messagedispose/:ids",
		middleware.OperLog(reg.App, "系统消息处理人", middleware.BusinessDelete), h.messageDisposeDelete)
	auth.DELETE("/flow/messagedispose/delmes/:mid", h.messageDisposeRemoveMine)
	auth.DELETE("/flow/messagedispose/szzdmes/:mid", h.messageDisposeReadMine)

	// ---------------------------------------------------------------- 系统内部消息
	auth.GET("/flow/messageinfo/list", h.messageInfoList)
	auth.GET("/flow/messageinfo/listyb", h.messageInfoListYb)
	auth.GET("/flow/messageinfo/listyj", h.messageInfoListYj)
	auth.GET("/flow/messageinfo/listxx", h.messageInfoListXx)
	auth.GET("/flow/messageinfo/export",
		middleware.OperLog(reg.App, "系统内部消息", middleware.BusinessExport), h.messageInfoExport)
	// Java 把 exportShrz 写在 /{id} 之后；Go 侧静态段优先，放前放后都能命中，这里按静态优先排列。
	auth.GET("/flow/messageinfo/exportShrz",
		middleware.OperLog(reg.App, "导出审核日志", middleware.BusinessExport), h.messageInfoExportShrz)
	auth.GET("/flow/messageinfo/:id", h.messageInfoGet)
	auth.DELETE("/flow/messageinfo/:ids",
		middleware.OperLog(reg.App, "系统内部消息", middleware.BusinessDelete), h.messageInfoDelete)
	// DIFF: Java 的 add / edit 被整段块注释，故不注册 POST "" 与 PUT ""。

	// ---------------------------------------------------------------- 流程名称
	auth.GET("/flow/flowname/list", middleware.Perm("flow:flowname:list"), h.flowNameList)
	auth.GET("/flow/flowname/listQuery", h.flowNameListQuery)
	auth.GET("/flow/flowname/export", middleware.Perm("flow:flowname:export"),
		middleware.OperLog(reg.App, "流程名称", middleware.BusinessExport), h.flowNameExport)
	auth.GET("/flow/flowname/:id", middleware.Perm("flow:flowname:query"), h.flowNameGet)
	auth.POST("/flow/flowname", middleware.Perm("flow:flowname:add"),
		middleware.OperLog(reg.App, "流程名称", middleware.BusinessInsert), h.flowNameSave)
	auth.PUT("/flow/flowname", middleware.Perm("flow:flowname:edit"),
		middleware.OperLog(reg.App, "流程名称", middleware.BusinessUpdate), h.flowNameSave)
	auth.DELETE("/flow/flowname/:ids", middleware.Perm("flow:flowname:remove"),
		middleware.OperLog(reg.App, "流程名称", middleware.BusinessDelete), h.flowNameDelete)
	auth.POST("/flow/flowname/tbFlow", middleware.Perm("flow:flowname:edit"),
		middleware.OperLog(reg.App, "同步其他单位的工作流", middleware.BusinessUpdate), h.flowNameTbFlow)

	// ---------------------------------------------------------------- 流程节点
	auth.GET("/flow/flowtemplate/list", h.templateList)
	auth.GET("/flow/flowtemplate/flowlist", h.templateFlowList)
	auth.GET("/flow/flowtemplate/export",
		middleware.OperLog(reg.App, "流程节点", middleware.BusinessExport), h.templateExport)
	auth.GET("/flow/flowtemplate/:id", h.templateGet)
	auth.POST("/flow/flowtemplate",
		middleware.OperLog(reg.App, "流程节点", middleware.BusinessInsert), h.templateSave)
	auth.PUT("/flow/flowtemplate",
		middleware.OperLog(reg.App, "流程节点", middleware.BusinessUpdate), h.templateSave)
	auth.DELETE("/flow/flowtemplate/:ids",
		middleware.OperLog(reg.App, "流程节点", middleware.BusinessDelete), h.templateDelete)
}
