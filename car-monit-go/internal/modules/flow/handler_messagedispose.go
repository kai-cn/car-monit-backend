// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageDisposeController.java
// 类/职责: /flow/messagedispose/** 全部 HTTP 入口（消息处理人）
// 对应 Go 文件: internal/modules/flow/handler_messagedispose.go
//
// /delmes/{mid} 与 /szzdmes/{mid} 的第二个参数是控制器自己算出的当前用户 ID，
// 同一个消息对不同人操作，落库范围不同。
package flow

import (
	"strconv"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// messageDisposeList 对应 list。
func (h *handler) messageDisposeList(c *gin.Context) {
	var q MessageDisposeQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectMessageDisposeList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// messageDisposeExport 对应 export。
func (h *handler) messageDisposeExport(c *gin.Context) {
	var q MessageDisposeQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, _, err := h.svc.selectMessageDisposeList(c.Request.Context(), h.svc.db, q, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, messageDisposeExportRow(row))
	}
	filename, err := h.writeExcel("系统消息处理人数据", messageDisposeExportCols(), data)
	respondExcel(c, filename, err)
}

// messageDisposeGet 对应 getInfo。
func (h *handler) messageDisposeGet(c *gin.Context) {
	row, err := h.svc.selectMessageDisposeByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// messageDisposeSave 对应 add / edit。
func (h *handler) messageDisposeSave(c *gin.Context) {
	var body FlowMessageDispose
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveMessageDisposeRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// messageDisposeDelete 对应 remove。
func (h *handler) messageDisposeDelete(c *gin.Context) {
	count, err := h.svc.deleteMessageDisposeByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// messageDisposeRemoveMine 对应 delmes/{mid}：物理删除自己的处理记录。
func (h *handler) messageDisposeRemoveMine(c *gin.Context) {
	bussID := strconv.FormatInt(actorFrom(c).UserID, 10)
	count, err := h.svc.removeFlowMessage(c.Request.Context(), h.svc.db, c.Param("mid"), bussID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}

// messageDisposeReadMine 对应 szzdmes/{mid}：把自己的那条置为已办理。
func (h *handler) messageDisposeReadMine(c *gin.Context) {
	bussID := strconv.FormatInt(actorFrom(c).UserID, 10)
	count, err := h.svc.saveSzzdFlowMessage(c.Request.Context(), h.svc.db, c.Param("mid"), bussID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}
