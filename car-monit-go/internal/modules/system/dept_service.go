// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysDeptServiceImpl.java:44-435
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysDeptMapper.xml:15-266
// 类/职责: 部门业务层 —— 列表/树/唯一性校验/增删改（含 sub_code 与 tenant_id 联动）
// 对应 Go 文件: internal/modules/system/dept_service.go
//
// DIFF: Java 的 @DataScope 注解在 SysDeptMapper.xml 里对应位置是**注释掉的**，
// 因此这里不附加数据权限条件，保持与 Java 实际行为一致。
// DIFF: Java 的 @Transactional 由 Spring 代理；Go 显式用 db.Transaction。
package system

import (
	"context"
	"fmt"
	"strings"

	"gorm.io/gorm"

	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

const deptSelectVo = `
	select d.dept_id, d.parent_id, d.ancestors, d.dept_name, d.order_num, d.leader_id, d.leader,
	       d.fgld_id, d.fgld_name, d.bank_name, d.account, d.social_code, d.postal_code, d.address,
	       d.phone, d.email, d.status, d.del_flag, d.create_by, d.create_time,
	       d.is_zbzg, d.is_uint, d.tree_leavel, d.sub_code, d.dept_jc, d.tenant_id
	from sys_dept d`

// deptQuery 对应 SysDept 作为查询条件时 mapper XML 里用到的属性。
type deptQuery struct {
	ParentID    *int64
	DeptName    string
	Status      string
	DeptID      *int64
	IsZbzg      string
	IsUint      string
	TreeLeavel  *int
	SubCode     string
	DeptJc      string
	TenantID    *int64
	Flag        string
	DataID      string
	LeaderID    *int64
	Leader      string
	FgldID      *int64
	FgldName    string
	DeptSubCode string
}

// where 复刻 SysDeptMapper.selectDeptList 的 <if> 分支。
func (q deptQuery) where() (string, []any) {
	var sb strings.Builder
	args := make([]any, 0, 8)
	sb.WriteString(" where d.del_flag = '0'")
	add := func(cond string, v any) {
		sb.WriteString(cond)
		args = append(args, v)
	}
	if q.ParentID != nil {
		add(" and d.parent_id = ?", *q.ParentID)
	}
	if q.DeptName != "" {
		add(" and d.dept_name like concat('%', ?, '%')", q.DeptName)
	}
	if q.Status != "" {
		add(" and d.status = ?", q.Status)
	}
	if q.DeptID != nil {
		add(" and d.dept_id = ?", *q.DeptID)
	}
	if q.IsZbzg != "" {
		add(" and d.is_zbzg = ?", q.IsZbzg)
	}
	if q.IsUint != "" {
		add(" and d.is_uint = ?", q.IsUint)
	}
	if q.TreeLeavel != nil {
		add(" and d.tree_leavel = ?", *q.TreeLeavel)
	}
	if q.SubCode != "" {
		add(" and d.sub_code = ?", q.SubCode)
	}
	if q.DeptJc != "" {
		add(" and d.dept_jc = ?", q.DeptJc)
	}
	if q.TenantID != nil {
		add(" and d.tenant_id = ?", *q.TenantID)
	}
	if q.Flag == "sjzbDept" {
		add(` and exists (
			select 1 from sys_dept tb, sys_dept tb1
			where tb.del_flag = '0' and tb1.dept_id = tb.parent_id
			and tb.dept_id = ? and tb1.dept_id = d.tenant_id)`, q.DataID)
	}
	if q.LeaderID != nil {
		add(" and d.leader_id = ?", *q.LeaderID)
	}
	if q.Leader != "" {
		add(" and d.leader = ?", q.Leader)
	}
	if q.FgldID != nil {
		add(" and d.fgld_id = ?", *q.FgldID)
	}
	if q.FgldName != "" {
		add(" and d.fgld_name like concat('%', ?, '%')", q.FgldName)
	}
	if q.DeptSubCode != "" {
		add(" and d.sub_code like concat(?, '%')", q.DeptSubCode)
	}
	sb.WriteString(" order by d.parent_id, d.order_num")
	return sb.String(), args
}

// selectDeptList 对应 SysDeptServiceImpl.selectDeptList。
func (s *service) selectDeptList(ctx context.Context, q deptQuery) ([]model.SysDept, error) {
	where, args := q.where()
	rows, _, err := queryPaged[model.SysDept](ctx, s.db(ctx), web.PageDomain{}, deptSelectVo+where, args, "")
	if err != nil {
		return nil, err
	}
	return nonNilSlice(rows), nil
}

// selectDeptByID 对应 SysDeptMapper.selectDeptById（不过滤 del_flag）。
func (s *service) selectDeptByID(ctx context.Context, deptID int64) (*model.SysDept, error) {
	var d model.SysDept
	err := s.db(ctx).Raw(deptSelectVo+" where dept_id = ?", deptID).Scan(&d).Error
	if err != nil {
		return nil, err
	}
	if d.DeptID == 0 {
		return nil, nil
	}
	return &d, nil
}

// selectDeptListByRoleID 对应 SysDeptMapper.selectDeptListByRoleId。
func (s *service) selectDeptListByRoleID(ctx context.Context, roleID int64, deptCheckStrictly bool) ([]int64, error) {
	sql := `select d.dept_id from sys_dept d
		left join sys_role_dept rd on d.dept_id = rd.dept_id
		where rd.role_id = ?`
	args := []any{roleID}
	if deptCheckStrictly {
		sql += ` and d.dept_id not in (select d.parent_id from sys_dept d
			inner join sys_role_dept rd on d.dept_id = rd.dept_id and rd.role_id = ?)`
		args = append(args, roleID)
	}
	sql += " order by d.parent_id, d.order_num"
	ids := make([]int64, 0)
	err := s.db(ctx).Raw(sql, args...).Scan(&ids).Error
	return ids, err
}

// checkDeptNameUnique 对应 SysDeptMapper.checkDeptNameUnique：按 (dept_name, parent_id) 判重。
func (s *service) checkDeptNameUnique(ctx context.Context, deptName string, parentID int64) (*model.SysDept, error) {
	var d model.SysDept
	err := s.db(ctx).Raw(deptSelectVo+" where dept_name = ? and parent_id = ? limit 1", deptName, parentID).Scan(&d).Error
	if err != nil {
		return nil, err
	}
	if d.DeptID == 0 {
		return nil, nil
	}
	return &d, nil
}

// hasChildByDeptID 对应 SysDeptMapper.hasChildByDeptId。
func (s *service) hasChildByDeptID(ctx context.Context, deptID int64) (bool, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_dept where del_flag = '0' and parent_id = ? limit 1", deptID).Scan(&n).Error
	return n > 0, err
}

// checkDeptExistUser 对应 SysDeptMapper.checkDeptExistUser。
func (s *service) checkDeptExistUser(ctx context.Context, deptID int64) (bool, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_user where dept_id = ? and del_flag = '0'", deptID).Scan(&n).Error
	return n > 0, err
}

// selectNormalChildrenDeptByID 对应 SysDeptMapper.selectNormalChildrenDeptById。
func (s *service) selectNormalChildrenDeptByID(ctx context.Context, deptID int64) (int64, error) {
	var n int64
	err := s.db(ctx).Raw("select count(*) from sys_dept where status = 0 and del_flag = '0' and find_in_set(?, ancestors)", deptID).Scan(&n).Error
	return n, err
}

// selectTenantID 对应 SysDeptMapper.selectTenantId：找 sub_code 前缀最长的“单位”祖先。
func (s *service) selectTenantID(ctx context.Context, subCode string) (*model.SysDept, error) {
	var d model.SysDept
	err := s.db(ctx).Raw(deptSelectVo+` where d.del_flag = '0' and ? like concat(d.sub_code, '%')
		and d.is_uint = '1' order by d.tree_leavel desc limit 1`, subCode).Scan(&d).Error
	if err != nil {
		return nil, err
	}
	if d.DeptID == 0 {
		return nil, nil
	}
	return &d, nil
}

// buildSubCode 复刻 Java 的部门编码生成规则。
func buildSubCode(parentID int64, parentSubCode string, counts int) string {
	next := counts + 1
	if parentID == 0 {
		return fmt.Sprintf("00%d", next)
	}
	switch {
	case counts < 9:
		return fmt.Sprintf("%s-00%d", parentSubCode, next)
	case counts < 99:
		return fmt.Sprintf("%s-0%d", parentSubCode, next)
	default:
		return fmt.Sprintf("%s-%d", parentSubCode, next)
	}
}

// prepareDeptForWrite 对应 insert/update 共用的“树级别 + sub_code”计算。
func (s *service) prepareDeptForWrite(ctx context.Context, d *model.SysDept) error {
	parentID := model.Int64Val(d.ParentID)
	parentSubCode := ""
	if parentID == 0 {
		d.TreeLeavel = model.IntPtr(1)
		parentSubCode = "001"
	} else {
		parent, err := s.selectDeptByID(ctx, parentID)
		if err != nil {
			return err
		}
		if parent == nil {
			// Java 在 parentBO.getTreeLeavel() 处抛 NPE，GlobalExceptionHandler 返回 msg=null。
			return web.NewNilMessageError()
		}
		d.TreeLeavel = model.IntPtr(model.IntVal(parent.TreeLeavel) + 1)
		parentSubCode = model.Str(parent.SubCode)
	}

	flag := true
	if d.DeptID != 0 {
		old, err := s.selectDeptByID(ctx, d.DeptID)
		if err != nil {
			return err
		}
		if old != nil && model.Int64Val(old.ParentID) == parentID {
			flag = false
		}
	}
	if flag {
		counts, err := s.countChildren(ctx, parentID)
		if err != nil {
			return err
		}
		d.SubCode = model.Ptr(buildSubCode(parentID, parentSubCode, counts))
	}
	if model.Str(d.IsUint) == "0" {
		d.IsZbzg = model.Ptr("0")
	}
	return nil
}

func (s *service) countChildren(ctx context.Context, parentID int64) (int, error) {
	var n int64
	err := s.db(ctx).Raw("select count(1) from sys_dept where del_flag = '0' and parent_id = ?", parentID).Scan(&n).Error
	return int(n), err
}

// insertDept 对应 SysDeptServiceImpl.insertDept（@Transactional）。
func (s *service) insertDept(ctx context.Context, d *model.SysDept) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := s.prepareDeptForWrite(ctx, d); err != nil {
			return err
		}
		cols := deptInsertColumns(d)
		res := tx.Table("sys_dept").Create(cols)
		if res.Error != nil {
			return res.Error
		}
		rows = res.RowsAffected
		if d.DeptID == 0 {
			var id int64
			if err := tx.Raw("select last_insert_id()").Scan(&id).Error; err != nil {
				return err
			}
			d.DeptID = id
		}
		// JAVA 对照: 修改 tenant_id —— 部门取祖先单位，单位取自身。
		tenantID := d.DeptID
		if model.Str(d.IsUint) == "0" {
			tenant, err := s.selectTenantID(ctx, model.Str(d.SubCode))
			if err != nil {
				return err
			}
			if tenant == nil {
				return nil
			}
			tenantID = tenant.DeptID
		}
		return tx.Table("sys_dept").Where("dept_id = ?", d.DeptID).Update("tenant_id", tenantID).Error
	})
	return rows, err
}

