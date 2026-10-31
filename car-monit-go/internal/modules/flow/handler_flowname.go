// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowNameController.java
// 类/职责: /flow/flowname/** 全部 HTTP 入口（流程名称）
// 对应 Go 文件: internal/modules/flow/handler_flowname.go
//
// 这是 flow 包里唯一逐个方法都挂 @PreAuthorize 的控制器。
package flow

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// flowNameList 对应 list（管理员视角，不过滤租户）。
func (h *handler) flowNameList(c *gin.Context) {
	var q FlowNameQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectFlowNameList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// flowNameListQuery 对应 listQuery（单位只看自己的流程，无权限点）。
func (h *handler) flowNameListQuery(c *gin.Context) {
	var q FlowNameQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	a := actorFrom(c)
	q.TenantID = i64Ptr(a.TenantID) // 查询单位自己的流程
	rows, total, err := h.svc.selectFlowNameList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// flowNameExport 对应 export。
func (h *handler) flowNameExport(c *gin.Context) {
	var q FlowNameQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.selectFlowNameAll(c.Request.Context(), h.svc.db, q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, flowNameExportRow(row))
	}
	filename, err := h.writeExcel("流程名称数据", flowNameExportCols(), data)
	respondExcel(c, filename, err)
}

// flowNameGet 对应 getInfo。
func (h *handler) flowNameGet(c *gin.Context) {
	row, err := h.svc.selectFlowNameByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// flowNameSave 对应 add / edit（service 侧先查节点 key 是否重复）。
func (h *handler) flowNameSave(c *gin.Context) {
	var body FlowName
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveFlowNameRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// flowNameDelete 对应 remove。
func (h *handler) flowNameDelete(c *gin.Context) {
	count, err := h.svc.deleteFlowNameByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// flowNameTbFlow 对应 tbFlow（同步其他单位的工作流）。
func (h *handler) flowNameTbFlow(c *gin.Context) {
	res, err := h.svc.tbFlow(c.Request.Context(), actorFrom(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}
