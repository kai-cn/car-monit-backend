// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowCurrentNodeController.java
// 类/职责: /flow/currentnode/** 全部 HTTP 入口（当前节点 / 审核 / 撤销 / 委托）
// 对应 Go 文件: internal/modules/flow/handler_currentnode.go
//
// 本控制器在 Java 里一个 @PreAuthorize 都没有（全是注释行），这里保持不放。
package flow

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// currentNodeList 对应 list。
func (h *handler) currentNodeList(c *gin.Context) {
	var q CurrentNodeQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectCurrentNodeList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// currentNodeExport 对应 export（无 startPage，导全量）。
func (h *handler) currentNodeExport(c *gin.Context) {
	var q CurrentNodeQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, _, err := h.svc.selectCurrentNodeList(c.Request.Context(), h.svc.db, q, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, currentNodeExportRow(row))
	}
	filename, err := h.writeExcel("流程_当前节点数据", currentNodeExportCols(), data)
	respondExcel(c, filename, err)
}

// currentNodeGetByBillID 对应 getInfoByBillId：查不到时回显查询条件本身（不是 null）。
func (h *handler) currentNodeGetByBillID(c *gin.Context) {
	billOid := c.Param("billOid")
	probe := &FlowCurrentNode{BillOid: strPtr(billOid)}
	rows, err := h.svc.selectCurrentNodeAll(c.Request.Context(), h.svc.db, CurrentNodeQuery{BillOid: strPtr(billOid)})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(rows) > 0 {
		probe = &rows[0]
	}
	web.JSON(c, web.SuccessData(probe))
}

// currentNodeGet 对应 getInfo。
func (h *handler) currentNodeGet(c *gin.Context) {
	row, err := h.svc.selectCurrentNodeByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// currentNodeSave 对应 add / edit。
func (h *handler) currentNodeSave(c *gin.Context) {
	var body FlowCurrentNode
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveCurrentNodeRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// currentNodeDelete 对应 remove。
func (h *handler) currentNodeDelete(c *gin.Context) {
	count, err := h.svc.deleteCurrentNodeByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// currentNodeAudit 对应 saveFlowAuit（流程审核）。
func (h *handler) currentNodeAudit(c *gin.Context) {
	var body FlowCurrentNode
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveFlowAuit(c.Request.Context(), actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// currentNodeSubmitReturn 对应 submitReturn（撤销流程）。
func (h *handler) currentNodeSubmitReturn(c *gin.Context) {
	var body FlowCurrentNode
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.submitReturn(c.Request.Context(), actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// currentNodeSubmitEntrust 对应 submitEntrustFlow（委托-办理流程）。
func (h *handler) currentNodeSubmitEntrust(c *gin.Context) {
	var body FlowCurrentNode
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.submitEntrustFlow(c.Request.Context(), actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}
