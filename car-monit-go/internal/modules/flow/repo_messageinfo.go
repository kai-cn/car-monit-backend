// JAVA 对照: com/ruoyi/flow/mapper/FlowMessageInfoMapper.java
// JAVA 对照: ruoyi-system/src/main/resources/mapper/flow/FlowMessageInfoMapper.xml
// JAVA 对照: com/ruoyi/flow/service/impl/FlowMessageInfoServiceImpl.java
// 类/职责: flow_message_info 数据访问 + 消息主体 upsert
// 对应 Go 文件: internal/modules/flow/repo_messageinfo.go
//
// DIFF: XML 的别名是 camelCase（flowStatus / curEmpNames / msgStatus），GORM 按
// gorm column 名匹配列标签，因此这里把别名写成对应的下划线列名，JSON 输出不变。
// DIFF: 详情语句只查主表（与 XML 一致），列表语句 left join FLOW_APPLY_INFO。
package flow

import (
	"context"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/web"
)

const messageInfoVo = ` t.ID, t.message_no, t.BILL_OID, t.BUSS_TYPE, t.FLOW_RUID, t.MSG_TITLE, t.MSG_CONTEXT, t.MSG_TYPE, t.MSG_URL, t.PC_OID,
	t.APPLY_NAME, t.BACK_COL1, t.BACK_COL2, t.BACK_COL3, t.sort, t.eps_id, t.del_flag, t.create_by, t.create_time, t.update_by, t.update_time `

const messageInfoFrom = "flow_message_info t left join flow_apply_info app on app.del_flag = '0' and app.BILL_OID = t.BILL_OID"

// flag 取值 —— 与 XML 的 <choose> 分支一一对应。
const (
	flagMyDb = "mydb" // 我的待办
	flagMyYb = "myyb" // 我的已办
	flagMyYj = "myyj" // 我的已结
	flagMyXx = "myxx" // 我的消息
)

func messageInfoWhere(q MessageInfoQuery) *whereClause {
	w := &whereClause{}
	w.eq("t.id", q.ID)
	w.eq("t.message_no", q.MessageNo)
	w.eq("t.BILL_OID", q.BillOid)
	w.eq("t.BUSS_TYPE", q.BussType)
	w.eq("t.FLOW_RUID", q.FlowRuid)
	w.like("t.MSG_TITLE", q.MsgTitle)
	w.like("t.MSG_CONTEXT", q.MsgContext)
	w.eq("t.MSG_TYPE", q.MsgType)
	w.eq("t.MSG_URL", q.MsgUrl)
	w.eq("t.PC_OID", q.PcOid)
	w.like("t.APPLY_NAME", q.ApplyName)
	w.eq("t.BACK_COL1", q.BackCol1)
	w.eq("t.BACK_COL2", q.BackCol2)
	w.eq("t.BACK_COL3", q.BackCol3)
	w.eqInt("t.sort", q.Sort)
	w.eqInt("t.eps_id", q.EpsID)
	w.eqInt("t.create_by", q.CreateBy)
	return w
}

// selectMessageInfoList 对应 selectFlowMessageInfoList：flag 驱动投影与 WHERE 变形。
func (s *Service) selectMessageInfoList(ctx context.Context, db *gorm.DB, q MessageInfoQuery,
	flag string, userID int64, pd web.PageDomain) ([]FlowMessageInfo, int64, error) {
	if err := pd.StartPageError(); err != nil {
		return nil, 0, err
	}
	w := messageInfoWhere(q)

	selectSQL := messageInfoVo + ",app.FLOW_STATUS flow_status,app.BACK_COL1 cur_emp_names"
	selectArgs := make([]any, 0, 1)
	if flag == flagMyXx {
		selectSQL += ",(select t2.MSG_STATUS from flow_message_dispose t2 where t2.del_flag = '0' and t2.mid = t.id and t2.BUSS_ID = ?) msg_status"
		selectArgs = append(selectArgs, userID)
	}

	switch flag {
	case flagMyDb:
		w.and("t.MSG_TYPE = '2'")
		w.and("exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ? and t1.MSG_STATUS = '2')", userID)
	case flagMyYb:
		w.and("t.MSG_TYPE = '2'")
		w.and("exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ? and t1.MSG_STATUS = '1')", userID)
	case flagMyYj:
		w.and("t.MSG_TYPE = '2'")
		w.and("exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ? and t1.MSG_STATUS = '1')", userID)
		w.and("app.FLOW_STATUS = '3'")
	case flagMyXx:
		w.and("t.MSG_TYPE = '1'")
		w.and("exists (select 1 from flow_message_dispose t1 where t1.del_flag = '0' and t1.mid = t.id and t1.BUSS_ID = ?)", userID)
	}

	cond := " and t.del_flag = '0'" + w.String()
	rows := make([]FlowMessageInfo, 0)

	total := int64(0)
	if pd.HasPage {
		var err error
		total, err = countRows(ctx, db, messageInfoFrom, cond, w.args)
		if err != nil {
			return nil, 0, err
		}
	}

	if pd.SkipQuery(total) {
		return rows, total, nil
	}

	args := append(selectArgs, w.args...)
	base := "select " + selectSQL + " from " + messageInfoFrom + " where 1 = 1" + cond
	sqlStr, sqlArgs := pageSQL(base, args, pd, "t.create_time desc,t.id", total)
	if err := db.WithContext(ctx).Raw(sqlStr, sqlArgs...).Scan(&rows).Error; err != nil {
		return nil, 0, err
	}
	if !pd.HasPage {
		total = int64(len(rows))
	}
	return rows, total, nil
}

