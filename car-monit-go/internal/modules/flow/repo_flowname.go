// JAVA 对照: com/ruoyi/flow/mapper/FlowNameMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowNameMapper.xml
// 类/职责: flow_name 数据访问（列表联 sys_dept 取单位名）
// 对应 Go 文件: internal/modules/flow/repo_flowname.go
//
// 照抄的怪癖：
//  1. 列表联 sys_dept 取 IFNULL(sd.dept_name,'系统默认') tenantName，tenantName 过滤的也是这个别名；
//  2. updateFlowName 的 SET 里没有 tenant_id / create_by / create_time；
//  3. isExitsKey 恒定带 create_by = -1 —— 只查系统预置流程。
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const flowNameVo = ` t.ID, t.FLOW_KEY, t.FLOW_TITLE, t.FLOW_CONTEXT, t.BUSS_NAME,t.sort, t.eps_id, t.del_flag,
	t.create_by, t.create_time, t.update_by, t.update_time,t.tenant_id, t.flow_business_type `

const flowNameFrom = "flow_name t left join sys_dept sd on sd.dept_id = t.tenant_id"

func flowNameWhere(q FlowNameQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.flow_business_type", q.FlowBusinessType)
	w.eq("t.FLOW_KEY", q.FlowKey)
	w.like("t.FLOW_TITLE", q.FlowTitle)
	if v := orEmpty(q.TenantName); v != "" {
		w.and("IFNULL(sd.dept_name,'系统默认') like concat('%', ?, '%')", v)
	}
	w.like("t.FLOW_CONTEXT", q.FlowContext)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	w.eqInt("t.tenant_id", q.TenantID)
	return w
}

