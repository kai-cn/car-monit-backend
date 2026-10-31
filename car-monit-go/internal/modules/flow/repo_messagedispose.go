// JAVA 对照: com/ruoyi/flow/mapper/FlowMessageDisposeMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowMessageDisposeMapper.xml
// 类/职责: flow_message_dispose 数据访问（待办的处理人明细）
// 对应 Go 文件: internal/modules/flow/repo_messagedispose.go
//
// 三种"按 mid 动待办"的写操作语义不同，不能合并：
//   - removeFlowMessage      <delete>（物理删），可只删自己那条
//   - saveSzzdFlowMessage    只把自己那条置 MSG_STATUS='1'
//   - saveSzzdFlowMessageAll 把所有未办理的处理人改成 bussId 并置为已办理
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const messageDisposeVo = ` t.ID, t.MID, t.BUSS_ID, t.BUSS_NAME, t.MSG_STATUS, t.HANG_TIME, t.DISPOSE_OTHER, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

// 空 mid 的替身（Java 里就地改成 "-1"，靠 WHERE 不命中来挡参数）。
const emptyMid = "-1"

func messageDisposeWhere(q MessageDisposeQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.MID", q.Mid)
	w.eq("t.BUSS_ID", q.BussId)
	w.like("t.BUSS_NAME", q.BussName)
	w.eq("t.MSG_STATUS", q.MsgStatus)
	if q.HangTime != nil && *q.HangTime != "" {
		w.and("t.HANG_TIME = ?", *q.HangTime)
	}
	w.eq("t.DISPOSE_OTHER", q.DisposeOther)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

func (s *Service) selectMessageDisposeList(ctx context.Context, db *gorm.DB, q MessageDisposeQuery, pd web.PageDomain) ([]FlowMessageDispose, int64, error) {
	w := messageDisposeWhere(q)
	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowMessageDispose, 0)
	total, err := queryList(ctx, db, messageDisposeVo, "flow_message_dispose t", cond,
		"t.create_time desc,t.id", w.args, pd, &rows)
	if err != nil {
		return nil, 0, err
	}
	return rows, total, nil
}

func (s *Service) selectMessageDisposeAll(ctx context.Context, db *gorm.DB, q MessageDisposeQuery) ([]FlowMessageDispose, error) {
	rows, _, err := s.selectMessageDisposeList(ctx, db, q, web.PageDomain{})
	return rows, err
}

func (s *Service) selectMessageDisposeByID(ctx context.Context, db *gorm.DB, id string) (*FlowMessageDispose, error) {
	rows := make([]FlowMessageDispose, 0, 1)
	sql := "select " + messageDisposeVo + " from flow_message_dispose t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertMessageDispose(ctx context.Context, db *gorm.DB, e *FlowMessageDispose) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("MID", e.Mid)
	c.add("BUSS_ID", e.BussId)
	c.add("BUSS_NAME", e.BussName)
	c.add("MSG_STATUS", e.MsgStatus)
	c.add("HANG_TIME", e.HangTime)
	c.add("DISPOSE_OTHER", e.DisposeOther)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.insert(ctx, db, "flow_message_dispose")
}

func (s *Service) updateMessageDispose(ctx context.Context, db *gorm.DB, e *FlowMessageDispose) error {
	c := &colset{}
	c.add("MID", e.Mid)
	c.add("BUSS_ID", e.BussId)
	c.add("BUSS_NAME", e.BussName)
	c.add("MSG_STATUS", e.MsgStatus)
	c.add("HANG_TIME", e.HangTime)
	c.add("DISPOSE_OTHER", e.DisposeOther)
	c.add("sort", e.Sort)
	c.add("eps_id", e.EpsID)
	c.add("del_flag", e.DelFlag)
	c.add("create_by", e.CreateBy)
	c.add("create_time", e.CreateTime)
	c.add("update_by", e.UpdateBy)
	c.add("update_time", e.UpdateTime)
	return c.update(ctx, db, "flow_message_dispose", strVal(e.ID))
}

// deleteMessageDisposeByIDs 对应 deleteFlowMessageDisposeByIds —— 逻辑删。
func (s *Service) deleteMessageDisposeByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_message_dispose set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

// removeFlowMessage 对应 removeFlowMessage —— **物理删**。
func (s *Service) removeFlowMessage(ctx context.Context, db *gorm.DB, mid, bussID string) (int64, error) {
	realMid := mid
	if realMid == "" {
		realMid = emptyMid
	}
	sql := "delete from flow_message_dispose where MID = ?"
	args := []any{realMid}
	if bussID != "" {
		sql += " and BUSS_ID = ?"
		args = append(args, bussID)
	}
	res := db.WithContext(ctx).Exec(sql, args...)
	return res.RowsAffected, res.Error
}

// saveSzzdFlowMessage 对应 saveSzzdFlowMessage —— 只把自己那条置为已办理。
func (s *Service) saveSzzdFlowMessage(ctx context.Context, db *gorm.DB, mid, bussID string) (int64, error) {
	realMid := mid
	if realMid == "" {
		realMid = emptyMid
	}
	sql := "update flow_message_dispose set MSG_STATUS = '1' where del_flag = '0' and  MID = ?"
	args := []any{realMid}
	if bussID != "" {
		sql += " and BUSS_ID = ?"
		args = append(args, bussID)
	}
	res := db.WithContext(ctx).Exec(sql, args...)
	return res.RowsAffected, res.Error
}

// saveSzzdFlowMessageAll 对应 saveSzzdFlowMessageAll —— 改写处理人并置为已办理。
func (s *Service) saveSzzdFlowMessageAll(ctx context.Context, db *gorm.DB, mid, bussID string) (int64, error) {
	realMid := mid
	if realMid == "" {
		realMid = emptyMid
	}
	realBussID := bussID
	if realBussID == "" {
		realBussID = "-1"
	}
	res := db.WithContext(ctx).Exec(
		"update flow_message_dispose set MSG_STATUS = '1',BUSS_ID = ? where del_flag = '0' and  MID = ?  and MSG_STATUS = '2'",
		realBussID, realMid)
	return res.RowsAffected, res.Error
}

// saveFlowDisposeList 对应 saveFlowList(mid, userIds)：先按 mid+处理人物理删旧行，再插一条未办理。
func (s *Service) saveFlowDisposeList(ctx context.Context, db *gorm.DB, a actor, mid string, userIDs []string) error {
	for _, userID := range userIDs {
		if _, err := s.removeFlowMessage(ctx, db, mid, userID); err != nil {
			return err
		}
		row := &FlowMessageDispose{Mid: strPtr(mid), MsgStatus: strPtr("2"), BussId: strPtr(userID)}
		if _, err := s.saveMessageDisposeRow(ctx, db, a, row); err != nil {
			return err
		}
	}
	return nil
}

// saveMessageDisposeRow 对应 saveFlowMessageDispose（新增/修改 + 审计字段）。
func (s *Service) saveMessageDisposeRow(ctx context.Context, db *gorm.DB, a actor, e *FlowMessageDispose) (*web.AjaxResult, error) {
	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateMessageDispose(ctx, db, e); err != nil {
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
		if err := s.insertMessageDispose(ctx, db, e); err != nil {
			return nil, err
		}
	}
	return web.SuccessFull("操作成功！", strVal(e.ID)), nil
}
