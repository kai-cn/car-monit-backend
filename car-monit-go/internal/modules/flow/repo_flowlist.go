// JAVA 对照: com/ruoyi/flow/mapper/FlowListMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowListMapper.xml
// 类/职责: flow_list 数据访问（审核历史）
// 对应 Go 文件: internal/modules/flow/repo_flowlist.go
//
// DIFF: XML 有两条条件完全相同、只差排序方向的语句；Go 用 order 参数区分。
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const flowListVo = ` t.ID, t.BILL_OID, t.BUSS_TYPE, t.TASK_ID, t.flow_ruid, t.CURRENT_OID, t.SH_USER, t.SH_KEY, t.SH_VALUE, t.SH_CONTEXT, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

const (
	flowListOrderAsc  = "t.create_time ASC ,t.id"
	flowListOrderDesc = "t.create_time desc ,t.id"
)

func flowListWhere(q FlowListQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.BILL_OID", q.BillOid)
	w.eq("t.BUSS_TYPE", q.BussType)
	w.eq("t.TASK_ID", q.TaskId)
	w.eq("t.flow_ruid", q.FlowRuid)
	w.eq("t.CURRENT_OID", q.CurrentOid)
	w.eq("t.SH_USER", q.ShUser)
	w.eq("t.SH_KEY", q.ShKey)
	w.eq("t.SH_VALUE", q.ShValue)
	w.eq("t.SH_CONTEXT", q.ShContext)
	w.eq("t.BACK_COL1", q.BackCol1)
	w.eq("t.BACK_COL2", q.BackCol2)
	w.eq("t.BACK_COL3", q.BackCol3)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

func (s *Service) selectFlowListList(ctx context.Context, db *gorm.DB, q FlowListQuery, pd web.PageDomain) ([]FlowList, int64, error) {
	w := flowListWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowList, 0)
	total, err := queryList(ctx, db, flowListVo, "flow_list t", cond, flowListOrderAsc, w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

// selectFlowListListNew 对应 selectFlowListListNew（降序，内部退回找人用）。
func (s *Service) selectFlowListListNew(ctx context.Context, db *gorm.DB, q FlowListQuery) ([]FlowList, error) {
	w := flowListWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowList, 0)
	if _, err := queryList(ctx, db, flowListVo, "flow_list t", cond, flowListOrderDesc, w.args, web.PageDomain{}, &rows); err != nil {
		return nil, err
	}
	return rows, nil
}

// selectFlowListAll 是内部调用的不分页版本（listnew / exportShrz）。
func (s *Service) selectFlowListAll(ctx context.Context, db *gorm.DB, q FlowListQuery) ([]FlowList, error) {
	rows, _, err := s.selectFlowListList(ctx, db, q, web.PageDomain{})
	return rows, err
}

func (s *Service) selectFlowListByID(ctx context.Context, db *gorm.DB, id string) (*FlowList, error) {
	rows := make([]FlowList, 0, 1)
	sql := "select " + flowListVo + " from flow_list t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertFlowList(ctx context.Context, db *gorm.DB, e *FlowList) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("BILL_OID", e.BillOid)
	c.add("BUSS_TYPE", e.BussType)
	c.add("TASK_ID", e.TaskId)
	c.add("flow_ruid", e.FlowRuid)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("SH_USER", e.ShUser)
	c.add("SH_KEY", e.ShKey)
	c.add("SH_VALUE", e.ShValue)
	c.add("SH_CONTEXT", e.ShContext)
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
	return c.insert(ctx, db, "flow_list")
}

func (s *Service) updateFlowList(ctx context.Context, db *gorm.DB, e *FlowList) error {
	c := &colset{}
	c.add("BILL_OID", e.BillOid)
	c.add("BUSS_TYPE", e.BussType)
	c.add("TASK_ID", e.TaskId)
	c.add("flow_ruid", e.FlowRuid)
	c.add("CURRENT_OID", e.CurrentOid)
	c.add("SH_USER", e.ShUser)
	c.add("SH_KEY", e.ShKey)
	c.add("SH_VALUE", e.ShValue)
	c.add("SH_CONTEXT", e.ShContext)
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
	return c.update(ctx, db, "flow_list", strVal(e.ID))
}

// deleteFlowListByIDs 对应 deleteFlowListByIds —— 逻辑删。
func (s *Service) deleteFlowListByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_list set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}
