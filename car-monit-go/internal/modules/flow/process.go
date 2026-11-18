// JAVA 对照: com/ruoyi/flow/service/impl/FlowCurrentNodeServiceImpl.java
// JAVA 对照: com/ruoyi/flow/service/impl/FlowApplyInfoServiceImpl.java（saveFlowApplyInfoNew）
// JAVA 对照: com/ruoyi/flow/service/impl/FlowListServiceImpl.java（saveFlowList）
// 类/职责: 审批流核心 —— 提交 / 审核 / 撤销 / 委托，以及节点审批人解析
// 对应 Go 文件: internal/modules/flow/process.go
//
// 状态机（FlowTypeEnum）：1 起草中 / 2 审批中 / 3 审批通过 / 4 退回修改 / 5 审批拒绝。
// shValue 前端传数字：1 -> T 同意，2 -> F 拒绝（flowStatus=5），3 -> R 退回。
//
// DIFF: Java 的 @Transactional 由 Spring 代理；Go 显式 db.Transaction 包裹整段。
// DIFF: Java 里找不到主数据会 NPE（HTTP 500），这里统一返回 "系统异常"，落点一致。
package flow

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"strconv"
	"strings"
	"time"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

// FlowTypeEnum 的 code（getCode()）。
const (
	flowStatusSubmit  = "1" // 起草中
	flowStatusApprove = "2" // 审批中
	flowStatusEnd     = "3" // 审批通过
	flowStatusReturn  = "4" // 退回修改
	flowStatusStop    = "5" // 审批拒绝
)

// Constants 中与流程相关的常量。
const (
	flowResultEntrustKey    = "entrust"
	flowResultContextPrefix = "委托"
	flowResultContextSuffix = "办理"
	flowEntrustName         = "委托"

	roleDeptManager = "dept_manager"
	roleFgManager   = "fg_manager"
	roleDeptDutyEmp = "dept_duty_emp"
)

// 审核结论字母码 -> 中文（saveFlowList）。
var flowResultLabels = map[string]string{
	"S":                  "提交",
	"T":                  "同意",
	"F":                  "拒绝",
	"R":                  "退回",
	flowResultEntrustKey: flowEntrustName,
}

// selectRoleKey 对应 SysRoleMapper.selectRoleById(...).getRoleKey()。
func (s *Service) selectRoleKey(ctx context.Context, db *gorm.DB, roleID int64) (string, error) {
	var roleKey string
	err := db.WithContext(ctx).Raw("select r.role_key from sys_role r where r.role_id = ?", roleID).Row().Scan(&roleKey)
	if errors.Is(err, sql.ErrNoRows) {
		// 空结果：Java 的 selectRoleById 返回 null，这里按"角色不存在"处理。
		return "", nil
	}
	if err != nil {
		return "", err
	}
	return roleKey, nil
}

// getEmpInfoList 对应 getEmpInfoList：按节点配置找人（人员 / 角色 / 部门领导 / 分管领导 / 值班人）。
func (s *Service) getEmpInfoList(ctx context.Context, db *gorm.DB, a actor, tableName string,
	tpl *FlowTemplate, billOid string) ([]FlowCurrentNode, error) {
	result := make([]FlowCurrentNode, 0)
	configType := ptrTrim(tpl.ConfigType)
	configID := ptrTrim(tpl.ConfigId)

	if configID == "" {
		return result, nil
	}
	if configType == "1" {
		// 1 人员
		result = append(result, FlowCurrentNode{AuitEmpOid: strPtr(configID), AuitEmpName: tpl.ConfigName})
		return result, nil
	}

	// 角色
	q := &FlowCurrentNode{RoleId: strPtr(configID), BillOid: strPtr(billOid)}
	// Java 用未 trim 的 configId 调 Long.parseLong
	roleID, err := strconv.ParseInt(orEmpty(tpl.ConfigId), 10, 64)
	if err != nil {
		return nil, web.NewServiceError("系统异常")
	}
	roleKey, err := s.selectRoleKey(ctx, db, roleID)
	if err != nil {
		return nil, err
	}
	if roleKey == "" {
		return result, nil
	}
	userID := strconv.FormatInt(a.UserID, 10)
	switch roleKey {
	case roleDeptManager:
		// 部门领导审核：根据部门设置
		q.Flag = strPtr("bmjlAudit")
		q.RoleId = strPtr("")
		q.TenantID = nil
		q.BackCol1 = strPtr(userID)
	case roleFgManager:
		// 分管领导审核
		q.Flag = strPtr("fgldAudit")
		q.RoleId = strPtr("")
		q.TenantID = nil
		q.BackCol1 = strPtr(userID)
	case roleDeptDutyEmp:
		// 科室值班人审核：找到归属部门的
		q.Flag = strPtr("dutyAudit")
		q.TenantID = nil
		q.BackCol1 = strPtr(tableName)
	}
	return s.selectEmpInfoList(ctx, db, q)
}

