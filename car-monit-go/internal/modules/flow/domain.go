// JAVA 对照: com/ruoyi/common/core/domain/BaseUuidEntity.java
// JAVA 对照: com/ruoyi/flow/domain/FlowApplyInfo.java
// JAVA 对照: com/ruoyi/flow/domain/FlowCurrentNode.java
// JAVA 对照: com/ruoyi/flow/domain/FlowList.java
// JAVA 对照: com/ruoyi/flow/domain/FlowMessageDispose.java
// JAVA 对照: com/ruoyi/flow/domain/FlowMessageInfo.java
// JAVA 对照: com/ruoyi/flow/domain/FlowName.java
// JAVA 对照: com/ruoyi/flow/domain/FlowTemplate.java
// JAVA 对照: com/ruoyi/flow/domain/EntrustInfo.java
// 类/职责: flow 模块领域模型（JSON 字段与 Java 实体逐一对应）
// 对应 Go 文件: internal/modules/flow/domain.go
//
// DIFF: Java 的 Long/Integer/Timestamp/String 均可为 null，Jackson 默认输出 null；
// Go 用指针字段保留 null 语义（例如 /flow/applyinfo/listAll 不能把 create_by=0 当成条件）。
// DIFF: FlowMessageDispose.hangTime 的 Java @JsonFormat(pattern="flow_message_dispose") 是无效格式，
// 这里按项目统一约定输出 "yyyy-MM-dd HH:mm:ss"。
package flow

import "car-monit-go/internal/web"

// BaseUUID 对应 BaseUuidEntity（UUID 主键实体基类）。
type BaseUUID struct {
	ID          *string        `json:"id" gorm:"column:ID"`
	EpsID       *int64         `json:"epsId" gorm:"column:eps_id"`
	DelFlag     *string        `json:"delFlag" gorm:"column:del_flag"`
	CreateBy    *int64         `json:"createBy" gorm:"column:create_by"`
	CreateTime  *web.DateTime  `json:"createTime" gorm:"column:create_time"`
	UpdateBy    *int64         `json:"updateBy" gorm:"column:update_by"`
	UpdateTime  *web.DateTime  `json:"updateTime" gorm:"column:update_time"`
	Sort        *int64         `json:"sort" gorm:"column:sort"`
	Remark      *string        `json:"remark" gorm:"column:remark"`
	TenantID    *int64         `json:"tenantId" gorm:"column:tenant_id"`
	DeptSubCode *string        `json:"deptSubCode" gorm:"column:dept_sub_code"`
	Flag        *string        `json:"flag" gorm:"-"`
	SearchValue *string        `json:"searchValue" gorm:"-"`
	Params      map[string]any `json:"params" gorm:"-"`
}

// FlowApplyInfo 对应 flow_apply_info。
type FlowApplyInfo struct {
	BaseUUID
	BillOid     *string `json:"billOid" gorm:"column:BILL_OID"`
	BussType    *string `json:"bussType" gorm:"column:BUSS_TYPE"`
	FlowRuid    *string `json:"flowRuid" gorm:"column:FLOW_RUID"`
	MsgTitle    *string `json:"msgTitle" gorm:"column:MSG_TITLE"`
	MsgContext  *string `json:"msgContext" gorm:"column:MSG_CONTEXT"`
	MsgType     *string `json:"msgType" gorm:"column:MSG_TYPE"`
	MsgUrl      *string `json:"msgUrl" gorm:"column:MSG_URL"`
	ApplyName   *string `json:"applyName" gorm:"column:APPLY_NAME"`
	CurrentOid  *string `json:"currentOid" gorm:"column:CURRENT_OID"`
	PcOid       *string `json:"pcOid" gorm:"column:PC_OID"`
	BackCol1    *string `json:"backCol1" gorm:"column:BACK_COL1"`
	BackCol2    *string `json:"backCol2" gorm:"column:BACK_COL2"`
	BackCol3    *string `json:"backCol3" gorm:"column:BACK_COL3"`
	FlowStatus  *string `json:"flowStatus" gorm:"column:FLOW_STATUS"`
	AuitEmpName *string `json:"auitEmpName" gorm:"column:auit_emp_name"`
	EntrustInfo *string `json:"entrustInfo" gorm:"column:entrust_info"`
}

