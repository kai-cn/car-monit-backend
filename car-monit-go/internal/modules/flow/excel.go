// JAVA 对照: com/ruoyi/common/utils/poi/ExcelUtil.java（@Excel 字段导出）
// 类/职责: flow 模块 7 张表的 Excel 导出
// 对应 Go 文件: internal/modules/flow/excel.go
//
// DIFF: Java 用 POI 逐单元格写样式；Go 用 excelize，只保证表头文案、列顺序与取值一致。
// DIFF: 文件写入 ruoyi.profile/download，返回 AjaxResult(msg=文件名)，与 ExcelUtil 一致。
// DIFF: @Excel(readConverterExp=...) 在本工程里都是非法表达式（缺少逗号分隔），
// 因此这里输出原始值，不做字典/表达式翻译。
package flow

import (
	"os"
	"path/filepath"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/xuri/excelize/v2"

	"car-monit-go/internal/web"
)

// exportCol 描述导出的一列（表头 + 取值函数）。
type exportCol struct {
	title string
	value func(row reflectRow) any
}

// reflectRow 是各实体在导出时的通用视图（由各实体自己构造 map）。
type reflectRow map[string]any

func strCell(v *string) any {
	if v == nil {
		return ""
	}
	return *v
}

func intCell(v *int64) any {
	if v == nil {
		return ""
	}
	return *v
}

func timeCell(v *web.DateTime) any {
	if v == nil || v.IsZero() {
		return ""
	}
	return v.String()
}