// getEmpInfoListReturn 对应 getEmpInfoListReturn：退回时的审批人取自审核历史。
func (s *Service) getEmpInfoListReturn(ctx context.Context, db *gorm.DB, tpl *FlowTemplate, billOid string) ([]FlowCurrentNode, error) {
	result := make([]FlowCurrentNode, 0)
	rows, err := s.selectFlowListListNew(ctx, db, FlowListQuery{BillOid: strPtr(billOid), CurrentOid: tpl.ID})
	if err != nil {
		return nil, err
	}
	if len(rows) > 0 {
		result = append(result, FlowCurrentNode{
			AuitEmpOid:  strPtr(strconv.FormatInt(i64Val(rows[0].CreateBy), 10)),
			AuitEmpName: rows[0].ShUser,
		})
	}
	return result, nil
}

// saveFlowNode 对应 saveFlowNode：把"节点模板 × 审批人"展开成 N 条当前节点记录。
func (s *Service) saveFlowNode(ctx context.Context, db *gorm.DB, a actor, tpl *FlowTemplate,
	empList []FlowCurrentNode, billOid, projectID string) error {
	for i := range empList {
		node := &FlowCurrentNode{
			BillOid:     strPtr(billOid),
			FlowOid:     tpl.FlowOid,
			CurrentOid:  tpl.ID,
			NodeOrder:   tpl.NodeOrder,
			NodeKey:     tpl.NodeKey,
			NodeName:    tpl.NodeName,
			ConfigType:  tpl.ConfigType,
			ConfigId:    tpl.ConfigId,
			ConfigName:  tpl.ConfigName,
			AuitEmpOid:  empList[i].AuitEmpOid,
			AuitEmpName: empList[i].AuitEmpName,
			BackCol1:    strPtr(projectID), // 项目权限字段
		}
		if _, err := s.saveCurrentNodeRow(ctx, db, a, node); err != nil {
			return err
		}
	}
	return nil
}

// saveFlowHistory 对应 saveFlowList(template, ...)：插一条审核历史。
func (s *Service) saveFlowHistory(ctx context.Context, db *gorm.DB, a actor, tpl *FlowTemplate,
	billOid, flowKey, auitResult, auitContext string) error {
	row := &FlowList{
		BillOid:    strPtr(billOid),
		BussType:   strPtr(flowKey),
		FlowRuid:   tpl.FlowOid,
		CurrentOid: tpl.ID,
		ShUser:     strPtr(a.RealName),
		ShKey:      strPtr(auitResult),
		ShContext:  strPtr(auitContext),
	}
	if label, ok := flowResultLabels[auitResult]; ok {
		row.ShValue = strPtr(label)
	}
	_, err := s.saveFlowListRow(ctx, db, a, row)
	return err
}

