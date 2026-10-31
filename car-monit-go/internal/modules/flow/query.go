// JAVA 对照: 各 Mapper XML 的 <select ...List parameterType="..."> 查询参数
// 类/职责: 列表查询条件（对应 Spring MVC 把 query string 绑定到实体）
// 对应 Go 文件: internal/modules/flow/query.go
//
// DIFF: Java 直接复用实体接收 query 参数；Go 单独定义 Query 结构，只包含 Mapper 中
// 参与 <if> 判断的字段。字符串条件仍按 MyBatis 语义：null 或 "" 都视为不参与过滤。
package flow

import "strings"

// QueryBase 对应各实体继承自 BaseUuidEntity 的通用查询字段。
type QueryBase struct {
	ID       *string `form:"id"`
	Sort     *int64  `form:"sort"`
	EpsID    *int64  `form:"epsId"`
	CreateBy *int64  `form:"createBy"`
	Flag     *string `form:"flag"`
}

// ApplyInfoQuery 对应 FlowApplyInfoMapper.selectFlowApplyInfoList 的条件。
type ApplyInfoQuery struct {
	QueryBase
	BillOid    *string `form:"billOid"`
	BussType   *string `form:"bussType"`
	FlowRuid   *string `form:"flowRuid"`
	MsgTitle   *string `form:"msgTitle"`
	MsgContext *string `form:"msgContext"`
	MsgType    *string `form:"msgType"`
	MsgUrl     *string `form:"msgUrl"`
	ApplyName  *string `form:"applyName"`
	CurrentOid *string `form:"currentOid"`
	PcOid      *string `form:"pcOid"`
	BackCol1   *string `form:"backCol1"`
	BackCol2   *string `form:"backCol2"`
	BackCol3   *string `form:"backCol3"`
	FlowStatus *string `form:"flowStatus"`
}

// CurrentNodeQuery 对应 FlowCurrentNodeMapper.selectFlowCurrentNodeList 的条件。
type CurrentNodeQuery struct {
	QueryBase
	FlowOid     *string `form:"flowOid"`
	CurrentOid  *string `form:"currentOid"`
	NodeOrder   *int64  `form:"nodeOrder"`
	NodeKey     *string `form:"nodeKey"`
	NodeName    *string `form:"nodeName"`
	ConfigType  *string `form:"configType"`
	ConfigId    *string `form:"configId"`
	ConfigName  *string `form:"configName"`
	BillOid     *string `form:"billOid"`
	AuitEmpOid  *string `form:"auitEmpOid"`
	AuitEmpName *string `form:"auitEmpName"`
	BackCol1    *string `form:"backCol1"`
	BackCol2    *string `form:"backCol2"`
	BackCol3    *string `form:"backCol3"`
}

// FlowListQuery 对应 FlowListMapper.selectFlowListList / selectFlowListListNew 的条件。
type FlowListQuery struct {
	QueryBase
	BillOid    *string `form:"billOid"`
	BussType   *string `form:"bussType"`
	TaskId     *string `form:"taskId"`
	FlowRuid   *string `form:"flowRuid"`
	CurrentOid *string `form:"currentOid"`
	ShUser     *string `form:"shUser"`
	ShKey      *string `form:"shKey"`
	ShValue    *string `form:"shValue"`
	ShContext  *string `form:"shContext"`
	BackCol1   *string `form:"backCol1"`
	BackCol2   *string `form:"backCol2"`
	BackCol3   *string `form:"backCol3"`
}

// MessageDisposeQuery 对应 FlowMessageDisposeMapper.selectFlowMessageDisposeList 的条件。
type MessageDisposeQuery struct {
	QueryBase
	Mid          *string `form:"mid"`
	BussId       *string `form:"bussId"`
	BussName     *string `form:"bussName"`
	MsgStatus    *string `form:"msgStatus"`
	HangTime     *string `form:"hangTime"`
	DisposeOther *string `form:"disposeOther"`
}

// MessageInfoQuery 对应 FlowMessageInfoMapper.selectFlowMessageInfoList 的条件。
type MessageInfoQuery struct {
	QueryBase
	MessageNo  *string `form:"messageNo"`
	BillOid    *string `form:"billOid"`
	BussType   *string `form:"bussType"`
	FlowRuid   *string `form:"flowRuid"`
	MsgTitle   *string `form:"msgTitle"`
	MsgContext *string `form:"msgContext"`
	MsgType    *string `form:"msgType"`
	MsgUrl     *string `form:"msgUrl"`
	PcOid      *string `form:"pcOid"`
	ApplyName  *string `form:"applyName"`
	BackCol1   *string `form:"backCol1"`
	BackCol2   *string `form:"backCol2"`
	BackCol3   *string `form:"backCol3"`
	UserID     *int64  `form:"userId"`
}

// FlowNameQuery 对应 FlowNameMapper.selectFlowNameList 的条件。
type FlowNameQuery struct {
	QueryBase
	FlowBusinessType *string `form:"flowBusinessType"`
	FlowKey          *string `form:"flowKey"`
	FlowTitle        *string `form:"flowTitle"`
	TenantName       *string `form:"tenantName"`
	FlowContext      *string `form:"flowContext"`
	TenantID         *int64  `form:"tenantId"`
}

// FlowTemplateQuery 对应 FlowTemplateMapper.selectFlowTemplateList 的条件。
type FlowTemplateQuery struct {
	QueryBase
	FlowOid         *string `form:"flowOid"`
	FlowType        *string `form:"flowType"`
	NodeOrder       *int64  `form:"nodeOrder"`
	NodeKey         *string `form:"nodeKey"`
	NodeName        *string `form:"nodeName"`
	NextNodeOid     *string `form:"nextNodeOid"`
	PreviousNodeOid *string `form:"previousNodeOid"`
	ReturnNum       *int64  `form:"returnNum"`
	ReturnNodeOid   *string `form:"returnNodeOid"`
	ConfigCondtion  *string `form:"configCondtion"`
	ConfigType      *string `form:"configType"`
	ConfigId        *string `form:"configId"`
	ConfigName      *string `form:"configName"`
}

// whereClause 累积 MyBatis 风格的 "and ..." 条件。
type whereClause struct {
	b    strings.Builder
	args []any
}

func (w *whereClause) and(expr string, args ...any) {
	w.b.WriteString(" and ")
	w.b.WriteString(expr)
	w.args = append(w.args, args...)
}

func (w *whereClause) eq(col string, v *string) {
	if v != nil && *v != "" {
		w.and(col+" = ?", *v)
	}
}

func (w *whereClause) like(col string, v *string) {
	if v != nil && *v != "" {
		w.and(col+" like concat('%', ?, '%')", *v)
	}
}

func (w *whereClause) eqInt(col string, v *int64) {
	if v != nil {
		w.and(col+" = ?", *v)
	}
}

func (w *whereClause) String() string { return w.b.String() }
