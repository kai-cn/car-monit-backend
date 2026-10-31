// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysRoleServiceImpl.java:53-343
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysRoleMapper.xml:33-148
// JAVA 对照: com/ruoyi/system/mapper/{SysRoleMenuMapper,SysRoleDeptMapper,SysUserRoleMapper}.xml
// 类/职责: 角色业务层 —— 列表（含数据权限）/唯一性校验/增删改/菜单与数据权限分配
// 对应 Go 文件: internal/modules/system/role_service.go
package system

import (
	"context"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// roleQuery 对应 SysRoleMapper.selectRoleList 中 <if> 覆盖的属性。
type roleQuery struct {
	RoleName  string
	RoleKey   string
	Status    string
	BeginTime string
	EndTime   string
}

func parseRoleQuery(c *gin.Context) roleQuery {
	return roleQuery{
		RoleName:  queryStr(c, "roleName"),
		RoleKey:   queryStr(c, "roleKey"),
		Status:    queryStr(c, "status"),
		BeginTime: queryParamsTime(c, "beginTime"),
		EndTime:   queryParamsTime(c, "endTime"),
	}
}

const roleSelectVo = `
	select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,
	       r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark
	from sys_role r
	left join sys_user_role ur on ur.role_id = r.role_id
	left join sys_user u on u.user_id = ur.user_id
	left join sys_dept d on u.dept_id = d.dept_id`

// selectRoleList 对应 SysRoleServiceImpl.selectRoleList（@DataScope(deptAlias = "d")）。
func (s *service) selectRoleList(ctx context.Context, q roleQuery, lu *model.LoginUser) ([]model.SysRole, error) {
	where, args := q.where(lu)
	rows, _, err := queryPaged[model.SysRole](ctx, s.db(ctx), web.PageDomain{}, roleSelectVo+where, args, "r.role_sort")
	if err != nil {
		return nil, err
	}
	return nonNilSlice(rows), nil
}

// selectRoleListPaged 供 /system/role/list 使用（startPage）。
func (s *service) selectRoleListPaged(ctx context.Context, q roleQuery, lu *model.LoginUser, pd web.PageDomain) ([]model.SysRole, int64, error) {
	where, args := q.where(lu)
	rows, total, err := queryPaged[model.SysRole](ctx, s.db(ctx), pd, roleSelectVo+where, args, orderByOr(pd, "r.role_sort"))
	if err != nil {
		return nil, 0, err
	}
	return nonNilSlice(rows), total, nil
}

func (q roleQuery) where(lu *model.LoginUser) (string, []any) {
	var sb strings.Builder
	args := make([]any, 0, 4)
	sb.WriteString(" where r.del_flag = '0'")
	if q.RoleName != "" {
		sb.WriteString(" and r.role_name like concat('%', ?, '%')")
		args = append(args, q.RoleName)
	}
	if q.Status != "" {
		sb.WriteString(" and r.status = ?")
		args = append(args, q.Status)
	}
	if q.RoleKey != "" {
		sb.WriteString(" and r.role_key = ?")
		args = append(args, q.RoleKey)
	}
	if q.BeginTime != "" {
		sb.WriteString(" and date_format(r.create_time,'%y%m%d') >= date_format(?,'%y%m%d')")
		args = append(args, q.BeginTime)
	}
	if q.EndTime != "" {
		sb.WriteString(" and date_format(r.create_time,'%y%m%d') <= date_format(?,'%y%m%d')")
		args = append(args, q.EndTime)
	}
	// 数据范围过滤（SysRoleMapper.xml:52 ${params.dataScope}）
	if cond, dsArgs := dataScopeCond(lu, "d", ""); cond != "" {
		sb.WriteString(cond)
		args = append(args, dsArgs...)
	}
	return sb.String(), args
}

// selectRoleAll 对应 SysRoleServiceImpl.selectRoleAll（经 AOP 代理调用 selectRoleList）。
func (s *service) selectRoleAll(ctx context.Context, lu *model.LoginUser) ([]model.SysRole, error) {
	return s.selectRoleList(ctx, roleQuery{}, lu)
}

// selectRoleListByUserId 对应 SysRoleMapper.selectRoleListByUserId（返回角色ID集合）。
func (s *service) selectRoleListByUserId(ctx context.Context, userID int64) ([]int64, error) {
	ids := make([]int64, 0)
	err := s.db(ctx).Raw(`
		select r.role_id
		from sys_role r
		left join sys_user_role ur on ur.role_id = r.role_id
		left join sys_user u on u.user_id = ur.user_id
		where u.user_id = ?`, userID).Scan(&ids).Error
	return ids, err
}

// selectRoleByID 对应 SysRoleMapper.selectRoleById。
func (s *service) selectRoleByID(ctx context.Context, roleID int64) (*model.SysRole, error) {
	var role model.SysRole
	err := s.db(ctx).Raw(roleSelectVo+" where r.role_id = ?", roleID).Scan(&role).Error
	if err != nil {
		return nil, err
	}
	if role.RoleID == 0 {
		return nil, nil
	}
	return &role, nil
}

// checkRoleNameUnique 对应 SysRoleMapper.checkRoleNameUnique。
func (s *service) checkRoleNameUnique(ctx context.Context, roleName string, roleID int64) (string, error) {
	var role model.SysRole
	err := s.db(ctx).Raw(roleSelectVo+" where r.role_name = ? limit 1", roleName).Scan(&role).Error
	if err != nil {
		return "", err
	}
	if role.RoleID != 0 && role.RoleID != roleID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkRoleKeyUnique 对应 SysRoleMapper.checkRoleKeyUnique。
func (s *service) checkRoleKeyUnique(ctx context.Context, roleKey string, roleID int64) (string, error) {
	var role model.SysRole
	err := s.db(ctx).Raw(roleSelectVo+" where r.role_key = ? limit 1", roleKey).Scan(&role).Error
	if err != nil {
		return "", err
	}
	if role.RoleID != 0 && role.RoleID != roleID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkRoleAllowed 对应 SysRoleServiceImpl.checkRoleAllowed。
func checkRoleAllowed(roleID int64) error {
	if roleID == 1 {
		return web.NewServiceError("不允许操作超级管理员角色")
	}
	return nil
}

// countUserRoleByRoleID 对应 SysUserRoleMapper.countUserRoleByRoleId。
func (s *service) countUserRoleByRoleID(ctx context.Context, roleID int64) (int64, error) {
	var count int64
	err := s.db(ctx).Raw("select count(1) from sys_user_role where role_id = ?", roleID).Scan(&count).Error
	return count, err
}

// roleBody 对应 SysRole 请求体。
type roleBody struct {
	RoleID            *int64  `json:"roleId"`
	RoleName          *string `json:"roleName"`
	RoleKey           *string `json:"roleKey"`
	RoleSort          *string `json:"roleSort"`
	DataScope         *string `json:"dataScope"`
	MenuCheckStrictly bool    `json:"menuCheckStrictly"`
	DeptCheckStrictly bool    `json:"deptCheckStrictly"`
	Status            *string `json:"status"`
	Remark            *string `json:"remark"`
	MenuIDs           []int64 `json:"menuIds"`
	DeptIDs           []int64 `json:"deptIds"`
}

// insertRole 对应 SysRoleServiceImpl.insertRole（@Transactional）。
func (s *service) insertRole(ctx context.Context, b *roleBody, createBy string) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		cols := make([]string, 0, 12)
		vals := make([]any, 0, 12)
		add := func(col string, v any) {
			cols = append(cols, col)
			vals = append(vals, v)
		}
		// JAVA 对照: SysRoleMapper.xml:93-119 insertRole
		if b.RoleID != nil && *b.RoleID != 0 {
			add("role_id", *b.RoleID)
		}
		if strOr(b.RoleName) != "" {
			add("role_name", *b.RoleName)
		}
		if strOr(b.RoleKey) != "" {
			add("role_key", *b.RoleKey)
		}
		if strOr(b.RoleSort) != "" {
			add("role_sort", *b.RoleSort)
		}
		if strOr(b.DataScope) != "" {
			add("data_scope", *b.DataScope)
		}
		// Java 的 menuCheckStrictly / deptCheckStrictly 是基本类型，永远非 null。
		add("menu_check_strictly", b.MenuCheckStrictly)
		add("dept_check_strictly", b.DeptCheckStrictly)
		if strOr(b.Status) != "" {
			add("status", *b.Status)
		}
		if strOr(b.Remark) != "" {
			add("remark", *b.Remark)
		}
		if createBy != "" {
			add("create_by", createBy)
		}
		cols = append(cols, "create_time")
		vals = append(vals, now())
		sql := "insert into sys_role (" + strings.Join(cols, ", ") + ") values (" + placeholders(len(cols)) + ")"
		res := tx.Exec(sql, vals...)
		if res.Error != nil {
			return res.Error
		}
		var newID int64
		if err := tx.Raw("select last_insert_id()").Scan(&newID).Error; err != nil {
			return err
		}
		b.RoleID = &newID
		n, err := insertRoleMenu(tx, *b.RoleID, b.MenuIDs)
		if err != nil {
			return err
		}
		rows = n
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// insertRoleMenu 对应 SysRoleServiceImpl.insertRoleMenu（返回批量插入行数，空列表返回 1）。
func insertRoleMenu(tx *gorm.DB, roleID int64, menuIDs []int64) (int64, error) {
	if len(menuIDs) == 0 {
		// DIFF: Java 在 menuIds 为 null 时抛 NPE；Go 视为“未分配菜单”，返回 1（toAjax 成功）。
		return 1, nil
	}
	parts := make([]string, 0, len(menuIDs))
	args := make([]any, 0, len(menuIDs)*2)
	for _, mid := range menuIDs {
		parts = append(parts, "(?,?)")
		args = append(args, roleID, mid)
	}
	res := tx.Exec("insert into sys_role_menu (role_id, menu_id) values "+strings.Join(parts, ","), args...)
	if res.Error != nil {
		return 0, res.Error
	}
	return res.RowsAffected, nil
}

// insertRoleDept 对应 SysRoleServiceImpl.insertRoleDept。
func insertRoleDept(tx *gorm.DB, roleID int64, deptIDs []int64) (int64, error) {
	if len(deptIDs) == 0 {
		return 1, nil
	}
	parts := make([]string, 0, len(deptIDs))
	args := make([]any, 0, len(deptIDs)*2)
	for _, did := range deptIDs {
		parts = append(parts, "(?,?)")
		args = append(args, roleID, did)
	}
	res := tx.Exec("insert into sys_role_dept (role_id, dept_id) values "+strings.Join(parts, ","), args...)
	if res.Error != nil {
		return 0, res.Error
	}
	return res.RowsAffected, nil
}

// updateRole 对应 SysRoleServiceImpl.updateRole（@Transactional）。
func (s *service) updateRole(ctx context.Context, b *roleBody, updateBy string) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if b.RoleID == nil {
			return web.NewServiceError("角色ID不能为空")
		}
		if err := execUpdateRole(tx, b, updateBy); err != nil {
			return err
		}
		if err := tx.Exec("delete from sys_role_menu where role_id = ?", *b.RoleID).Error; err != nil {
			return err
		}
		n, err := insertRoleMenu(tx, *b.RoleID, b.MenuIDs)
		if err != nil {
			return err
		}
		rows = n
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// updateRoleStatus 对应 SysRoleServiceImpl.updateRoleStatus（仅更新状态等非空字段）。
func (s *service) updateRoleStatus(ctx context.Context, b *roleBody, updateBy string) (int64, error) {
	if b.RoleID == nil {
		return 0, web.NewServiceError("角色ID不能为空")
	}
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if err := execUpdateRole(tx, b, updateBy); err != nil {
			return err
		}
		rows = 1
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// execUpdateRole 对应 SysRoleMapper.updateRole。
// JAVA 对照: SysRoleMapper.xml:121-136
func execUpdateRole(tx *gorm.DB, b *roleBody, updateBy string) error {
	if b.RoleID == nil {
		return web.NewServiceError("角色ID不能为空")
	}
	sets := make([]string, 0, 12)
	args := make([]any, 0, 14)
	strCol := func(col string, p *string, requireNonEmpty bool) {
		if p == nil {
			return
		}
		if requireNonEmpty && *p == "" {
			return
		}
		sets = append(sets, col+" = ?")
		args = append(args, *p)
	}
	strCol("role_name", b.RoleName, true)
	strCol("role_key", b.RoleKey, true)
	strCol("role_sort", b.RoleSort, true)
	strCol("data_scope", b.DataScope, true)
	sets = append(sets, "menu_check_strictly = ?", "dept_check_strictly = ?")
	args = append(args, b.MenuCheckStrictly, b.DeptCheckStrictly)
	strCol("status", b.Status, true)
	strCol("remark", b.Remark, false)
	if updateBy != "" {
		sets = append(sets, "update_by = ?")
		args = append(args, updateBy)
	}
	sets = append(sets, "update_time = ?")
	args = append(args, now())
	args = append(args, *b.RoleID)
	return tx.Exec("update sys_role set "+strings.Join(sets, ", ")+" where role_id = ?", args...).Error
}

// authDataScope 对应 SysRoleServiceImpl.authDataScope（@Transactional）。
func (s *service) authDataScope(ctx context.Context, b *roleBody, updateBy string) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		if b.RoleID == nil {
			return web.NewServiceError("角色ID不能为空")
		}
		if err := execUpdateRole(tx, b, updateBy); err != nil {
			return err
		}
		if err := tx.Exec("delete from sys_role_dept where role_id = ?", *b.RoleID).Error; err != nil {
			return err
		}
		n, err := insertRoleDept(tx, *b.RoleID, b.DeptIDs)
		if err != nil {
			return err
		}
		rows = n
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// deleteRoleByIDs 对应 SysRoleServiceImpl.deleteRoleByIds（@Transactional）。
func (s *service) deleteRoleByIDs(ctx context.Context, roleIDs []int64) (int64, error) {
	for _, id := range roleIDs {
		if err := checkRoleAllowed(id); err != nil {
			return 0, err
		}
		role, err := s.selectRoleByID(ctx, id)
		if err != nil {
			return 0, err
		}
		count, err := s.countUserRoleByRoleID(ctx, id)
		if err != nil {
			return 0, err
		}
		if count > 0 {
			name := ""
			if role != nil {
				name = model.Str(role.RoleName)
			}
			return 0, web.NewServiceError("%s已分配,不能删除", name)
		}
	}
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		ph := placeholders(len(roleIDs))
		args := make([]any, 0, len(roleIDs))
		for _, id := range roleIDs {
			args = append(args, id)
		}
		if err := tx.Exec("delete from sys_role_menu where role_id in ("+ph+")", args...).Error; err != nil {
			return err
		}
		if err := tx.Exec("delete from sys_role_dept where role_id in ("+ph+")", args...).Error; err != nil {
			return err
		}
		res := tx.Exec("update sys_role set del_flag = '2' where role_id in ("+ph+")", args...)
		if res.Error != nil {
			return res.Error
		}
		rows = res.RowsAffected
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}