// FlowCurrentNode 对应 flow_current_node。
type FlowCurrentNode struct {
	BaseUUID
	FlowOid         *string `json:"flowOid" gorm:"column:FLOW_OID"`
	CurrentOid      *string `json:"currentOid" gorm:"column:CURRENT_OID"`
	NodeOrder       *int64  `json:"nodeOrder" gorm:"column:NODE_ORDER"`
	NodeKey         *string `json:"nodeKey" gorm:"column:NODE_KEY"`
	NodeName        *string `json:"nodeName" gorm:"column:NODE_NAME"`
	ConfigType      *string `json:"configType" gorm:"column:CONFIG_TYPE"`
	ConfigId        *string `json:"configId" gorm:"column:CONFIG_ID"`
	ConfigName      *string `json:"configName" gorm:"column:CONFIG_NAME"`
	BillOid         *string `json:"billOid" gorm:"column:BILL_OID"`
	AuitEmpOid      *string `json:"auitEmpOid" gorm:"column:AUIT_EMP_OID"`
	AuitEmpName     *string `json:"auitEmpName" gorm:"column:AUIT_EMP_NAME"`
	BackCol1        *string `json:"backCol1" gorm:"column:BACK_COL1"`
	BackCol2        *string `json:"backCol2" gorm:"column:BACK_COL2"`
	BackCol3        *string `json:"backCol3" gorm:"column:BACK_COL3"`
	RoleId          *string `json:"roleId" gorm:"-"`
	TableName       *string `json:"tableName" gorm:"-"`
	ProjectId       *string `json:"projectId" gorm:"-"`
	FlowKey         *string `json:"flowKey" gorm:"-"`
	FlowRuid        *string `json:"flowRuid" gorm:"-"`
	FlowApplyOid    *string `json:"flowApplyOid" gorm:"-"`
	FlowStatus      *string `json:"flowStatus" gorm:"-"`
	ShValue         *string `json:"shValue" gorm:"-"`
	ShContext       *string `json:"shContext" gorm:"-"`
	EntrustUserId   *string `json:"entrustUserId" gorm:"-"`
	EntrustUserName *string `json:"entrustUserName" gorm:"-"`
	RoleKey         *string `json:"roleKey" gorm:"-"`
	DeptID          *int64  `json:"deptId" gorm:"-"`
}

// FlowList 对应 flow_list。
type FlowList struct {
	BaseUUID
	BillOid    *string `json:"billOid" gorm:"column:BILL_OID"`
	BussType   *string `json:"bussType" gorm:"column:BUSS_TYPE"`
	TaskId     *string `json:"taskId" gorm:"column:TASK_ID"`
	FlowRuid   *string `json:"flowRuid" gorm:"column:flow_ruid"`
	CurrentOid *string `json:"currentOid" gorm:"column:CURRENT_OID"`
	ShUser     *string `json:"shUser" gorm:"column:SH_USER"`
	ShKey      *string `json:"shKey" gorm:"column:SH_KEY"`
	ShValue    *string `json:"shValue" gorm:"column:SH_VALUE"`
	ShContext  *string `json:"shContext" gorm:"column:SH_CONTEXT"`
	BackCol1   *string `json:"backCol1" gorm:"column:BACK_COL1"`
	BackCol2   *string `json:"backCol2" gorm:"column:BACK_COL2"`
	BackCol3   *string `json:"backCol3" gorm:"column:BACK_COL3"`
}

// FlowMessageDispose 对应 flow_message_dispose。
type FlowMessageDispose struct {
	BaseUUID
	Mid          *string       `json:"mid" gorm:"column:MID"`
	BussId       *string       `json:"bussId" gorm:"column:BUSS_ID"`
	BussName     *string       `json:"bussName" gorm:"column:BUSS_NAME"`
	MsgStatus    *string       `json:"msgStatus" gorm:"column:MSG_STATUS"`
	HangTime     *web.DateTime `json:"hangTime" gorm:"column:HANG_TIME"`
	DisposeOther *string       `json:"disposeOther" gorm:"column:DISPOSE_OTHER"`
}

