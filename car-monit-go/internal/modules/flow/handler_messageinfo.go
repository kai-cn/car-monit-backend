// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowMessageInfoController.java
// 类/职责: /flow/messageinfo/** 全部 HTTP 入口（系统内部消息）
// 对应 Go 文件: internal/modules/flow/handler_messageinfo.go
//
// Java 里 add / edit 被整段块注释掉了，因此这里不注册 POST "" 与 PUT ""。
package flow

import (
	"net/http"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// messageInfoListWithFlag 是四个列表接口共用的三步：startPage -> setFlag -> setUserId。
func (h *handler) messageInfoListWithFlag(c *gin.Context, flag string) {
	var q MessageInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectMessageInfoList(c.Request.Context(), h.svc.db, q, flag, actorFrom(c).UserID, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// messageInfoList 对应 list（我的待办）。
func (h *handler) messageInfoList(c *gin.Context) { h.messageInfoListWithFlag(c, flagMyDb) }

// messageInfoListYb 对应 listyb（我的已办）。
func (h *handler) messageInfoListYb(c *gin.Context) { h.messageInfoListWithFlag(c, flagMyYb) }

// messageInfoListYj 对应 listyj（我的已结）。
func (h *handler) messageInfoListYj(c *gin.Context) { h.messageInfoListWithFlag(c, flagMyYj) }

// messageInfoListXx 对应 listxx（我的消息）。
func (h *handler) messageInfoListXx(c *gin.Context) { h.messageInfoListWithFlag(c, flagMyXx) }

// messageInfoExport 对应 export：不设 flag / userId，也不分页。
func (h *handler) messageInfoExport(c *gin.Context) {
	var q MessageInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.selectMessageInfoAll(c.Request.Context(), h.svc.db, q)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, messageInfoExportRow(row))
	}
	filename, err := h.writeExcel("系统内部消息数据", messageInfoExportCols(), data)
	respondExcel(c, filename, err)
}

// messageInfoExportShrz 对应 exportShrz：按消息导出对应的审核日志。
//
// DIFF: Java 用 easypoi 模板 templates/export/exportShrz.xlsx；Go 侧模板文件不存在，
// 用 excelize 生成等价版面（标题 / 申请人 / 明细表）。
// JAVA 对照: 查不到消息时 Java 直接 NPE，GlobalExceptionHandler 返回 code 500 + msg = null。
func (h *handler) messageInfoExportShrz(c *gin.Context) {
	var q MessageInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	msg, err := h.svc.selectMessageInfoByID(c.Request.Context(), h.svc.db, strVal(q.ID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg == nil {
		web.JSON(c, web.ErrorResult(web.NewNilMessageError()))
		return
	}

	history, err := h.svc.selectFlowListAll(c.Request.Context(), h.svc.db, FlowListQuery{BillOid: msg.BillOid})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// Java: fl.setSort(i+1) —— 从 1 开始
	for i := range history {
		history[i].Sort = i64Ptr(int64(i + 1))
	}

	data, err := buildShrzWorkbook(orEmpty(msg.ApplyName), formatDateOnly(msg.CreateTime), orEmpty(msg.MsgTitle), history)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	c.Header("Content-Type", "application/octet-stream;charset=UTF-8")
	// Java: response.setHeader("Content-Disposition", "attachment") —— 没有 filename
	c.Header("Content-Disposition", "attachment")
	c.Data(http.StatusOK, "application/octet-stream", data)
}

// messageInfoGet 对应 getInfo。
func (h *handler) messageInfoGet(c *gin.Context) {
	row, err := h.svc.selectMessageInfoByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// messageInfoDelete 对应 remove。
func (h *handler) messageInfoDelete(c *gin.Context) {
	count, err := h.svc.deleteMessageInfoByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}
