// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowListController.java
// 类/职责: /flow/flowlist/** 全部 HTTP 入口（审核历史）
// 对应 Go 文件: internal/modules/flow/handler_flowlist.go
//
// listnew 的语义：先按 billOid 查审核历史（升序），再按 flow_apply_info 的状态
// 在末尾补一条"待审批 / 流程结束"的虚拟记录；不分页。
package flow

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// flowListList 对应 list。
func (h *handler) flowListList(c *gin.Context) {
	var q FlowListQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectFlowListList(c.Request.Context(), h.svc.db, q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// flowListNew 对应 listnew：历史 + 当前状态尾巴。
func (h *handler) flowListNew(c *gin.Context) {
	var q FlowListQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if orEmpty(q.BillOid) == "" {
		q.BillOid = strPtr("-1")
	}

	rows, err := h.svc.selectFlowListAll(c.Request.Context(), h.svc.db, q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	// 获取我的申请记录
	applyList, _, err := h.svc.selectApplyInfoList(c.Request.Context(), h.svc.db,
		ApplyInfoQuery{BillOid: q.BillOid}, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(applyList) > 0 {
		status := isNull(orEmpty(applyList[0].FlowStatus))
		auitEmpName := isNull(orEmpty(applyList[0].BackCol1))
		switch status {
		case flowStatusApprove:
			// 当前审核人（空了就不补）
			if auitEmpName != "" {
				rows = append(rows, FlowList{ShUser: strPtr(auitEmpName), ShValue: strPtr("待审批")})
			}
		case flowStatusEnd:
			rows = append(rows, FlowList{ShValue: strPtr("流程结束")})
		}
	}

	web.JSON(c, web.SuccessData(rows))
}

// flowListExport 对应 export（无 startPage，导全量）。
func (h *handler) flowListExport(c *gin.Context) {
	var q FlowListQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, _, err := h.svc.selectFlowListList(c.Request.Context(), h.svc.db, q, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, flowListExportRow(row))
	}
	filename, err := h.writeExcel("审核历史记录数据", flowListExportCols(), data)
	respondExcel(c, filename, err)
}

// flowListGet 对应 getInfo。
func (h *handler) flowListGet(c *gin.Context) {
	row, err := h.svc.selectFlowListByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// flowListSave 对应 add / edit。
func (h *handler) flowListSave(c *gin.Context) {
	var body FlowList
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveFlowListRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// flowListDelete 对应 remove。
func (h *handler) flowListDelete(c *gin.Context) {
	count, err := h.svc.deleteFlowListByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}