// JAVA 对照: ExcelUtil.exportExcel(list, sheetName) / encodingFilename / getAbsoluteFile
// writeExcel 生成 xlsx 并写入 download 目录，返回文件名（对应 ExcelUtil.exportExcel）。
func (h *handler) writeExcel(sheetName string, cols []exportCol, rows []reflectRow) (string, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()
	if err := f.SetSheetName("Sheet1", sheetName); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	header := make([]any, len(cols))
	for i, col := range cols {
		header[i] = col.title
	}
	if err := f.SetSheetRow(sheetName, "A1", &header); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	for i, row := range rows {
		cell, err := excelize.CoordinatesToCellName(1, i+2)
		if err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		values := make([]any, len(cols))
		for j, col := range cols {
			values[j] = col.value(row)
		}
		if err := f.SetSheetRow(sheetName, cell, &values); err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
	}
	for i := range cols {
		name, err := excelize.ColumnNumberToName(i + 1)
		if err != nil {
			return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		_ = f.SetColWidth(sheetName, name, name, 20)
	}

	filename := uuid.NewString() + "_" + sheetName + ".xlsx"
	path := h.app.Cfg.RuoYi.DownloadPath() + filename
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	if err := f.SaveAs(path); err != nil {
		return "", web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return filename, nil
}

// respondExcel 对应 AjaxResult.success(filename)：文件名放在 msg，无 data。
func respondExcel(c *gin.Context, filename string, err error) {
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// applyInfoExportCols 对应 FlowApplyInfo 上的 @Excel 字段。
func applyInfoExportCols() []exportCol {
	return []exportCol{
		{"单据OID", func(r reflectRow) any { return r["billOid"] }},
		{"业务类型-字典", func(r reflectRow) any { return r["bussType"] }},
		{"流程实例ID", func(r reflectRow) any { return r["flowRuid"] }},
		{"标题", func(r reflectRow) any { return r["msgTitle"] }},
		{"内容", func(r reflectRow) any { return r["msgContext"] }},
		{"消息类型(1:通知业务，2:办理业务)", func(r reflectRow) any { return r["msgType"] }},
		{"处理的URL", func(r reflectRow) any { return r["msgUrl"] }},
		{"申请人", func(r reflectRow) any { return r["applyName"] }},
		{"当前节点OID(流程节点OID)", func(r reflectRow) any { return r["currentOid"] }},
		{"批次OID", func(r reflectRow) any { return r["pcOid"] }},
		{"备用字段1", func(r reflectRow) any { return r["backCol1"] }},
		{"备用字段2", func(r reflectRow) any { return r["backCol2"] }},
		{"备用字段3", func(r reflectRow) any { return r["backCol3"] }},
		{"流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)", func(r reflectRow) any { return r["flowStatus"] }},
	}
}

func applyInfoExportRow(e FlowApplyInfo) reflectRow {
	return reflectRow{
		"billOid": strCell(e.BillOid), "bussType": strCell(e.BussType), "flowRuid": strCell(e.FlowRuid),
		"msgTitle": strCell(e.MsgTitle), "msgContext": strCell(e.MsgContext), "msgType": strCell(e.MsgType),
		"msgUrl": strCell(e.MsgUrl), "applyName": strCell(e.ApplyName), "currentOid": strCell(e.CurrentOid),
		"pcOid": strCell(e.PcOid), "backCol1": strCell(e.BackCol1), "backCol2": strCell(e.BackCol2),
		"backCol3": strCell(e.BackCol3), "flowStatus": strCell(e.FlowStatus),
	}
}

func currentNodeExportCols() []exportCol {
	return []exportCol{
		{"流程OID", func(r reflectRow) any { return r["flowOid"] }},
		{"当前节点OID(流程节点OID)", func(r reflectRow) any { return r["currentOid"] }},
		{"节点顺序", func(r reflectRow) any { return r["nodeOrder"] }},
		{"节点KEY", func(r reflectRow) any { return r["nodeKey"] }},
		{"节点名称", func(r reflectRow) any { return r["nodeName"] }},
		{"当前流程类型(字典：1人员2角色3其他)", func(r reflectRow) any { return r["configType"] }},
		{"节点配置id", func(r reflectRow) any { return r["configId"] }},
		{"节点配置名称", func(r reflectRow) any { return r["configName"] }},
		{"单据OID", func(r reflectRow) any { return r["billOid"] }},
		{"处理人ID", func(r reflectRow) any { return r["auitEmpOid"] }},
		{"处理人名称", func(r reflectRow) any { return r["auitEmpName"] }},
		{"备用字段1", func(r reflectRow) any { return r["backCol1"] }},
		{"备用字段2", func(r reflectRow) any { return r["backCol2"] }},
		{"备用字段3", func(r reflectRow) any { return r["backCol3"] }},
		{"流程key", func(r reflectRow) any { return r["flowKey"] }},
		{"流程实例ID", func(r reflectRow) any { return r["flowRuid"] }},
		{"流程申请ID", func(r reflectRow) any { return r["flowApplyOid"] }},
		{"流程状态(1起草中2审批中3审批通过4退回修改5审批拒绝)", func(r reflectRow) any { return r["flowStatus"] }},
	}
}

func currentNodeExportRow(e FlowCurrentNode) reflectRow {
	return reflectRow{
		"flowOid": strCell(e.FlowOid), "currentOid": strCell(e.CurrentOid), "nodeOrder": intCell(e.NodeOrder),
		"nodeKey": strCell(e.NodeKey), "nodeName": strCell(e.NodeName), "configType": strCell(e.ConfigType),
		"configId": strCell(e.ConfigId), "configName": strCell(e.ConfigName), "billOid": strCell(e.BillOid),
		"auitEmpOid": strCell(e.AuitEmpOid), "auitEmpName": strCell(e.AuitEmpName),
		"backCol1": strCell(e.BackCol1), "backCol2": strCell(e.BackCol2), "backCol3": strCell(e.BackCol3),
		"flowKey": strCell(e.FlowKey), "flowRuid": strCell(e.FlowRuid),
		"flowApplyOid": strCell(e.FlowApplyOid), "flowStatus": strCell(e.FlowStatus),
	}
}

func flowListExportCols() []exportCol {
	return []exportCol{
		{"单据OID", func(r reflectRow) any { return r["billOid"] }},
		{"流程类型", func(r reflectRow) any { return r["bussType"] }},
		{"任务ID", func(r reflectRow) any { return r["taskId"] }},
		{"流程实例ID", func(r reflectRow) any { return r["flowRuid"] }},
		{"当前节点OID(流程节点OID)", func(r reflectRow) any { return r["currentOid"] }},
		{"审核人", func(r reflectRow) any { return r["shUser"] }},
		{"审核结论KEY", func(r reflectRow) any { return r["shKey"] }},
		{"审核结论", func(r reflectRow) any { return r["shValue"] }},
		{"内容", func(r reflectRow) any { return r["shContext"] }},
		{"备用字段1", func(r reflectRow) any { return r["backCol1"] }},
		{"备用字段2", func(r reflectRow) any { return r["backCol2"] }},
		{"备用字段3", func(r reflectRow) any { return r["backCol3"] }},
	}
}

func flowListExportRow(e FlowList) reflectRow {
	return reflectRow{
		"billOid": strCell(e.BillOid), "bussType": strCell(e.BussType), "taskId": strCell(e.TaskId),
		"flowRuid": strCell(e.FlowRuid), "currentOid": strCell(e.CurrentOid), "shUser": strCell(e.ShUser),
		"shKey": strCell(e.ShKey), "shValue": strCell(e.ShValue), "shContext": strCell(e.ShContext),
		"backCol1": strCell(e.BackCol1), "backCol2": strCell(e.BackCol2), "backCol3": strCell(e.BackCol3),
	}
}

func messageDisposeExportCols() []exportCol {
	return []exportCol{
		{"消息外键", func(r reflectRow) any { return r["mid"] }},
		{"处理对象ID", func(r reflectRow) any { return r["bussId"] }},
		{"处理对象名称", func(r reflectRow) any { return r["bussName"] }},
		{"消息状态", func(r reflectRow) any { return r["msgStatus"] }},
		{"处理时间", func(r reflectRow) any { return r["hangTime"] }},
		{"其他", func(r reflectRow) any { return r["disposeOther"] }},
	}
}

func messageDisposeExportRow(e FlowMessageDispose) reflectRow {
	return reflectRow{
		"mid": strCell(e.Mid), "bussId": strCell(e.BussId), "bussName": strCell(e.BussName),
		"msgStatus": strCell(e.MsgStatus), "hangTime": timeCell(e.HangTime), "disposeOther": strCell(e.DisposeOther),
	}
}

func messageInfoExportCols() []exportCol {
	return []exportCol{
		{"单据OID", func(r reflectRow) any { return r["billOid"] }},
		{"业务类型-字典", func(r reflectRow) any { return r["bussType"] }},
		{"流程实例ID", func(r reflectRow) any { return r["flowRuid"] }},
		{"标题", func(r reflectRow) any { return r["msgTitle"] }},
		{"内容", func(r reflectRow) any { return r["msgContext"] }},
		{"消息类型(1:通知业务，2:办理业务)", func(r reflectRow) any { return r["msgType"] }},
		{"处理的URL", func(r reflectRow) any { return r["msgUrl"] }},
		{"批次OID", func(r reflectRow) any { return r["pcOid"] }},
		{"申请人", func(r reflectRow) any { return r["applyName"] }},
		{"备用字段1", func(r reflectRow) any { return r["backCol1"] }},
		{"备用字段2", func(r reflectRow) any { return r["backCol2"] }},
		{"备用字段3", func(r reflectRow) any { return r["backCol3"] }},
	}
}

func messageInfoExportRow(e FlowMessageInfo) reflectRow {
	return reflectRow{
		"billOid": strCell(e.BillOid), "bussType": strCell(e.BussType), "flowRuid": strCell(e.FlowRuid),
		"msgTitle": strCell(e.MsgTitle), "msgContext": strCell(e.MsgContext), "msgType": strCell(e.MsgType),
		"msgUrl": strCell(e.MsgUrl), "pcOid": strCell(e.PcOid), "applyName": strCell(e.ApplyName),
		"backCol1": strCell(e.BackCol1), "backCol2": strCell(e.BackCol2), "backCol3": strCell(e.BackCol3),
	}
}

func flowNameExportCols() []exportCol {
	return []exportCol{
		{"流程KEY", func(r reflectRow) any { return r["flowKey"] }},
		{"流程名称", func(r reflectRow) any { return r["flowTitle"] }},
		{"内容", func(r reflectRow) any { return r["flowContext"] }},
		{"业务名称", func(r reflectRow) any { return r["bussName"] }},
		{"单位名称", func(r reflectRow) any { return r["tenantName"] }},
	}
}

func flowNameExportRow(e FlowName) reflectRow {
	return reflectRow{
		"flowKey": strCell(e.FlowKey), "flowTitle": strCell(e.FlowTitle), "flowContext": strCell(e.FlowContext),
		"bussName": strCell(e.BussName), "tenantName": strCell(e.TenantName),
	}
}

func flowTemplateExportCols() []exportCol {
	return []exportCol{
		{"流程OID", func(r reflectRow) any { return r["flowOid"] }},
		{"当前流程类型(字典：1正常流程2会签流程)", func(r reflectRow) any { return r["flowType"] }},
		{"节点顺序", func(r reflectRow) any { return r["nodeOrder"] }},
		{"节点KEY", func(r reflectRow) any { return r["nodeKey"] }},
		{"节点名称", func(r reflectRow) any { return r["nodeName"] }},
		{"下一节点OID(-1为当前为最后一个节点)", func(r reflectRow) any { return r["nextNodeOid"] }},
		{"上一节点OID(0为开始节点)", func(r reflectRow) any { return r["previousNodeOid"] }},
		{"驳回到第几步 0 是发起人", func(r reflectRow) any { return r["returnNum"] }},
		{"驳回节点OID", func(r reflectRow) any { return r["returnNodeOid"] }},
		{"节点配置条件", func(r reflectRow) any { return r["configCondtion"] }},
		{"当前流程类型(字典：1人员2角色3其他)", func(r reflectRow) any { return r["configType"] }},
		{"节点配置id", func(r reflectRow) any { return r["configId"] }},
		{"节点配置名称", func(r reflectRow) any { return r["configName"] }},
	}
}

func flowTemplateExportRow(e FlowTemplate) reflectRow {
	return reflectRow{
		"flowOid": strCell(e.FlowOid), "flowType": strCell(e.FlowType), "nodeOrder": intCell(e.NodeOrder),
		"nodeKey": strCell(e.NodeKey), "nodeName": strCell(e.NodeName), "nextNodeOid": strCell(e.NextNodeOid),
		"previousNodeOid": strCell(e.PreviousNodeOid), "returnNum": intCell(e.ReturnNum),
		"returnNodeOid": strCell(e.ReturnNodeOid), "configCondtion": strCell(e.ConfigCondtion),
		"configType": strCell(e.ConfigType), "configId": strCell(e.ConfigId), "configName": strCell(e.ConfigName),
	}
}

// buildShrzWorkbook 近似 EasyPOI 模板 templates/export/exportShrz.xlsx 的版面。
//
// DIFF: 原模板文件不在 Go 侧，这里用 excelize 直接生成等价结构：
//
//	第 1 行：消息标题
//	第 2 行：申请人 / 申请时间
//	第 3 行：明细表头（序号 / 审核人 / 审核结论 / 内容 / 时间）
//	第 4 行起：审核历史
func buildShrzWorkbook(applyName, createTime, msgTitle string, rows []FlowList) ([]byte, error) {
	f := excelize.NewFile()
	defer func() { _ = f.Close() }()
	const sheet = "审核日志"
	if err := f.SetSheetName("Sheet1", sheet); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	_ = f.SetCellValue(sheet, "A1", msgTitle)
	_ = f.SetCellValue(sheet, "A2", "申请人："+applyName)
	_ = f.SetCellValue(sheet, "C2", "申请时间："+createTime)
	header := []any{"序号", "审核人", "审核结论", "内容", "时间"}
	if err := f.SetSheetRow(sheet, "A3", &header); err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	for i, row := range rows {
		cell, err := excelize.CoordinatesToCellName(1, i+4)
		if err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
		values := []any{
			i + 1,
			strCell(row.ShUser),
			strCell(row.ShValue),
			strCell(row.ShContext),
			strCellFromTime(row.CreateTime),
		}
		if err := f.SetSheetRow(sheet, cell, &values); err != nil {
			return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
		}
	}
	buf, err := f.WriteToBuffer()
	if err != nil {
		return nil, web.NewServiceError("导出Excel失败，请联系网站管理员！")
	}
	return buf.Bytes(), nil
}

// strCellFromTime 把可选时间格式化成 yyyy-MM-dd HH:mm:ss。
func strCellFromTime(t *web.DateTime) string {
	if t == nil || t.IsZero() {
		return ""
	}
	return t.Format("2006-01-02 15:04:05")
}

// formatDateOnly 对应 DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD, date)。
func formatDateOnly(t *web.DateTime) string {
	if t == nil || t.IsZero() {
		return ""
	}
	return t.Format("2006-01-02")
}
