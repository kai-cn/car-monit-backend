// JAVA 对照: com/ruoyi/flow/mapper/FlowApplyInfoMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowApplyInfoMapper.xml
// 类/职责: flow_apply_info 数据访问（动态 SQL 与 XML 一一对应）
// 对应 Go 文件: internal/modules/flow/repo_applyinfo.go
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const applyInfoVo = ` t.ID, t.entrust_info, t.BILL_OID, t.BUSS_TYPE, t.FLOW_RUID, t.MSG_TITLE, t.MSG_CONTEXT, t.MSG_TYPE, t.MSG_URL, t.APPLY_NAME,
	t.CURRENT_OID, t.PC_OID, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.FLOW_STATUS, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

func applyInfoWhere(q ApplyInfoQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.BILL_OID", q.BillOid)
	w.eq("t.BUSS_TYPE", q.BussType)
	w.eq("t.FLOW_RUID", q.FlowRuid)
	w.like("t.MSG_TITLE", q.MsgTitle)
	w.like("t.MSG_CONTEXT", q.MsgContext)
	w.eq("t.MSG_TYPE", q.MsgType)
	w.eq("t.MSG_URL", q.MsgUrl)
	w.like("t.APPLY_NAME", q.ApplyName)
	w.eq("t.CURRENT_OID", q.CurrentOid)
	w.eq("t.PC_OID", q.PcOid)
	w.eq("t.BACK_COL1", q.BackCol1)
	w.eq("t.BACK_COL2", q.BackCol2)
	w.eq("t.BACK_COL3", q.BackCol3)
	w.eq("t.FLOW_STATUS", q.FlowStatus)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

// selectApplyInfoList 对应 selectFlowApplyInfoList（列表投影多带 BACK_COL1 的别名 auitEmpName）。
func (s *Service) selectApplyInfoList(ctx context.Context, db *gorm.DB, q ApplyInfoQuery, pd web.PageDomain) ([]FlowApplyInfo, int64, error) {
	w := applyInfoWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowApplyInfo, 0)
	total, err := queryList(ctx, db, applyInfoVo+", t.BACK_COL1 auit_emp_name", "flow_apply_info t", cond,
		"t.create_time desc,t.id", w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

// selectApplyInfoByID 对应 selectFlowApplyInfoById —— 详情语句不带 del_flag、不带别名。
func (s *Service) selectApplyInfoByID(ctx context.Context, db *gorm.DB, id string) (*FlowApplyInfo, error) {
	rows := make([]FlowApplyInfo, 0, 1)
	sql := "select " + applyInfoVo + " from flow_apply_info t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

// selectApplyInfoByBillID 对应 selectByBillId（条件写的是数字 0，XML 原文如此）。
func (s *Service) selectApplyInfoByBillID(ctx context.Context, db *gorm.DB, billID string) (*FlowApplyInfo, error) {
	rows := make([]FlowApplyInfo, 0, 1)
	sql := "select " + applyInfoVo + " from flow_apply_info t where t.del_flag = 0 and t.bill_oid = ?"
	if err := db.WithContext(ctx).Raw(sql, billID).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertApplyInfo(ctx context.Context, db *gorm.DB, e *FlowApplyInfo) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("entrust_info", e.EntrustInfo)
	c.add("BILL_OID", e.BillOid)
	c.add("BUSS_TYPE", e.BussType)
	c.add("FLOW_RUID", e.FlowRuid)
	c.add("MSG_TITLE", e.MsgTitle)
	c.add("MSG_CONTEXT", e.MsgContext)
	c.add("MSG_TYPE", e.MsgType)
	c.add("MSG_URL", e.MsgUrl)
	c.add("APPLY_NAME", e.ApplyName)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("PC_OID", e.PcOid)
	c.add("BACK_COL1", e.BackCol1)
	c.add("BACK_COL2", e.BackCol2)
	c.add("BACK_COL3", e.BackCol3)
	c.add("FLOW_STATUS", e.FlowStatus)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.insert(ctx, db, "flow_apply_info")
}

func (s *Service) updateApplyInfo(ctx context.Context, db *gorm.DB, e *FlowApplyInfo) error {
	c := &colset{}
	c.add("BILL_OID", e.BillOid)
	c.add("entrust_info", e.EntrustInfo)
	c.add("BUSS_TYPE", e.BussType)
	c.add("FLOW_RUID", e.FlowRuid)
	c.add("MSG_TITLE", e.MsgTitle)
	c.add("MSG_CONTEXT", e.MsgContext)
	c.add("MSG_TYPE", e.MsgType)
	c.add("MSG_URL", e.MsgUrl)
	c.add("APPLY_NAME", e.ApplyName)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("PC_OID", e.PcOid)
	c.add("BACK_COL1", e.BackCol1)
	c.add("BACK_COL2", e.BackCol2)
	c.add("BACK_COL3", e.BackCol3)
	c.add("FLOW_STATUS", e.FlowStatus)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.update(ctx, db, "flow_apply_info", strVal(e.ID))
}

func (s *Service) deleteApplyInfoByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_apply_info set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

func (s *Service) deleteApplyInfoByID(ctx context.Context, db *gorm.DB, id string) (int64, error) {
	res := db.WithContext(ctx).Exec("update flow_apply_info set del_flag = '1' where ID = ?", id)
	return res.RowsAffected, res.Error
}