// FlowMessageInfo 对应 flow_message_info。
type FlowMessageInfo struct {
	BaseUUID
	MessageNo   *string              `json:"messageNo" gorm:"column:message_no"`
	BillOid     *string              `json:"billOid" gorm:"column:BILL_OID"`
	BussType    *string              `json:"bussType" gorm:"column:BUSS_TYPE"`
	FlowRuid    *string              `json:"flowRuid" gorm:"column:FLOW_RUID"`
	MsgTitle    *string              `json:"msgTitle" gorm:"column:MSG_TITLE"`
	MsgContext  *string              `json:"msgContext" gorm:"column:MSG_CONTEXT"`
	MsgType     *string              `json:"msgType" gorm:"column:MSG_TYPE"`
	MsgUrl      *string              `json:"msgUrl" gorm:"column:MSG_URL"`
	PcOid       *string              `json:"pcOid" gorm:"column:PC_OID"`
	ApplyName   *string              `json:"applyName" gorm:"column:APPLY_NAME"`
	BackCol1    *string              `json:"backCol1" gorm:"column:BACK_COL1"`
	BackCol2    *string              `json:"backCol2" gorm:"column:BACK_COL2"`
	BackCol3    *string              `json:"backCol3" gorm:"column:BACK_COL3"`
	UserID      *int64               `json:"userId" gorm:"-"`
	MsgStatus   *string              `json:"msgStatus" gorm:"column:msg_status"`
	FlowStatus  *string              `json:"flowStatus" gorm:"column:flow_status"`
	CurEmpNames *string              `json:"curEmpNames" gorm:"column:cur_emp_names"`
	DisposeList []FlowMessageDispose `json:"disposeList" gorm:"-"`
}

// FlowName 对应 flow_name。
type FlowName struct {
	BaseUUID
	FlowKey          *string `json:"flowKey" gorm:"column:FLOW_KEY"`
	FlowTitle        *string `json:"flowTitle" gorm:"column:FLOW_TITLE"`
	FlowContext      *string `json:"flowContext" gorm:"column:FLOW_CONTEXT"`
	BussName         *string `json:"bussName" gorm:"column:BUSS_NAME"`
	TenantName       *string `json:"tenantName" gorm:"column:tenant_name"`
	FlowBusinessType *string `json:"flowBusinessType" gorm:"column:flow_business_type"`
}

// FlowTemplate 对应 flow_template。
type FlowTemplate struct {
	BaseUUID
	FlowOid         *string `json:"flowOid" gorm:"column:FLOW_OID"`
	FlowType        *string `json:"flowType" gorm:"column:FLOW_TYPE"`
	NodeOrder       *int64  `json:"nodeOrder" gorm:"column:NODE_ORDER"`
	NodeKey         *string `json:"nodeKey" gorm:"column:NODE_KEY"`
	NodeName        *string `json:"nodeName" gorm:"column:NODE_NAME"`
	NextNodeOid     *string `json:"nextNodeOid" gorm:"column:NEXT_NODE_OID"`
	PreviousNodeOid *string `json:"previousNodeOid" gorm:"column:PREVIOUS_NODE_OID"`
	ReturnNum       *int64  `json:"returnNum" gorm:"column:RETURN_NUM"`
	ReturnNodeOid   *string `json:"returnNodeOid" gorm:"column:RETURN_NODE_OID"`
	ConfigCondtion  *string `json:"configCondtion" gorm:"column:CONFIG_CONDTION"`
	ConfigType      *string `json:"configType" gorm:"column:CONFIG_TYPE"`
	ConfigId        *string `json:"configId" gorm:"column:CONFIG_ID"`
	ConfigName      *string `json:"configName" gorm:"column:CONFIG_NAME"`
}

// EntrustInfo 对应 EntrustInfo（保存在 flow_apply_info.entrust_info 的 JSON 数组元素）。
//
// DIFF: Java 的 operationTime 由 fastjson @JSONField(format="yyyy-MM-dd HH:mm:ss.SS") 输出，
// 这里保存为已格式化的字符串，保证写入 entrust_info 的 JSON 与 Java 一致。
type EntrustInfo struct {
	OperatorUserId   *string `json:"operatorUserId"`
	OperatorUserName *string `json:"operatorUserName"`
	EntrustUserId    *string `json:"entrustUserId"`
	EntrustUserName  *string `json:"entrustUserName"`
	FlowId           *string `json:"flowId"`
	FlowKey          *string `json:"flowKey"`
	FlowTemplateId   *string `json:"flowTemplateId"`
	OperationTime    *string `json:"operationTime"`
}