// selectFlowNameList 对应 selectFlowNameList（order by tenant_id,flow_key,id）。
func (s *Service) selectFlowNameList(ctx context.Context, db *gorm.DB, q FlowNameQuery, pd web.PageDomain) ([]FlowName, int64, error) {
	w := flowNameWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowName, 0)
	total, err := queryList(ctx, db, flowNameVo+",IFNULL(sd.dept_name,'系统默认') tenant_name", flowNameFrom, cond,
		"t.tenant_id,t.flow_key,t.id", w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

func (s *Service) selectFlowNameAll(ctx context.Context, db *gorm.DB, q FlowNameQuery) ([]FlowName, error) {
	rows, _, err := s.selectFlowNameList(ctx, db, q, web.PageDomain{})
	return rows, err
}

// selectFlowNameByID 对应 selectFlowNameById（只查主表，不连 sys_dept）。
func (s *Service) selectFlowNameByID(ctx context.Context, db *gorm.DB, id string) (*FlowName, error) {
	rows := make([]FlowName, 0, 1)
	sql := "select " + flowNameVo + " from flow_name t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertFlowName(ctx context.Context, db *gorm.DB, e *FlowName) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("flow_business_type", e.FlowBusinessType)
	c.add("FLOW_KEY", e.FlowKey)
	c.add("FLOW_TITLE", e.FlowTitle)
	c.add("FLOW_CONTEXT", e.FlowContext)
	c.add("BUSS_NAME", e.BussName)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	c.add("tenant_id", e.TenantID)
	return c.insert(ctx, db, "flow_name")
}

// updateFlowName 对应 updateFlowName —— SET 里不含 tenant_id/create_by/create_time。
func (s *Service) updateFlowName(ctx context.Context, db *gorm.DB, e *FlowName) error {
	c := &colset{}
	c.add("FLOW_KEY", e.FlowKey)
	c.add("flow_business_type", e.FlowBusinessType)
	c.add("FLOW_TITLE", e.FlowTitle)
	c.add("FLOW_CONTEXT", e.FlowContext)
	c.add("BUSS_NAME", e.BussName)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.update(ctx, db, "flow_name", strVal(e.ID))
}

// deleteFlowNameByIDs 对应 deleteFlowNameByIds —— 逻辑删。
func (s *Service) deleteFlowNameByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_name set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

// isExistsKey 对应 isExitsKey：只查 create_by = -1 的系统预置流程。
func (s *Service) isExistsFlowNameKey(ctx context.Context, db *gorm.DB, q *FlowName) (int64, error) {
	sql := "select count(1) from flow_name t where t.del_flag = '0'  and t.FLOW_KEY = ? and t.create_by = -1"
	args := []any{orEmpty(q.FlowKey)}
	if q.TenantID != nil {
		sql += " and t.tenant_id = ?"
		args = append(args, *q.TenantID)
	}
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

// saveFlowNameRow 对应 saveFlowName（含 isExitsKey 查重与 createBy=-1 标记）。
func (s *Service) saveFlowNameRow(ctx context.Context, db *gorm.DB, a actor, e *FlowName) (*web.AjaxResult, error) {
	count, err := s.isExistsFlowNameKey(ctx, db, e)
	if err != nil {
		return nil, err
	}
	if count > 0 {
		return web.ErrorMsg("节点key存在重复"), nil
	}

	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateFlowName(ctx, db, e); err != nil {
			return nil, err
		}
	} else {
		e.ID = strPtr(newUUID())
		e.DelFlag = strPtr("0")
		e.EpsID = i64Ptr(a.EpsID)
		// 新增时 createBy 写死 -1：这是"系统预置"标记，tbFlow 靠它识别源流程。
		e.CreateBy = i64Ptr(-1)
		e.CreateTime = nowDateTime()
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.insertFlowName(ctx, db, e); err != nil {
			return nil, err
		}
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}

// tbFlow 对应 tbFlow：把系统预置流程（create_by = -1）复制到所有 is_uint='1' 的单位。
//
// 照抄点：入参 flowName 完全不用；flow_business_type 固定 "1"；节点复制只清
// next/previous，returnNum / returnNodeOid 原样带过去，最后 saveFlow 重算链路。
func (s *Service) tbFlow(ctx context.Context, a actor) (*web.AjaxResult, error) {
	var res *web.AjaxResult
	err := s.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		r, err := s.doTbFlow(ctx, tx, a)
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

func (s *Service) doTbFlow(ctx context.Context, db *gorm.DB, a actor) (*web.AjaxResult, error) {
	sourceList, err := s.selectFlowNameAll(ctx, db, FlowNameQuery{QueryBase: QueryBase{CreateBy: i64Ptr(-1)}})
	if err != nil {
		return nil, err
	}

	// 查询要同步的单位（SysDeptMapper.selectDeptList 的 is_uint 条件）
	deptRows := make([]struct {
		DeptID int64 `gorm:"column:dept_id"`
	}, 0)
	if err := db.WithContext(ctx).Raw(
		"select d.dept_id from sys_dept d where d.del_flag = '0' and d.is_uint = '1' order by d.parent_id, d.order_num",
	).Scan(&deptRows).Error; err != nil {
		return nil, err
	}

	for i := range sourceList {
		tempFlowName := sourceList[i]
		// 查询自己的配置信息
		templateList, err := s.selectTemplateAll(ctx, db, FlowTemplateQuery{FlowOid: tempFlowName.ID})
		if err != nil {
			return nil, err
		}

		for _, dept := range deptRows {
			// 判断是否已存在
			exists, err := s.selectFlowNameAll(ctx, db, FlowNameQuery{
				TenantID: i64Ptr(dept.DeptID),
				FlowKey:  tempFlowName.FlowKey,
			})
			if err != nil {
				return nil, err
			}
			if len(exists) > 0 {
				continue
			}

			addFlowName := &FlowName{
				BaseUUID: BaseUUID{
					ID:         strPtr(newUUID()),
					DelFlag:    strPtr("0"),
					EpsID:      i64Ptr(a.EpsID),
					CreateBy:   i64Ptr(a.UserID),
					CreateTime: nowDateTime(),
					UpdateBy:   i64Ptr(a.UserID),
					UpdateTime: nowDateTime(),
					Sort:       tempFlowName.Sort,
					TenantID:   i64Ptr(dept.DeptID),
				},
				FlowKey:          tempFlowName.FlowKey,
				FlowTitle:        tempFlowName.FlowTitle,
				FlowContext:      tempFlowName.FlowContext,
				BussName:         tempFlowName.BussName,
				FlowBusinessType: strPtr("1"),
			}
			if err := s.insertFlowName(ctx, db, addFlowName); err != nil {
				return nil, err
			}

			for k := range templateList {
				addTemplate := templateList[k]
				addTemplate.ID = nil // 主键清空 -> 新增
				addTemplate.FlowOid = addFlowName.ID
				addTemplate.NextNodeOid = strPtr("")
				addTemplate.PreviousNodeOid = strPtr("")
				if _, err := s.saveTemplateRowNew(ctx, db, a, &addTemplate); err != nil {
					return nil, err
				}
			}
			if err := s.saveFlowOrder(ctx, db, strVal(addFlowName.ID)); err != nil {
				return nil, err
			}
		}
	}
	return web.SuccessMsg("同步成功！"), nil
}