// updateDept 对应 SysDeptServiceImpl.updateDept（@Transactional）。
func (s *service) updateDept(ctx context.Context, d *model.SysDept) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := s.prepareDeptForWrite(ctx, d); err != nil {
			return err
		}
		cols := deptUpdateColumns(d)
		if len(cols) > 0 {
			res := tx.Table("sys_dept").Where("dept_id = ?", d.DeptID).Updates(cols)
			if res.Error != nil {
				return res.Error
			}
			rows = res.RowsAffected
		}
		return s.updateTenantIDs(ctx, tx, model.Str(d.SubCode))
	})
	return rows, err
}

// updateTenantIDs 对应 SysDeptServiceImpl.updateTenantId：刷新 sub_code 前缀子树的 tenant_id。
func (s *service) updateTenantIDs(ctx context.Context, tx *gorm.DB, subCode string) error {
	sql := deptSelectVo + " where d.del_flag = '0'"
	args := []any{}
	if subCode != "" {
		sql += " and d.sub_code like concat(?, '%')"
		args = append(args, subCode)
	}
	rows := make([]model.SysDept, 0)
	if err := tx.WithContext(ctx).Raw(sql, args...).Scan(&rows).Error; err != nil {
		return err
	}
	for _, d := range rows {
		tenantID := d.DeptID
		if model.Str(d.IsUint) == "0" {
			var tenant model.SysDept
			if err := tx.WithContext(ctx).Raw(deptSelectVo+` where d.del_flag = '0' and ? like concat(d.sub_code, '%')
				and d.is_uint = '1' order by d.tree_leavel desc limit 1`, d.SubCode).Scan(&tenant).Error; err != nil {
				return err
			}
			if tenant.DeptID == 0 {
				continue
			}
			tenantID = tenant.DeptID
		}
		if err := tx.WithContext(ctx).Table("sys_dept").Where("dept_id = ?", d.DeptID).
			Update("tenant_id", tenantID).Error; err != nil {
			return err
		}
	}
	return nil
}

