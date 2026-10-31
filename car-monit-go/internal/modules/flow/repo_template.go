// JAVA 对照: com/ruoyi/flow/mapper/FlowTemplateMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowTemplateMapper.xml
// JAVA 对照: com/ruoyi/flow/service/impl/FlowTemplateServiceImpl.java
// 类/职责: flow_template 数据访问、节点查重与节点链路重算
// 对应 Go 文件: internal/modules/flow/repo_template.go
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const flowTemplateVo = ` t.ID, t.FLOW_OID, t.FLOW_TYPE, t.NODE_ORDER, t.NODE_KEY, t.NODE_NAME, t.NEXT_NODE_OID, t.PREVIOUS_NODE_OID, t.RETURN_NUM, t.RETURN_NODE_OID,
	t.CONFIG_CONDTION, t.CONFIG_TYPE, t.CONFIG_ID, t.CONFIG_NAME, t.sort,
	t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

const (
	templateFirstNodeSentinel = "0"
	templateLastNodeSentinel  = "-1"
)

func templateWhere(q FlowTemplateQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.FLOW_OID", q.FlowOid)
	w.eq("t.FLOW_TYPE", q.FlowType)
	w.eqInt("t.NODE_ORDER", q.NodeOrder)
	w.eq("t.NODE_KEY", q.NodeKey)
	w.like("t.NODE_NAME", q.NodeName)
	w.eq("t.NEXT_NODE_OID", q.NextNodeOid)
	w.eq("t.PREVIOUS_NODE_OID", q.PreviousNodeOid)
	w.eqInt("t.RETURN_NUM", q.ReturnNum)
	w.eq("t.RETURN_NODE_OID", q.ReturnNodeOid)
	w.eq("t.CONFIG_CONDTION", q.ConfigCondtion)
	w.eq("t.CONFIG_TYPE", q.ConfigType)
	w.eq("t.CONFIG_ID", q.ConfigId)
	w.like("t.CONFIG_NAME", q.ConfigName)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

// selectTemplateList 对应 selectFlowTemplateList（order by NODE_ORDER,id）。
func (s *Service) selectTemplateList(ctx context.Context, db *gorm.DB, q FlowTemplateQuery, pd web.PageDomain) ([]FlowTemplate, int64, error) {
	w := templateWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowTemplate, 0)
	total, err := queryList(ctx, db, flowTemplateVo, "flow_template t", cond, "t.NODE_ORDER ,t.id", w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

func (s *Service) selectTemplateAll(ctx context.Context, db *gorm.DB, q FlowTemplateQuery) ([]FlowTemplate, error) {
	rows, _, err := s.selectTemplateList(ctx, db, q, web.PageDomain{})
	return rows, err
}

func (s *Service) selectTemplateByID(ctx context.Context, db *gorm.DB, id string) (*FlowTemplate, error) {
	rows := make([]FlowTemplate, 0, 1)
	sql := "select " + flowTemplateVo + " from flow_template t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertTemplate(ctx context.Context, db *gorm.DB, e *FlowTemplate) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("FLOW_OID", e.FlowOid)
	c.add("FLOW_TYPE", e.FlowType)
	c.add("NODE_ORDER", e.NodeOrder)
	c.add("NODE_KEY", e.NodeKey)
	c.add("NODE_NAME", e.NodeName)
	c.add("NEXT_NODE_OID", e.NextNodeOid)
	c.add("PREVIOUS_NODE_OID", e.PreviousNodeOid)
	c.add("RETURN_NUM", e.ReturnNum)
	c.add("RETURN_NODE_OID", e.ReturnNodeOid)
	c.add("CONFIG_CONDTION", e.ConfigCondtion)
	c.add("CONFIG_TYPE", e.ConfigType)
	c.add("CONFIG_ID", e.ConfigId)
	c.add("CONFIG_NAME", e.ConfigName)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.insert(ctx, db, "flow_template")
}

func (s *Service) updateTemplate(ctx context.Context, db *gorm.DB, e *FlowTemplate) error {
	c := &colset{}
	c.add("FLOW_OID", e.FlowOid)
	c.add("FLOW_TYPE", e.FlowType)
	c.add("NODE_ORDER", e.NodeOrder)
	c.add("NODE_KEY", e.NodeKey)
	c.add("NODE_NAME", e.NodeName)
	c.add("NEXT_NODE_OID", e.NextNodeOid)
	c.add("PREVIOUS_NODE_OID", e.PreviousNodeOid)
	c.add("RETURN_NUM", e.ReturnNum)
	c.add("RETURN_NODE_OID", e.ReturnNodeOid)
	c.add("CONFIG_CONDTION", e.ConfigCondtion)
	c.add("CONFIG_TYPE", e.ConfigType)
	c.add("CONFIG_ID", e.ConfigId)
	c.add("CONFIG_NAME", e.ConfigName)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.update(ctx, db, "flow_template", strVal(e.ID))
}

// deleteTemplateByIDs 对应 deleteFlowTemplateByIds —— 逻辑删。
func (s *Service) deleteTemplateByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_template set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

// isExistsTemplateKey 对应 isExitsKey（同流程下节点 key 唯一）。
func (s *Service) isExistsTemplateKey(ctx context.Context, db *gorm.DB, q *FlowTemplate) (int64, error) {
	sql := "select count(1) from flow_template t where t.del_flag = '0' and t.FLOW_OID = ? and t.NODE_KEY = ?"
	args := []any{orEmpty(q.FlowOid), orEmpty(q.NodeKey)}
	if strVal(q.ID) != "" {
		sql += " and t.id != ?"
		args = append(args, strVal(q.ID))
	}
	var count int64
	if err := db.WithContext(ctx).Raw(sql, args...).Row().Scan(&count); err != nil {
		return 0, err
	}
	return count, nil
}

// isExistsTemplateSort 对应 isExitsSort（同流程下节点顺序唯一）。
func (s *Service) isExistsTemplateSort(ctx context.Context, db *gorm.DB, q *FlowTemplate) (int64, error) {
	sql := "select count(1) from flow_template t where t.del_flag = '0' and t.FLOW_OID = ? and t.NODE_ORDER = ?"
	args := []any{orEmpty(q.FlowOid), q.NodeOrder}
	if strVal(q.ID) != "" {
		sql += " and t.id != ?"
		args = append(args, strVal(q.ID))
	}
	var count int64
	if err := db.WithContext(ctx).Raw(sql, args...).Row().Scan(&count); err != nil {
		return 0, err
	}
	return count, nil
}

// saveFlowOrder 对应 saveFlow：按 NODE_ORDER 重算上一节点 / 下一节点 / 退回节点。
func (s *Service) saveFlowOrder(ctx context.Context, db *gorm.DB, flowOid string) error {
	if flowOid == "" {
		return nil
	}
	rows, err := s.selectTemplateAll(ctx, db, FlowTemplateQuery{FlowOid: strPtr(flowOid)})
	if err != nil {
		return err
	}
	firstID := "-1"
	for i := range rows {
		node := &rows[i]
		preNode := ""
		nextNode := ""
		returnNode := ""
		if i == 0 {
			preNode = templateFirstNodeSentinel
			returnNode = templateFirstNodeSentinel
			firstID = strVal(node.ID)
		} else {
			preNode = strVal(rows[i-1].ID)
			returnList, err := s.selectTemplateAll(ctx, db, FlowTemplateQuery{FlowOid: strPtr(flowOid), NodeOrder: node.ReturnNum})
			if err != nil {
				return err
			}
			if len(returnList) > 0 {
				returnNode = strVal(returnList[0].ID)
			} else {
				returnNode = firstID
			}
		}
		if i == len(rows)-1 {
			nextNode = templateLastNodeSentinel
		} else {
			nextNode = strVal(rows[i+1].ID)
		}
		node.PreviousNodeOid = strPtr(preNode)
		node.NextNodeOid = strPtr(nextNode)
		node.ReturnNodeOid = strPtr(returnNode)
		if err := s.updateTemplate(ctx, db, node); err != nil {
			return err
		}
	}
	return nil
}

// saveTemplateRow 对应 saveFlowTemplate（查重 + upsert + 重算链路）。
func (s *Service) saveTemplateRow(ctx context.Context, db *gorm.DB, a actor, e *FlowTemplate) (*web.AjaxResult, error) {
	count, err := s.isExistsTemplateKey(ctx, db, e)
	if err != nil {
		return nil, err
	}
	if count > 0 {
		return web.ErrorMsg("节点key存在重复"), nil
	}
	count, err = s.isExistsTemplateSort(ctx, db, e)
	if err != nil {
		return nil, err
	}
	if count > 0 {
		return web.ErrorMsg("节点顺序存在重复"), nil
	}

	if _, err := s.upsertTemplate(ctx, db, a, e, i64Ptr(a.UserID)); err != nil {
		return nil, err
	}
	if err := s.saveFlowOrder(ctx, db, orEmpty(e.FlowOid)); err != nil {
		return nil, err
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// saveTemplateRowNew 对应 saveFlowTemplateNew：免查重，新增时 create_by 固定 -2（同步标记）。
func (s *Service) saveTemplateRowNew(ctx context.Context, db *gorm.DB, a actor, e *FlowTemplate) (*web.AjaxResult, error) {
	if _, err := s.upsertTemplate(ctx, db, a, e, i64Ptr(-2)); err != nil {
		return nil, err
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// upsertTemplate 是 saveFlowTemplate / saveFlowTemplateNew 共用的新增或修改。
func (s *Service) upsertTemplate(ctx context.Context, db *gorm.DB, a actor, e *FlowTemplate, createBy *int64) (string, error) {
	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateTemplate(ctx, db, e); err != nil {
			return "", err
		}
		return strVal(e.ID), nil
	}
	e.ID = strPtr(newUUID())
	e.DelFlag = strPtr("0")
	e.EpsID = i64Ptr(a.EpsID)
	e.CreateBy = createBy
	e.CreateTime = nowDateTime()
	e.UpdateBy = i64Ptr(a.UserID)
	e.UpdateTime = nowDateTime()
	if err := s.insertTemplate(ctx, db, e); err != nil {
		return "", err
	}
	return strVal(e.ID), nil
}