// selectMessageInfoAll 是内部 upsert / 待办查询用的不分页版本。
func (s *Service) selectMessageInfoAll(ctx context.Context, db *gorm.DB, q MessageInfoQuery) ([]FlowMessageInfo, error) {
	rows, _, err := s.selectMessageInfoList(ctx, db, q, "", 0, web.PageDomain{})
	return rows, err
}

func (s *Service) selectMessageInfoByID(ctx context.Context, db *gorm.DB, id string) (*FlowMessageInfo, error) {
	rows := make([]FlowMessageInfo, 0, 1)
	sql := "select " + messageInfoVo + " from flow_message_info t where t.ID = ?"
	if err := db.WithContext(ctx).Raw(sql, id).Scan(&rows).Error; err != nil {
		return nil, err
	}
	if len(rows) == 0 || rows[0].ID == nil {
		return nil, nil
	}
	return &rows[0], nil
}

func (s *Service) insertMessageInfo(ctx context.Context, db *gorm.DB, e *FlowMessageInfo) error {
	c := &colset{}
	c.add("ID", e.ID)
	c.add("message_no", e.MessageNo)
	c.add("BILL_OID", e.BillOid)
	c.add("BUSS_TYPE", e.BussType)
	c.add("FLOW_RUID", e.FlowRuid)
	c.add("MSG_TITLE", e.MsgTitle)
	c.add("MSG_CONTEXT", e.MsgContext)
	c.add("MSG_TYPE", e.MsgType)
	c.add("MSG_URL", e.MsgUrl)
	c.add("PC_OID", e.PcOid)
	c.add("APPLY_NAME", e.ApplyName)
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
	return c.insert(ctx, db, "flow_message_info")
}

func (s *Service) updateMessageInfo(ctx context.Context, db *gorm.DB, e *FlowMessageInfo) error {
	c := &colset{}
	// 注意 XML 里 message_no 排在 bill_oid 之后（顺序照抄）。
	c.add("BILL_OID", e.BillOid)
	c.add("message_no", e.MessageNo)
	c.add("BUSS_TYPE", e.BussType)
	c.add("FLOW_RUID", e.FlowRuid)
	c.add("MSG_TITLE", e.MsgTitle)
	c.add("MSG_CONTEXT", e.MsgContext)
	c.add("MSG_TYPE", e.MsgType)
	c.add("MSG_URL", e.MsgUrl)
	c.add("PC_OID", e.PcOid)
	c.add("APPLY_NAME", e.ApplyName)
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
	return c.update(ctx, db, "flow_message_info", strVal(e.ID))
}

// deleteMessageInfoByIDs 对应 deleteFlowMessageInfoByIds —— 逻辑删。
func (s *Service) deleteMessageInfoByIDs(ctx context.Context, db *gorm.DB, ids []string) (int64, error) {
	if len(ids) == 0 {
		return 0, nil
	}
	marks := strings.TrimSuffix(strings.Repeat("?,", len(ids)), ",")
	args := make([]any, len(ids))
	for i, id := range ids {
		args[i] = id
	}
	res := db.WithContext(ctx).Exec("update flow_message_info set del_flag = '1' where ID in ("+marks+")", args...)
	return res.RowsAffected, res.Error
}

// saveMessageInfoRow 对应 saveFlowMessageInfo：按 billOid + msgType + bussType upsert，返回主键。
func (s *Service) saveMessageInfoRow(ctx context.Context, db *gorm.DB, a actor, e *FlowMessageInfo) (string, error) {
	exist, err := s.selectMessageInfoAll(ctx, db, MessageInfoQuery{
		BillOid: e.BillOid, MsgType: e.MsgType, BussType: e.BussType,
	})
	if err != nil {
		return "", err
	}
	if len(exist) > 0 {
		e.ID = exist[0].ID
	}

	if strVal(e.ID) != "" {
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.updateMessageInfo(ctx, db, e); err != nil {
			return "", err
		}
	} else {
		e.ID = strPtr(newUUID())
		e.DelFlag = strPtr("0")
		e.EpsID = i64Ptr(a.EpsID)
		e.CreateBy = i64Ptr(a.UserID)
		e.CreateTime = nowDateTime()
		e.UpdateBy = i64Ptr(a.UserID)
		e.UpdateTime = nowDateTime()
		if err := s.insertMessageInfo(ctx, db, e); err != nil {
			return "", err
		}
	}

	// 新增明细：disposeList 为空时不报错，消息主体照样落库。
	for i := range e.DisposeList {
		d := &e.DisposeList[i]
		d.Mid = e.ID
		d.MsgStatus = strPtr("2")
		if _, err := s.saveMessageDisposeRow(ctx, db, a, d); err != nil {
			return "", err
		}
	}
	return strVal(e.ID), nil
}
