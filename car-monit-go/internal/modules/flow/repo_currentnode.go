// JAVA 对照: com/ruoyi/flow/mapper/FlowCurrentNodeMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowCurrentNodeMapper.xml
// 类/职责: flow_current_node 数据访问（含找人 SQL 与业务表状态回写）
// 对应 Go 文件: internal/modules/flow/repo_currentnode.go
//
// DIFF: XML 的 ${backCol1} 被当作表名直接拼接（dutyAudit 分支），这里先用
// safeIdentifier 校验，语义不变但挡住非法标识符。
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const currentNodeVo = ` t.ID, t.FLOW_OID, t.CURRENT_OID, t.NODE_ORDER, t.NODE_KEY, t.NODE_NAME, t.CONFIG_TYPE, t.CONFIG_ID, t.CONFIG_NAME, t.BILL_OID, t.AUIT_EMP_OID, t.AUIT_EMP_NAME,
	t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

func currentNodeWhere(q CurrentNodeQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.FLOW_OID", q.FlowOid)
	w.eq("t.CURRENT_OID", q.CurrentOid)
	w.eqInt("t.NODE_ORDER", q.NodeOrder)
	w.eq("t.NODE_KEY", q.NodeKey)
	w.like("t.NODE_NAME", q.NodeName)
	w.eq("t.CONFIG_TYPE", q.ConfigType)
	w.eq("t.CONFIG_ID", q.ConfigId)
	w.like("t.CONFIG_NAME", q.ConfigName)
	w.eq("t.BILL_OID", q.BillOid)
	w.eq("t.AUIT_EMP_OID", q.AuitEmpOid)
	w.like("t.AUIT_EMP_NAME", q.AuitEmpName)
	w.eq("t.BACK_COL1", q.BackCol1)
	w.eq("t.BACK_COL2", q.BackCol2)
	w.eq("t.BACK_COL3", q.BackCol3)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

// selectCurrentNodeList 对应 selectFlowCurrentNodeList（order by create_time desc,t.id）。
func (s *Service) selectCurrentNodeList(ctx context.Context, db *gorm.DB, q CurrentNodeQuery, pd web.PageDomain) ([]FlowCurrentNode, int64, error) {
	w := currentNodeWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowCurrentNode, 0)
	total, err := queryList(ctx, db, currentNodeVo, "flow_current_node t", cond,
		"t.create_time desc,t.id", w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

// selectCurrentNodeAll 是内部调用用的不分页版本（等价于不带 startPage 的 selectList）。
func (s *Service) selectCurrentNodeAll(ctx context.Context, db *gorm.DB, q CurrentNodeQuery) ([]FlowCurrentNode, error) {
	rows, _, err := s.selectCurrentNodeList(ctx, db, q, web.PageDomain{})
	return rows, err
}

// selectCurrentNodeByID 对应 selectFlowCurrentNodeById（不带 del_flag）。
func (s *Service) selectCurrentNodeByID(ctx context.Context, db *gorm.DB, id string) (*FlowCurrentNode, error) {
	rows := make([]FlowCurrentNode, 0, 1)
	sql := "select " + currentNodeVo + " from flow_current_node t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertCurrentNode(ctx context.Context, db *gorm.DB, e *FlowCurrentNode) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("FLOW_OID", e.FlowOid)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("NODE_ORDER", e.NodeOrder)
	c.add("NODE_KEY", e.NodeKey)
	c.add("NODE_NAME", e.NodeName)
	c.add("CONFIG_TYPE", e.ConfigType)
	c.add("CONFIG_ID", e.ConfigId)
	c.add("CONFIG_NAME", e.ConfigName)
	c.add("BILL_OID", e.BillOid)
	c.add("AUIT_EMP_OID", e.AuitEmpOid)
	c.add("AUIT_EMP_NAME", e.AuitEmpName)
	c.add("BACK_COL1", e.BackCol1)
	c.add("BACK_COL2", e.BackCol2)
	c.add("BACK_COL3", e.BackCol3)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.insert(ctx, db, "flow_current_node")
}

func (s *Service) updateCurrentNode(ctx context.Context, db *gorm.DB, e *FlowCurrentNode) error {
	c := &colset{}
	c.add("FLOW_OID", e.FlowOid)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("NODE_ORDER", e.NodeOrder)
	c.add("NODE_KEY", e.NodeKey)
	c.add("NODE_NAME", e.NodeName)
	c.add("CONFIG_TYPE", e.ConfigType)
	c.add("CONFIG_ID", e.ConfigId)
	c.add("CONFIG_NAME", e.ConfigName)
	c.add("BILL_OID", e.BillOid)
	c.add("AUIT_EMP_OID", e.AuitEmpOid)
	c.add("AUIT_EMP_NAME", e.AuitEmpName)
	c.add("BACK_COL1", e.BackCol1)
	c.add("BACK_COL2", e.BackCol2)
	c.add("BACK_COL3", e.BackCol3)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.update(ctx, db, "flow_current_node", strVal(e.ID))
}

// deleteCurrentNodeByIDs 对应 deleteFlowCurrentNodeByIds —— 逻辑删。
func (s *Service) deleteCurrentNodeByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_current_node set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

// deleteCurrentNodeByBillID 对应 deleteByBillId —— **物理删**（XML 是 <delete>）。
func (s *Service) deleteCurrentNodeByBillID(ctx context.Context, db *gorm.DB, billOid string) (int64, error) {
	res := db.WithContext(ctx).Exec("delete from  flow_current_node  where BILL_OID = ?", billOid)
	return res.RowsAffected, res.Error
}

// selectEmpInfoList 对应 selectEmpInfoList：按角色 / 租户 / 部门 / 审核类型挑人。
func (s *Service) selectEmpInfoList(ctx context.Context, db *gorm.DB, q *FlowCurrentNode) ([]FlowCurrentNode, error) {
	sql := "select t.user_id AUIT_EMP_OID,t.nick_name AUIT_EMP_NAME from sys_user t " +
		"where t.del_flag = '0' and t.status = '0'"
	args := make([]any, 0, 4)

	if v := orEmpty(q.RoleId); v != "" {
		sql += " and exists (select 1 from sys_user_role t1 where t1.user_id = t.user_id and t1.role_id = ?)"
		args = append(args, v)
	}
	if q.TenantID != nil {
		sql += " and exists (select 1 from sys_dept td where td.del_flag = '0' and td.dept_id = t.dept_id and td.tenant_id = ?)"
		args = append(args, *q.TenantID)
	}
	if q.DeptID != nil {
		sql += " and t.dept_id = ?"
		args = append(args, *q.DeptID)
	}
	flag := orEmpty(q.Flag)
	// 科室值班人审核 —— ${backCol1} 是表名
	if flag == "dutyAudit" {
		table, err := safeIdentifier(orEmpty(q.BackCol1))
		if err != nil {
			return nil, err
		}
		sql += " and t.dept_id in  (select tp.borrow_dept_id from " + table + " tp where  tp.id = ?)"
		args = append(args, orEmpty(q.BillOid))
	}
	// 部门经理
	if flag == "bmjlAudit" {
		sql += " AND EXISTS ( SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0'" +
			" AND ds.dept_id = (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = ?)" +
			" AND ds.leader_id = t.user_id )"
		args = append(args, orEmpty(q.BackCol1))
	}
	// 分管领导
	if flag == "fgldAudit" {
		sql += " AND EXISTS ( SELECT 1 FROM sys_dept ds WHERE ds.del_flag = '0'" +
			" AND ds.dept_id = (SELECT tt.dept_id FROM sys_user tt WHERE tt.user_id = ?)" +
			" AND ds.fgld_id = t.user_id )"
		args = append(args, orEmpty(q.BackCol1))
	}
	rows := make([]FlowCurrentNode, 0)
	if err := db.WithContext(ctx).Raw(sql, args...).Scan(&rows).Error; err != nil {
		return nil, err
	}
	return rows, nil
}

// updateFlowTable 对应 updateFlowTable：把流程信息回写到业务表（${tableName}）。
func (s *Service) updateFlowTable(ctx context.Context, db *gorm.DB, e *FlowCurrentNode) error {
	table, err := safeIdentifier(orEmpty(e.TableName))
	if err != nil {
		return err
	}
	sets := make([]string, 0, 6)
	args := make([]any, 0, 6)
	if e.FlowKey != nil {
		sets = append(sets, "flow_key = ?")
		args = append(args, *e.FlowKey)
	}
	if e.FlowRuid != nil {
		sets = append(sets, "flow_ruid = ?")
		args = append(args, *e.FlowRuid)
	}
	if e.FlowApplyOid != nil {
		sets = append(sets, "flow_apply_oid = ?")
		args = append(args, *e.FlowApplyOid)
	}
	if e.FlowStatus != nil {
		sets = append(sets, "flow_status = ?")
		args = append(args, *e.FlowStatus)
		// OGNL: flowStatus == 3 —— String 与 int 的数值比较，只有 "3" 命中
		if *e.FlowStatus == "3" {
			sets = append(sets, "sh_time = now()")
		}
	}
	sets = append(sets, "update_time = now()")
	args = append(args, orEmpty(e.BillOid))
	sql := "update " + table + " set " + strings.Join(sets, ", ") + " where id = ?"
	return db.WithContext(ctx).Exec(sql, args...).Error
}