// saveFlowListRow 对应 saveFlowList（新增/修改 + 审计字段）。
func (s *Service) saveFlowListRow(ctx context.Context, db *gorm.DB, a actor, e *FlowList) (*web.AjaxResult, error) {
	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateFlowList(ctx, db, e); err != nil {
			return nil, err
		}
	} else {
		e.ID = strPtr(newUUID())
		e.DelFlag = strPtr("0")
		e.EpsID = i64Ptr(a.EpsID)
		e.CreateBy = i64Ptr(a.UserID)
		e.CreateTime = nowDateTime()
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.insertFlowList(ctx, db, e); err != nil {
			return nil, err
		}
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// saveApplyInfoRow 对应 saveFlowApplyInfo（新增/修改 + 审计字段）。
func (s *Service) saveApplyInfoRow(ctx context.Context, db *gorm.DB, a actor, e *FlowApplyInfo) (*web.AjaxResult, error) {
	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateApplyInfo(ctx, db, e); err != nil {
			return nil, err
		}
	} else {
		e.ID = strPtr(newUUID())
		e.DelFlag = strPtr("0")
		e.EpsID = i64Ptr(a.EpsID)
		e.CreateBy = i64Ptr(a.UserID)
		e.CreateTime = nowDateTime()
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.insertApplyInfo(ctx, db, e); err != nil {
			return nil, err
		}
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// saveApplyInfoNew 对应 saveFlowApplyInfoNew：按 billOid upsert，返回主键。
func (s *Service) saveApplyInfoNew(ctx context.Context, db *gorm.DB, a actor, e *FlowApplyInfo) (string, error) {
	exist, _, err := s.selectApplyInfoList(ctx, db, ApplyInfoQuery{BillOid: e.BillOid}, web.PageDomain{})
	if err != nil {
		return "", err
	}
	if len(exist) > 0 {
		e.ID = exist[0].ID
	}
	if _, err := s.saveApplyInfoRow(ctx, db, a, e); err != nil {
		return "", err
	}
	return strVal(e.ID), nil
}

// saveCurrentNodeRow 对应 saveFlowCurrentNode（新增/修改 + 审计字段）。
func (s *Service) saveCurrentNodeRow(ctx context.Context, db *gorm.DB, a actor, e *FlowCurrentNode) (*web.AjaxResult, error) {
	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateCurrentNode(ctx, db, e); err != nil {
			return nil, err
		}
	} else {
		e.ID = strPtr(newUUID())
		e.DelFlag = strPtr("0")
		e.EpsID = i64Ptr(a.EpsID)
		e.CreateBy = i64Ptr(a.UserID)
		e.CreateTime = nowDateTime()
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.insertCurrentNode(ctx, db, e); err != nil {
			return nil, err
		}
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// SaveFlowApply 对应 Java IFlowCurrentNodeService#saveFlowApply：提交业务申请。
//
// 业务模块通过 flow.NewService 构造服务后调用；flow 包内没有对应的 HTTP 入口
// （与 Java 控制器保持一致），因此这里是跨模块公开 API，不能按死代码删除。
func (s *Service) SaveFlowApply(ctx context.Context, a actor, flowKey, billOid, projectID, bussTitle string) (*web.AjaxResult, error) {
	var res *web.AjaxResult
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		r, err := s.doFlowApply(ctx, tx, a, flowKey, billOid, projectID, bussTitle)
		if err != nil {
			return err
		}
		res = r
		return nil
	})
	if err != nil {
		return nil, err
	}
	return res, nil
}

func (s *Service) doFlowApply(ctx context.Context, db *gorm.DB, a actor, flowKey, billOid, projectID, bussTitle string) (*web.AjaxResult, error) {
	// 根据流程 flowKey 查询流程节点 id
	flowNameList, err := s.selectFlowNameAll(ctx, db, FlowNameQuery{FlowKey: strPtr(flowKey)})
	if err != nil {
		return nil, err
	}
	if len(flowNameList) == 0 {
		return web.ErrorMsg("流程不存在，请与管理员联系！"), nil
	}
	flowName := flowNameList[0]

	// 根据流程查找第一个节点
	tplList, err := s.selectTemplateAll(ctx, db, FlowTemplateQuery{FlowOid: flowName.ID, PreviousNodeOid: strPtr("0")})
	if err != nil {
		return nil, err
	}
	if len(tplList) == 0 {
		return web.ErrorMsg("节点不存在，请与管理员联系！"), nil
	}
	tpl := tplList[0]

	// 根据节点查询审核人
	empList, err := s.getEmpInfoList(ctx, db, a, orEmpty(flowName.BussName), &tpl, billOid)
	if err != nil {
		return nil, err
	}
	if len(empList) == 0 {
		return web.ErrorMsg("该业务找不到下一审批人，请与管理员联系！"), nil
	}

	auitNames := ""
	useIDs := make([]string, 0, len(empList))
	for i := range empList {
		useIDs = append(useIDs, orEmpty(empList[i].AuitEmpOid))
		auitNames += orEmpty(empList[i].AuitEmpName) + ","
	}
	auitNames = strings.TrimSuffix(auitNames, ",")

	flowStatus := flowStatusApprove
	flowRuid := strVal(flowName.ID)
	bussTypeName := orEmpty(flowName.FlowTitle)
	tableName := orEmpty(flowName.BussName)

	// 提交的业务名称
	if strings.TrimSpace(bussTitle) == "" {
		bussTitle = bussTypeName
	}

	msgTitle1 := "【" + bussTypeName + "】你提交关于" + bussTitle + "的申请！"
	msgTitle2 := "【" + bussTypeName + "】" + a.RealName + "提交关于" + bussTitle + "的申请！"

	// 我的申请插入一条记录
	applyInfo := &FlowApplyInfo{
		BillOid:    strPtr(billOid),
		BussType:   strPtr(flowKey),
		FlowRuid:   strPtr(flowRuid),
		MsgType:    strPtr("1"),
		FlowStatus: strPtr(flowStatus),
		ApplyName:  strPtr(a.RealName),
		MsgTitle:   strPtr(msgTitle1),
		BackCol1:   strPtr(auitNames), // 当前处理人
	}
	flowApplyOid, err := s.saveApplyInfoNew(ctx, db, a, applyInfo)
	if err != nil {
		return nil, err
	}

	// 插入下一个节点
	if err := s.saveFlowNode(ctx, db, a, &tpl, empList, billOid, projectID); err != nil {
		return nil, err
	}

	// 发送消息主体
	messageInfo := &FlowMessageInfo{
		BillOid:   strPtr(billOid),
		BussType:  strPtr(flowKey),
		FlowRuid:  strPtr(flowRuid),
		MsgType:   strPtr("2"),
		ApplyName: strPtr(a.RealName),
		MsgTitle:  strPtr(msgTitle2),
	}
	mid, err := s.saveMessageInfoRow(ctx, db, a, messageInfo)
	if err != nil {
		return nil, err
	}
	// 发送消息明细
	if err := s.saveFlowDisposeList(ctx, db, a, mid, useIDs); err != nil {
		return nil, err
	}

	// 插入审核历史记录
	if err := s.saveFlowHistory(ctx, db, a, &tpl, billOid, flowKey, "S", ""); err != nil {
		return nil, err
	}

	// 反该业务状态
	if err := s.updateFlowTable(ctx, db, &FlowCurrentNode{
		TableName:    strPtr(tableName),
		BillOid:      strPtr(billOid),
		FlowKey:      strPtr(flowKey),
		FlowRuid:     strPtr(flowRuid),
		FlowApplyOid: strPtr(flowApplyOid),
		FlowStatus:   strPtr(flowStatus),
	}); err != nil {
		return nil, err
	}

	return web.SuccessMsg("流程提交成功！"), nil
}

// saveFlowAuit 对应 saveFlowAuit：业务审核（同意 / 拒绝 / 退回）。
func (s *Service) saveFlowAuit(ctx context.Context, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	var res *web.AjaxResult
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		r, err := s.doFlowAuit(ctx, tx, a, in)
		if err != nil {
			return err
		}
		res = r
		return nil
	})
	if err != nil {
		return nil, err
	}
	return res, nil
}

