// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow/FlowApplyInfoController.java
// 类/职责: /flow/applyinfo/** 全部 HTTP 入口（我的申请）
// 对应 Go 文件: internal/modules/flow/handler_applyinfo.go
package flow

import (
	"github.com/gin-gonic/gin"

	"car-monit-go/internal/web"
)

// applyInfoList 对应 list：只看自己创建的（控制器里强写 createBy = 当前用户）。
func (h *handler) applyInfoList(c *gin.Context) {
	var q ApplyInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	a := actorFrom(c)
	q.CreateBy = i64Ptr(a.UserID) // 查询我的申请
	rows, total, err := h.svc.selectApplyInfoList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// applyInfoListAll 对应 listAll（唯一带 @PreAuthorize 的方法）。
func (h *handler) applyInfoListAll(c *gin.Context) {
	var q ApplyInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, total, err := h.svc.selectApplyInfoList(c.Request.Context(), h.svc.db, q, web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// applyInfoExport 对应 export：不分页、不限制 createBy（导"按条件能查到的全部"）。
func (h *handler) applyInfoExport(c *gin.Context) {
	var q ApplyInfoQuery
	if err := bindQuery(c, &q); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, _, err := h.svc.selectApplyInfoList(c.Request.Context(), h.svc.db, q, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	data := make([]reflectRow, 0, len(rows))
	for _, row := range rows {
		data = append(data, applyInfoExportRow(row))
	}
	filename, err := h.writeExcel("我的申请数据", applyInfoExportCols(), data)
	respondExcel(c, filename, err)
}

// applyInfoGet 对应 getInfo。
func (h *handler) applyInfoGet(c *gin.Context) {
	row, err := h.svc.selectApplyInfoByID(c.Request.Context(), h.svc.db, c.Param("id"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(row))
}

// applyInfoSave 对应 add / edit（id 非空即修改）。
func (h *handler) applyInfoSave(c *gin.Context) {
	var body FlowApplyInfo
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	res, err := h.svc.saveApplyInfoRow(c.Request.Context(), h.svc.db, actorFrom(c), &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, res)
}

// applyInfoDelete 对应 remove。
func (h *handler) applyInfoDelete(c *gin.Context) {
	count, err := h.svc.deleteApplyInfoByIDs(c.Request.Context(), h.svc.db, splitIDs(c.Param("ids")))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(count))
}
