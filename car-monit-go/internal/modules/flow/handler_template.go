// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowTemplateController.java
// 类/职责: /flow/flowtemplate/** 全部 HTTP 入口（流程节点）
// 对应 Go 文件: internal/modules/flow/handler_template.go
//
// remove 的已知怪癖（照抄）：先逻辑删、再按 ids[0] 查（详情不带 del_flag）取 flowOid 重算链路。
package flow

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// templateList 对应 list。
func (h *handler) templateList(c *gin.Context) {
	var q FlowTemplateQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectTemplateList(c.Request.Context(), h.svc.db, q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// templateFlowList 对应 flowlist：flowOid 为空返回空数组，否则 [虚拟"申请人提交"节点] + 真实节点。
func (h *handler) templateFlowList(c *gin.Context) {
	var q FlowTemplateQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	result := make([]FlowTemplate, 0)
	if ptrTrim(q.FlowOid) != "" {
		result = append(result, FlowTemplate{
			BaseUUID:  BaseUUID{ID: strPtr("-1")},
			NodeOrder: i64Ptr(-1),
			NodeKey:   strPtr("tj"),
			NodeName:  strPtr("申请人提交"),
		})
		rows, err := h.svc.selectTemplateAll(c.Request.Context(), h.svc.db, q)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		result = append(result, rows...)
	}
	web.JSON(c, web.SuccessData(result))
}

// templateExport 对应 export。
func (h *handler) templateExport(c *gin.Context) {
	var q FlowTemplateQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.selectTemplateAll(c.Request.Context(), h.svc.db, q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, flowTemplateExportRow(row))
	}
	filename, err := h.writeExcel("流程节点数据", flowTemplateExportCols(), data)
	respondExcel(c, filename, err)
}

// templateGet 对应 getInfo。
func (h *handler) templateGet(c *gin.Context) {
	row, err := h.svc.selectTemplateByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// templateSave 对应 add / edit（service 侧查 key / 顺序是否重复）。
func (h *handler) templateSave(c *gin.Context) {
	var body FlowTemplate
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveTemplateRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// templateDelete 对应 remove：先删、后查（依赖逻辑删才成立）。
func (h *handler) templateDelete(c *gin.Context) {
	ids := splitIDs(c.Param("ids"))
	if len(ids) == 0 {
		web.JSON(c, web.ErrorMsg("系统异常"))
		return
	}
	count, err := h.svc.deleteTemplateByIDs(c.Request.Context(), h.svc.db, ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	row, err := h.svc.selectTemplateByID(c.Request.Context(), h.svc.db, ids[0])
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if row == nil {
		// Java: selectFlowTemplateById(ids[0]).getFlowOid() -> NPE
		web.JSON(c, web.ErrorMsg("系统异常"))
		return
	}
	if err := h.svc.saveFlowOrder(c.Request.Context(), h.svc.db, orEmpty(row.FlowOid)); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}