// deleteDeptByID 对应 SysDeptMapper.deleteDeptById（逻辑删除 del_flag='2'）。
func (s *service) deleteDeptByID(ctx context.Context, deptID int64) (int64, error) {
	res := s.db(ctx).Exec("update sys_dept set del_flag = '2' where dept_id = ?", deptID)
	return res.RowsAffected, res.Error
}

// buildDeptTree 对应 SysDeptServiceImpl.buildDeptTree。
func buildDeptTree(depts []model.SysDept) []model.SysDept {
	if len(depts) == 0 {
		return depts
	}
	ids := make(map[int64]struct{}, len(depts))
	for _, d := range depts {
		ids[d.DeptID] = struct{}{}
	}
	out := make([]model.SysDept, 0, len(depts))
	for i := range depts {
		if _, ok := ids[model.Int64Val(depts[i].ParentID)]; !ok {
			recursionDept(depts, &depts[i])
			out = append(out, depts[i])
		}
	}
	if len(out) == 0 {
		return depts
	}
	return out
}

func recursionDept(list []model.SysDept, node *model.SysDept) {
	children := make([]*model.SysDept, 0)
	for i := range list {
		if model.Int64Val(list[i].ParentID) == node.DeptID {
			children = append(children, &list[i])
		}
	}
	if len(children) > 0 {
		node.Children = children
		for _, child := range children {
			recursionDept(list, child)
		}
	}
}