func (s *Service) doFlowAuit(ctx context.Context, db *gorm.DB, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	shValue := orEmpty(in.ShValue)
	billOid := orEmpty(in.BillOid)
	projectID := ""
	flowStatus := flowStatusApprove

	if in.ShValue != nil {
		switch shValue {
		case "1":
			shValue = "T"
		case "2":
			shValue = "F"
			flowStatus = flowStatusStop
		case "3":
			shValue = "R"
		}
	}
	if shValue == "" {
		return web.ErrorMsg("请填写审核结论！"), nil
	}
	if billOid == "" {
		return web.ErrorMsg("业务不存在！"), nil
	}

	// 获取当前节点
	currentList, err := s.selectCurrentNodeAll(ctx, db, CurrentNodeQuery{
		BillOid:    strPtr(billOid),
		AuitEmpOid: strPtr(strconv.FormatInt(a.UserID, 10)),
	})
	if err != nil {
		return nil, err
	}
	if len(currentList) == 0 {
		return web.ErrorMsg("对不起，该单据已审核，请确定！"), nil
	}
	newCurrent := currentList[0]
	if orEmpty(newCurrent.BackCol1) != "" {
		projectID = orEmpty(newCurrent.BackCol1)
	}

	curTemplate, err := s.selectTemplateByID(ctx, db, orEmpty(newCurrent.CurrentOid))
	if err != nil {
		return nil, err
	}
	if curTemplate == nil {
		return nil, web.NewServiceError("系统异常")
	}
	nextNodeOid := orEmpty(curTemplate.NextNodeOid)
	// 注意：Java 实际生效的是"上一节点"，注释里的 returnNodeOid 被留在原地。
	returnNodeOid := orEmpty(curTemplate.PreviousNodeOid)

	flowName, err := s.selectFlowNameByID(ctx, db, orEmpty(curTemplate.FlowOid))
	if err != nil {
		return nil, err
	}
	if flowName == nil {
		return nil, web.NewServiceError("系统异常")
	}

	nextTemplate := &FlowTemplate{}
	empList := make([]FlowCurrentNode, 0)

	if nextNodeOid != "-1" && shValue == "T" {
		nextTemplate, err = s.selectTemplateByID(ctx, db, nextNodeOid)
		if err != nil {
			return nil, err
		}
		if nextTemplate == nil || strVal(nextTemplate.ID) == "" {
			return web.ErrorMsg("下一个节点不存在，请与管理员联系！"), nil
		}
		empList, err = s.getEmpInfoList(ctx, db, a, orEmpty(flowName.BussName), nextTemplate, billOid)
		if err != nil {
			return nil, err
		}
		if len(empList) == 0 {
			return web.ErrorMsg("该业务找不到下一审批人，请与管理员联系！"), nil
		}
	} else if returnNodeOid != "0" && shValue == "R" {
		nextTemplate, err = s.selectTemplateByID(ctx, db, returnNodeOid)
		if err != nil {
			return nil, err
		}
		if nextTemplate == nil || strVal(nextTemplate.ID) == "" {
			return web.ErrorMsg("退回节点不存在，请与管理员联系！"), nil
		}
		empList, err = s.getEmpInfoListReturn(ctx, db, nextTemplate, billOid)
		if err != nil {
			return nil, err
		}
		if len(empList) == 0 {
			return web.ErrorMsg("该业务找不到下一审批人，请与管理员联系！"), nil
		}
	}

	auitNames := ""
	useIDs := make([]string, 0, len(empList))
	for i := range empList {
		useIDs = append(useIDs, orEmpty(empList[i].AuitEmpOid))
		auitNames += orEmpty(empList[i].AuitEmpName) + ","
	}
	auitNames = strings.TrimSuffix(auitNames, ",")

	// 审核通过 / 退回
	if nextNodeOid == "-1" && shValue == "T" {
		flowStatus = flowStatusEnd
	}
	if returnNodeOid == "0" && shValue == "R" {
		flowStatus = flowStatusReturn
	}

	bussTypeName := orEmpty(flowName.FlowTitle)
	tableName := orEmpty(flowName.BussName)
	flowKey := orEmpty(flowName.FlowKey)
	flowRuid := strVal(flowName.ID)

	// 先删当前节点（物理删）
	if _, err := s.deleteCurrentNodeByBillID(ctx, db, billOid); err != nil {
		return nil, err
	}

	// 修改消息主体
	mid, err := s.saveMessageInfoRow(ctx, db, a, &FlowMessageInfo{BillOid: strPtr(billOid), MsgType: strPtr("2")})
	if err != nil {
		return nil, err
	}
	// 消息的待办全部设置为自己
	if _, err := s.saveSzzdFlowMessageAll(ctx, db, mid, strconv.FormatInt(a.UserID, 10)); err != nil {
		return nil, err
	}

	// 修改我的申请
	flowApplyOid, err := s.saveApplyInfoNew(ctx, db, a, &FlowApplyInfo{
		BillOid:    strPtr(billOid),
		FlowStatus: strPtr(flowStatus),
		BackCol1:   strPtr(auitNames),
	})
	if err != nil {
		return nil, err
	}

	// 申请人ID
	applyInfo, err := s.selectApplyInfoByID(ctx, db, flowApplyOid)
	if err != nil {
		return nil, err
	}
	if applyInfo == nil {
		return nil, web.NewServiceError("系统异常")
	}
	applyID := i64Val(applyInfo.CreateBy)

	// 修改业务状态
	if err := s.updateFlowTable(ctx, db, &FlowCurrentNode{
		TableName:  strPtr(tableName),
		BillOid:    strPtr(billOid),
		FlowStatus: strPtr(flowStatus),
	}); err != nil {
		return nil, err
	}

	// 插入审核意见
	if err := s.saveFlowHistory(ctx, db, a, curTemplate, billOid, flowKey, shValue, orEmpty(in.ShContext)); err != nil {
		return nil, err
	}

	// 插入下一个节点
	if err := s.saveFlowNode(ctx, db, a, nextTemplate, empList, billOid, projectID); err != nil {
		return nil, err
	}
	// 发送消息明细
	if err := s.saveFlowDisposeList(ctx, db, a, mid, useIDs); err != nil {
		return nil, err
	}

	// 业务反馈区域
	msgTitle1 := ""
	switch flowStatus {
	case flowStatusEnd:
		msgTitle1 = "你提交的" + bussTypeName + "业务已通过，请查看！"
	case flowStatusStop:
		msgTitle1 = "你提交的" + bussTypeName + "业务已拒绝，请查看！"
	case flowStatusReturn:
		msgTitle1 = "你提交的" + bussTypeName + "业务已退回，请查看！"
	}

	// 流程结束回调：Java 里业务实现已被注释掉（专家申请 / 设备申请 / 资源申请），这里保留空分支。

	// 发送消息给申请人
	if msgTitle1 != "" {
		grmid, err := s.saveMessageInfoRow(ctx, db, a, &FlowMessageInfo{
			BillOid:  strPtr(billOid),
			BussType: strPtr(flowKey),
			FlowRuid: strPtr(flowRuid),
			MsgType:  strPtr("1"),
			MsgTitle: strPtr(msgTitle1),
		})
		if err != nil {
			return nil, err
		}
		if err := s.saveFlowDisposeList(ctx, db, a, grmid, []string{strconv.FormatInt(applyID, 10)}); err != nil {
			return nil, err
		}
	}

	return web.SuccessMsg("审核成功！"), nil
}

// submitReturn 对应 submitReturn：撤销流程（仅当前节点是首节点时允许）。
func (s *Service) submitReturn(ctx context.Context, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	var res *web.AjaxResult
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		r, err := s.doSubmitReturn(ctx, tx, a, in)
		if err != nil {
			return err
		}
		res = r
		return nil
	})
	if err != nil {
		return nil, err
	}
	return res, nil
}

func (s *Service) doSubmitReturn(ctx context.Context, db *gorm.DB, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	billOid := orEmpty(in.BillOid)
	if billOid == "" {
		return web.ErrorMsg("业务不存在！"), nil
	}

	currentList, err := s.selectCurrentNodeAll(ctx, db, CurrentNodeQuery{BillOid: strPtr(billOid)})
	if err != nil {
		return nil, err
	}
	if len(currentList) == 0 {
		return web.ErrorMsg("撤销失败，该单据已撤销，请确定！"), nil
	}
	newCurrent := currentList[0]

	curTemplate, err := s.selectTemplateByID(ctx, db, orEmpty(newCurrent.CurrentOid))
	if err != nil {
		return nil, err
	}
	if curTemplate == nil {
		return nil, web.NewServiceError("系统异常")
	}
	previousNodeOid := orEmpty(curTemplate.PreviousNodeOid)
	if previousNodeOid != "0" {
		return web.ErrorMsg("撤销失败，该单据已审核，请确定！"), nil
	}

	flowName, err := s.selectFlowNameByID(ctx, db, orEmpty(curTemplate.FlowOid))
	if err != nil {
		return nil, err
	}
	if flowName == nil {
		return nil, web.NewServiceError("系统异常")
	}

	// 删除当前节点数据（物理删）
	if _, err := s.deleteCurrentNodeByBillID(ctx, db, billOid); err != nil {
		return nil, err
	}

	// 修改消息
	msgList, err := s.selectMessageInfoAll(ctx, db, MessageInfoQuery{BillOid: strPtr(billOid), MsgType: strPtr("2")})
	if err != nil {
		return nil, err
	}
	if len(msgList) > 0 {
		mid := strVal(msgList[0].ID)
		if _, err := s.deleteMessageInfoByIDs(ctx, db, []string{mid}); err != nil {
			return nil, err
		}
		// 消息的待办物理删（Java 传空 bussId -> 不带处理人条件）
		if _, err := s.removeFlowMessage(ctx, db, mid, ""); err != nil {
			return nil, err
		}
	}

	// 删除我的申请：Java 传的是请求体里的 flowCurrentNode.id（通常为 null -> 0 行）
	if _, err := s.deleteApplyInfoByID(ctx, db, strVal(in.ID)); err != nil {
		return nil, err
	}

	// 单据状态修改成草稿
	if err := s.updateFlowTable(ctx, db, &FlowCurrentNode{
		TableName:  flowName.BussName,
		BillOid:    strPtr(billOid),
		FlowStatus: strPtr(flowStatusSubmit),
	}); err != nil {
		return nil, err
	}

	return web.SuccessMsg("撤销成功！"), nil
}