// buildDeptTreeSelect 对应 SysDeptServiceImpl.buildDeptTreeSelect。
func buildDeptTreeSelect(depts []model.SysDept) []*model.TreeSelect {
	trees := buildDeptTree(depts)
	out := make([]*model.TreeSelect, 0, len(trees))
	for i := range trees {
		out = append(out, deptTreeSelect(&trees[i]))
	}
	return out
}

func deptTreeSelect(d *model.SysDept) *model.TreeSelect {
	ts := &model.TreeSelect{ID: d.DeptID, Label: model.Str(d.DeptName)}
	if len(d.Children) > 0 {
		ts.Children = make([]*model.TreeSelect, 0, len(d.Children))
		for _, child := range d.Children {
			ts.Children = append(ts.Children, deptTreeSelect(child))
		}
	}
	return ts
}

// deptInsertColumns 对应 SysDeptMapper.insertDept 的动态列（含 create_time=sysdate()）。
func deptInsertColumns(d *model.SysDept) map[string]any {
	cols := map[string]any{
		"create_time": now(),
	}
	if d.DeptID != 0 {
		cols["dept_id"] = d.DeptID
	}
	if d.ParentID != nil {
		cols["parent_id"] = *d.ParentID
	}
	putStr := func(col string, v *string) {
		if v != nil && *v != "" {
			cols[col] = *v
		}
	}
	putStr("dept_name", d.DeptName)
	putStr("ancestors", d.Ancestors)
	putStr("order_num", d.OrderNum)
	if d.LeaderID != nil {
		cols["leader_id"] = *d.LeaderID
	}
	putStr("leader", d.Leader)
	if d.FgldID != nil {
		cols["fgld_id"] = *d.FgldID
	}
	putStr("fgld_name", d.FgldName)
	putStr("bank_name", d.BankName)
	putStr("account", d.Account)
	putStr("social_code", d.SocialCode)
	putStr("postal_code", d.PostalCode)
	putStr("address", d.Address)
	putStr("phone", d.Phone)
	putStr("email", d.Email)
	putStr("status", d.Status)
	putStr("create_by", d.CreateBy)
	putStr("is_zbzg", d.IsZbzg)
	putStr("is_uint", d.IsUint)
	if d.TreeLeavel != nil {
		cols["tree_leavel"] = *d.TreeLeavel
	}
	putStr("sub_code", d.SubCode)
	putStr("dept_jc", d.DeptJc)
	if d.TenantID != nil {
		cols["tenant_id"] = *d.TenantID
	}
	return cols
}

// deptUpdateColumns 对应 SysDeptMapper.updateDept 的 <set>：
// phone/email 只判 != null（空串会写库），update_time 恒写。
func deptUpdateColumns(d *model.SysDept) map[string]any {
	cols := map[string]any{"update_time": now()}
	if d.ParentID != nil {
		cols["parent_id"] = *d.ParentID
	}
	putStr := func(col string, v *string) {
		if v != nil && *v != "" {
			cols[col] = *v
		}
	}
	putStr("dept_name", d.DeptName)
	putStr("ancestors", d.Ancestors)
	putStr("order_num", d.OrderNum)
	if d.LeaderID != nil {
		cols["leader_id"] = *d.LeaderID
	}
	putStr("leader", d.Leader)
	if d.FgldID != nil {
		cols["fgld_id"] = *d.FgldID
	}
	putStr("fgld_name", d.FgldName)
	putStr("bank_name", d.BankName)
	putStr("account", d.Account)
	putStr("social_code", d.SocialCode)
	putStr("postal_code", d.PostalCode)
	putStr("address", d.Address)
	putStr("phone", d.Phone)
	putStr("email", d.Email)
	putStr("status", d.Status)
	putStr("update_by", d.UpdateBy)
	putStr("is_zbzg", d.IsZbzg)
	putStr("is_uint", d.IsUint)
	if d.TreeLeavel != nil {
		cols["tree_leavel"] = *d.TreeLeavel
	}
	putStr("sub_code", d.SubCode)
	putStr("dept_jc", d.DeptJc)
	if d.TenantID != nil {
		cols["tenant_id"] = *d.TenantID
	}
	return cols
}