// submitEntrustFlow 对应 submitEntrustFlow：委托他人办理。
func (s *Service) submitEntrustFlow(ctx context.Context, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	var res *web.AjaxResult
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		r, err := s.doSubmitEntrustFlow(ctx, tx, a, in)
		if err != nil {
			return err
		}
		res = r
		return nil
	})
	if err != nil {
		return nil, err
	}
	return res, nil
}

func (s *Service) doSubmitEntrustFlow(ctx context.Context, db *gorm.DB, a actor, in *FlowCurrentNode) (*web.AjaxResult, error) {
	if strings.TrimSpace(orEmpty(in.EntrustUserId)) == "" ||
		strings.TrimSpace(orEmpty(in.EntrustUserName)) == "" ||
		strings.TrimSpace(orEmpty(in.BillOid)) == "" {
		return web.ErrorMsg("缺少参数!"), nil
	}
	billOid := orEmpty(in.BillOid)
	userID := strconv.FormatInt(a.UserID, 10)

	// 流程结果(委托)
	flowResult := flowResultEntrustKey
	flowResultContext := flowResultContextPrefix + orEmpty(in.EntrustUserName) + flowResultContextSuffix

	// 获取当前流程节点
	currentList, err := s.selectCurrentNodeAll(ctx, db, CurrentNodeQuery{BillOid: strPtr(billOid), AuitEmpOid: strPtr(userID)})
	if err != nil {
		return nil, err
	}
	if len(currentList) == 0 {
		return web.ErrorMsg("当前流程节点不存在!"), nil
	}
	currentNode := currentList[0]

	tpl, err := s.selectTemplateByID(ctx, db, orEmpty(currentNode.CurrentOid))
	if err != nil {
		return nil, err
	}
	if tpl == nil {
		return web.ErrorMsg("找不到对应的流程节点模板信息!"), nil
	}
	flowName, err := s.selectFlowNameByID(ctx, db, orEmpty(tpl.FlowOid))
	if err != nil {
		return nil, err
	}
	if flowName == nil {
		return web.ErrorMsg("找不到对应的流程信息!"), nil
	}
	applyInfo, err := s.selectApplyInfoByBillID(ctx, db, billOid)
	if err != nil {
		return nil, err
	}
	if applyInfo == nil {
		return web.ErrorMsg("找不到对应的流程申请信息!"), nil
	}

	// 更新当前流程节点数据
	currentNode.AuitEmpOid = in.EntrustUserId
	currentNode.AuitEmpName = in.EntrustUserName
	currentNode.BackCol2 = strPtr(userID)     // 委托之前的审核人id
	currentNode.BackCol3 = strPtr(a.RealName) // 委托之前的审核人名称
	if _, err := s.saveCurrentNodeRow(ctx, db, a, &currentNode); err != nil {
		return nil, err
	}

	// 保存流程委托信息
	if err := s.saveFlowHistory(ctx, db, a, tpl, billOid, orEmpty(flowName.FlowKey), flowResult, flowResultContext); err != nil {
		return nil, err
	}

	// 将流程信息设置为已办理
	messageInfoID, err := s.saveMessageInfoRow(ctx, db, a, &FlowMessageInfo{BillOid: strPtr(billOid), MsgType: strPtr("2")})
	if err != nil {
		return nil, err
	}
	if _, err := s.saveSzzdFlowMessageAll(ctx, db, messageInfoID, userID); err != nil {
		return nil, err
	}
	// 发送消息给委派的人员
	if err := s.saveFlowDisposeList(ctx, db, a, messageInfoID, []string{orEmpty(in.EntrustUserId)}); err != nil {
		return nil, err
	}

	// 保存委派的信息记录
	entrustInfo := EntrustInfo{
		OperatorUserId:   strPtr(userID),
		OperatorUserName: strPtr(a.RealName),
		EntrustUserId:    in.EntrustUserId,
		EntrustUserName:  in.EntrustUserName,
		// DIFF: Java @JSONField(format="yyyy-MM-dd HH:mm:ss.SS")，这里按毫秒位数格式化。
		OperationTime:  strPtr(time.Now().Format("2006-01-02 15:04:05.000")),
		FlowId:         flowName.ID,
		FlowKey:        flowName.FlowKey,
		FlowTemplateId: tpl.ID,
	}

	updateBo := &FlowApplyInfo{
		BaseUUID: BaseUUID{ID: applyInfo.ID},
		BackCol1: in.EntrustUserName,
	}
	raw := orEmpty(applyInfo.EntrustInfo)
	if strings.TrimSpace(raw) != "" {
		list := make([]EntrustInfo, 0)
		if err := json.Unmarshal([]byte(raw), &list); err != nil {
			// fastjson2 对非法 JSON 抛 JSONException -> HTTP 500
			return nil, web.NewServiceError("系统异常")
		}
		list = append(list, entrustInfo)
		data, err := json.Marshal(list)
		if err != nil {
			return nil, err
		}
		updateBo.EntrustInfo = strPtr(string(data))
	} else {
		data, err := json.Marshal([]EntrustInfo{entrustInfo})
		if err != nil {
			return nil, err
		}
		updateBo.EntrustInfo = strPtr(string(data))
	}

	if _, err := s.saveApplyInfoRow(ctx, db, a, updateBo); err != nil {
		return nil, err
	}

	return web.Success(), nil
}
