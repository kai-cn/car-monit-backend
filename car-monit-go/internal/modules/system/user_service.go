// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java:85-649
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml:104-503
// JAVA 对照: com/ruoyi/system/mapper/{SysUserRoleMapper,SysUserPostMapper}.xml
// 类/职责: 用户业务层 —— 列表/详情/唯一性校验/增删改/导入/当前用户信息
// 对应 Go 文件: internal/modules/system/user_service.go
//
// DIFF: Java 的 @Transactional 由 Spring 代理，Go 用 db.Transaction 包裹“先删关联再写主表”。
// DIFF: Java 的 MyBatis <if> 动态列用 *T 指针 + 显式列名列表表达，保证“未传字段不覆盖”。
package system

import (
	"context"
	"fmt"
	"strings"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

	"car-monit-go/internal/model"
	"car-monit-go/internal/platform/conv"
	"car-monit-go/internal/web"
)

// ---------------------------------------------------------------------------
// 查询条件
// JAVA 对照: SysUserMapper.xml:104-211 中 <if> 覆盖的属性
// ---------------------------------------------------------------------------

// userQuery 对应 Spring 从 query string 绑定的 SysUser 查询实体。
type userQuery struct {
	UserID        *int64
	UserNo        *int64
	UserName      string
	Status        string
	Phone         string
	BeginTime     string
	EndTime       string
	DeptID        *int64
	UserType      string
	CertEntityID  string
	CertID        string
	BussID        string
	BussName      string
	EpsName       string
	TenantID      *int64
	RoleCode      string
	Flag          string
	DataID        string
	QueryNickName string
	ExcludeID     *int64
}

// parseUserQuery 对应 Spring 对形参 SysUser 的自动绑定。
func parseUserQuery(c *gin.Context) userQuery {
	return userQuery{
		UserID:        queryInt64(c, "userId"),
		UserNo:        queryInt64(c, "userNo"),
		UserName:      queryStr(c, "userName"),
		Status:        queryStr(c, "status"),
		Phone:         queryStr(c, "phonenumber"),
		BeginTime:     queryParamsTime(c, "beginTime"),
		EndTime:       queryParamsTime(c, "endTime"),
		DeptID:        queryInt64(c, "deptId"),
		UserType:      queryStr(c, "userType"),
		CertEntityID:  queryStr(c, "certEntityId"),
		CertID:        queryStr(c, "certId"),
		BussID:        queryStr(c, "bussId"),
		BussName:      queryStr(c, "bussName"),
		EpsName:       queryStr(c, "epsName"),
		TenantID:      queryInt64(c, "tenantId"),
		RoleCode:      queryStr(c, "roleCode"),
		Flag:          strings.TrimSpace(c.Query("flag")),
		DataID:        strings.TrimSpace(c.Query("dataId")),
		QueryNickName: queryStr(c, "queryNickName"),
		ExcludeID:     queryInt64(c, "excludeId"),
	}
}

// where 复刻 SysUserMapper.selectUserList 的 where 分支。
// JAVA 对照: SysUserMapper.xml:113-210
func (q userQuery) where() (string, []any) {
	var sb strings.Builder
	args := make([]any, 0, 8)
	sb.WriteString(" where u.del_flag = '0'")
	if q.UserID != nil && *q.UserID != 0 {
		sb.WriteString(" and u.user_id = ?")
		args = append(args, *q.UserID)
	}
	if q.UserNo != nil && *q.UserNo != 0 {
		sb.WriteString(" and u.user_no = ?")
		args = append(args, *q.UserNo)
	}
	if q.UserName != "" {
		sb.WriteString(" and u.user_name like concat('%', ?, '%')")
		args = append(args, q.UserName)
	}
	if q.Status != "" {
		sb.WriteString(" and u.status = ?")
		args = append(args, q.Status)
	}
	if q.Phone != "" {
		sb.WriteString(" and u.phonenumber like concat('%', ?, '%')")
		args = append(args, q.Phone)
	}
	if q.BeginTime != "" {
		sb.WriteString(" and date_format(u.create_time,'%y%m%d') >= date_format(?,'%y%m%d')")
		args = append(args, q.BeginTime)
	}
	if q.EndTime != "" {
		sb.WriteString(" and date_format(u.create_time,'%y%m%d') <= date_format(?,'%y%m%d')")
		args = append(args, q.EndTime)
	}
	if q.DeptID != nil && *q.DeptID != 0 {
		sb.WriteString(" and (u.dept_id = ? or u.dept_id in ( select t.dept_id from sys_dept t where find_in_set(?, ancestors) ))")
		args = append(args, *q.DeptID, *q.DeptID)
	}
	if q.UserType != "" {
		sb.WriteString(" and u.user_type = ?")
		args = append(args, q.UserType)
	}
	if q.CertEntityID != "" {
		sb.WriteString(" and u.cert_entity_id = ?")
		args = append(args, q.CertEntityID)
	}
	if q.CertID != "" {
		sb.WriteString(" and u.cert_id = ?")
		args = append(args, q.CertID)
	}
	if q.BussID != "" {
		sb.WriteString(" and u.buss_id = ?")
		args = append(args, q.BussID)
	}
	if q.BussName != "" {
		sb.WriteString(" and u.buss_name like concat('%', ?, '%')")
		args = append(args, q.BussName)
	}
	if q.EpsName != "" {
		sb.WriteString(" and u.eps_name like concat('%', ?, '%')")
		args = append(args, q.EpsName)
	}
	if q.TenantID != nil {
		sb.WriteString(" and d.tenant_id = ?")
		args = append(args, *q.TenantID)
	}
	if q.RoleCode != "" {
		sb.WriteString(` and exists (select 1 from sys_user_role t1, sys_role t2
			where t2.del_flag = '0' and t2.role_id = t1.role_id and t1.user_id = u.user_id and t2.role_key = ? )`)
		args = append(args, q.RoleCode)
	}
	switch q.Flag {
	case "sjzbDept":
		sb.WriteString(` and exists (
			select 1 from sys_dept tb, sys_dept tb1
			where tb.del_flag = '0' and tb.del_flag = '0' and tb1.dept_id = tb.parent_id
			  and tb.dept_id = ? and tb1.dept_id = d.tenant_id )`)
		args = append(args, q.DataID)
	case "sjzbDeptCg":
		sb.WriteString(` and exists (
			select 1 from sys_dept tb, sys_dept tb1
			where tb.del_flag = '0' and tb.del_flag = '0' and tb1.dept_id = tb.parent_id
			  and tb.dept_id = ? and tb1.dept_id = d.tenant_id )
			and exists (
			select 1 from sys_user_role sr, sys_role r
			where r.role_id = sr.role_id and r.role_key = 'cgjl_manager' and sr.user_id = u.user_id )`)
		args = append(args, q.DataID)
	case "myDeptCg":
		sb.WriteString(` and exists (
			select 1 from sys_user_role sr, sys_role r
			where r.role_id = sr.role_id and r.role_key = 'cgjl_manager' and sr.user_id = u.user_id )`)
	}
	if q.QueryNickName != "" {
		sb.WriteString(" and u.nick_name like concat('%', ?, '%')")
		args = append(args, q.QueryNickName)
	}
	if q.ExcludeID != nil {
		sb.WriteString(" and u.user_id != ?")
		args = append(args, *q.ExcludeID)
	}
	// JAVA 对照: SysUserMapper.xml:209 —— 数据范围过滤在用户列表里被注释掉，故此处不加 dataScope。
	return sb.String(), args
}

// userJoinRow 承载 selectUserList 的额外列（部门关联）。
// JAVA 对照: SysUserMapper.xml:42-49 deptResult
//
// DIFF: Java 结果集的 d.dept_id 与 u.dept_id 同名，MyBatis 按 column 名映射；
// Go 把部门侧列统一加别名，避免同名列互相覆盖。
type userJoinRow struct {
	model.SysUser
	JoinDeptID   *int64  `gorm:"column:join_dept_id"`
	JoinDeptName *string `gorm:"column:join_dept_name"`
	DeptParentID *int64  `gorm:"column:dept_parent_id"`
	DeptOrderNum *string `gorm:"column:dept_order_num"`
	DeptLeader   *string `gorm:"column:dept_leader"`
	DeptStatus   *string `gorm:"column:dept_status"`
}

const userListSelect = `
	select u.user_id, u.user_no, u.dept_id, u.nick_name, u.user_name, u.email, u.avatar, u.phonenumber,
	       u.password, u.sex, u.status, u.del_flag, u.login_ip, u.login_date, u.create_by, u.create_time,
	       u.remark, u.user_type, u.cert_entity_id, u.cert_id, u.buss_id, u.buss_name, u.eps_name, u.image_id,
	       ifnull(d.tenant_id, -1) tenant_id, d2.dept_name tenant_name,
	       d.dept_id as join_dept_id, d.dept_name as join_dept_name,
	       d.parent_id as dept_parent_id, d.order_num as dept_order_num,
	       d.leader as dept_leader, d.status as dept_status
	from sys_user u
	left join sys_dept d on u.dept_id = d.dept_id
	left join sys_dept d2 on d.tenant_id = d2.dept_id`

// selectUserList 对应 SysUserServiceImpl.selectUserList（@DataScope 在本项目 SQL 中已注释）。
func (s *service) selectUserList(ctx context.Context, q userQuery, pd web.PageDomain) ([]*model.SysUser, int64, error) {
	where, args := q.where()
	rows, total, err := queryPaged[userJoinRow](ctx, s.db(ctx), pd, userListSelect+where, args, orderByOr(pd, ""))
	if err != nil {
		return nil, 0, err
	}
	out := make([]*model.SysUser, 0, len(rows))
	for i := range rows {
		u := rows[i].SysUser
		if rows[i].JoinDeptID != nil {
			// JAVA 对照: selectUserList 的 deptResult 只映射 dept_id / dept_name。
			u.Dept = &model.SysDept{
				DeptID:   *rows[i].JoinDeptID,
				DeptName: rows[i].JoinDeptName,
			}
		}
		// JAVA 对照: <collection property="roles"> 在 MyBatis 里恒为非 null 空列表。
		if u.Roles == nil {
			u.Roles = []*model.SysRole{}
		}
		clearUserSecret(&u)
		user := u
		out = append(out, &user)
	}
	return out, total, nil
}

// clearUserSecret 对应 SysUser.password 上的 @JsonIgnore。
// DIFF: Go 的 model.SysUser 把 password 标记为可序列化（基础层不允许改），
// 因此在返回给前端前显式清空，避免 BCrypt 散列外泄。
func clearUserSecret(u *model.SysUser) {
	u.Password = nil
	u.Salt = nil
}

// userDetailRow 对应 selectUserVo 的部门关联列。
type userDetailRow struct {
	model.SysUser
	JoinDeptID   *int64  `gorm:"column:join_dept_id"`
	JoinDeptName *string `gorm:"column:join_dept_name"`
	DeptParentID *int64  `gorm:"column:dept_parent_id"`
	DeptOrderNum *string `gorm:"column:dept_order_num"`
	DeptLeader   *string `gorm:"column:dept_leader"`
	DeptStatus   *string `gorm:"column:dept_status"`
}

const userSelectVo = `
	select u.user_id, u.user_no, u.dept_id, u.user_name, u.nick_name, u.email, u.avatar, u.phonenumber,
	       u.password, u.sex, u.status, u.del_flag, u.login_ip, u.login_date, u.create_by, u.create_time,
	       u.remark, u.user_type, u.cert_entity_id, u.cert_id, u.buss_id, u.buss_name, u.eps_name, u.image_id,
	       ifnull(d.tenant_id, -1) tenant_id, d.sub_code,
	       d.dept_id as join_dept_id, d.dept_name as join_dept_name, d.leader as dept_leader,
	       d.parent_id as dept_parent_id, d.order_num as dept_order_num, d.status as dept_status
	from sys_user u
	left join sys_dept d on u.dept_id = d.dept_id`

// selectUserByID 对应 SysUserMapper.selectUserById（含 roles 集合）。
func (s *service) selectUserByID(ctx context.Context, userID int64) (*model.SysUser, error) {
	var row userDetailRow
	err := s.db(ctx).Raw(userSelectVo+" where u.user_id = ?", userID).Scan(&row).Error
	if err != nil {
		return nil, err
	}
	if row.UserID == 0 {
		return nil, nil
	}
	u := row.SysUser
	if row.JoinDeptID != nil {
		// JAVA 对照: selectUserVo 的 deptResult —— leader 列在 Java 里没有被映射上（恒为 null）。
		u.Dept = &model.SysDept{
			DeptID:   *row.JoinDeptID,
			DeptName: row.JoinDeptName,
			Status:   row.DeptStatus,
			OrderNum: row.DeptOrderNum,
		}
		if row.DeptParentID != nil {
			u.Dept.ParentID = row.DeptParentID
		}
	}
	roles, err := s.selectRolesByUserID(ctx, userID)
	if err != nil {
		return nil, err
	}
	u.Roles = roles
	clearUserSecret(&u)
	return &u, nil
}

// selectUserByUserName 对应 SysUserMapper.selectUserByUserName。
// 注意：与 UserDetailsServiceImpl 不同，此处不过滤 del_flag（忠实于 Mapper）。
func (s *service) selectUserByUserName(ctx context.Context, userName string) (*model.SysUser, error) {
	var row userDetailRow
	err := s.db(ctx).Raw(userSelectVo+" where u.user_name = ?", userName).Scan(&row).Error
	if err != nil {
		return nil, err
	}
	if row.UserID == 0 {
		return nil, nil
	}
	u := row.SysUser
	if row.JoinDeptID != nil {
		u.Dept = &model.SysDept{DeptID: *row.JoinDeptID, DeptName: row.JoinDeptName}
	}
	roles, err := s.selectRolesByUserID(ctx, u.UserID)
	if err != nil {
		return nil, err
	}
	u.Roles = roles
	return &u, nil
}

// selectRolesByUserID 对应 selectUserVo 中 sys_user_role/sys_role 的关联结果。
func (s *service) selectRolesByUserID(ctx context.Context, userID int64) ([]*model.SysRole, error) {
	roles := make([]*model.SysRole, 0)
	err := s.db(ctx).Raw(`
		select r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope, r.status
		from sys_role r
		left join sys_user_role ur on ur.role_id = r.role_id
		where ur.user_id = ?`, userID).Scan(&roles).Error
	return roles, err
}

// selectRolesByUserName 对应 SysRoleMapper.selectRolesByUserName。
func (s *service) selectRolesByUserName(ctx context.Context, userName string) ([]*model.SysRole, error) {
	roles := make([]*model.SysRole, 0)
	err := s.db(ctx).Raw(`
		select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope,
		       r.menu_check_strictly, r.dept_check_strictly, r.status, r.del_flag, r.create_time, r.remark
		from sys_role r
		left join sys_user_role ur on ur.role_id = r.role_id
		left join sys_user u on u.user_id = ur.user_id
		left join sys_dept d on u.dept_id = d.dept_id
		where r.del_flag = '0' and u.user_name = ?`, userName).Scan(&roles).Error
	return roles, err
}

// ---------------------------------------------------------------------------
// 唯一性与权限校验
// JAVA 对照: SysUserServiceImpl.java:176-235
// ---------------------------------------------------------------------------

// checkUserNameUnique 对应 SysUserMapper.checkUserNameUnique。
func (s *service) checkUserNameUnique(ctx context.Context, userName string) (string, error) {
	var count int64
	err := s.db(ctx).Raw(`select count(1) from sys_user where user_name = ? and del_flag = '0' limit 1`, userName).
		Scan(&count).Error
	if err != nil {
		return "", err
	}
	if count > 0 {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkPhoneUnique 对应 SysUserServiceImpl.checkPhoneUnique。
func (s *service) checkPhoneUnique(ctx context.Context, phone string, userID int64) (string, error) {
	var row struct {
		UserID *int64 `gorm:"column:user_id"`
	}
	err := s.db(ctx).Raw(`select user_id, phonenumber from sys_user where phonenumber = ? and del_flag = '0' limit 1`, phone).
		Scan(&row).Error
	if err != nil {
		return "", err
	}
	if row.UserID != nil && *row.UserID != userID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkEmailUnique 对应 SysUserServiceImpl.checkEmailUnique。
func (s *service) checkEmailUnique(ctx context.Context, email string, userID int64) (string, error) {
	var row struct {
		UserID *int64 `gorm:"column:user_id"`
	}
	err := s.db(ctx).Raw(`select user_id, email from sys_user where email = ? and del_flag = '0' limit 1`, email).
		Scan(&row).Error
	if err != nil {
		return "", err
	}
	if row.UserID != nil && *row.UserID != userID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkUserAllowed 对应 SysUserServiceImpl.checkUserAllowed。
func checkUserAllowed(userID int64) error {
	if userID == 1 {
		return web.NewServiceError("不允许操作超级管理员用户")
	}
	return nil
}

// ---------------------------------------------------------------------------
// 写入
// ---------------------------------------------------------------------------

// userBody 对应 SysUser 的请求体（JSON）。
//
// DIFF: Java 用包装类型 null 区分“未传”；Go 用 *T 保持同样语义。
type userBody struct {
	UserID       *int64  `json:"userId"`
	UserNo       *int64  `json:"userNo"`
	DeptID       *int64  `json:"deptId"`
	UserName     *string `json:"userName"`
	NickName     *string `json:"nickName"`
	UserType     *string `json:"userType"`
	Email        *string `json:"email"`
	Phonenumber  *string `json:"phonenumber"`
	Sex          *string `json:"sex"`
	Avatar       *string `json:"avatar"`
	Password     *string `json:"password"`
	Status       *string `json:"status"`
	Remark       *string `json:"remark"`
	CertEntityID *string `json:"certEntityId"`
	CertID       *string `json:"certId"`
	BussID       *string `json:"bussId"`
	BussName     *string `json:"bussName"`
	EpsName      *string `json:"epsName"`
	LoginIP      *string `json:"loginIp"`
	DelFlag      *string `json:"delFlag"`
	ImageID      *string `json:"imageId"`
	TenantID     *int64  `json:"tenantId"`
	RoleIDs      []int64 `json:"roleIds"`
	PostIDs      []int64 `json:"postIds"`
}

func strOr(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func int64Or(p *int64) int64 {
	if p == nil {
		return 0
	}
	return *p
}

func strPtr(s string) *string { return conv.Str(s) }

// insertUser 对应 SysUserServiceImpl.insertUser（@Transactional）。
func (s *service) insertUser(ctx context.Context, b *userBody, createBy string) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// JAVA 对照: SysUserServiceImpl.java:247-251 —— 先用部门补齐 bussName / tenantId。
		if err := s.applyDeptOfUser(tx, b); err != nil {
			return err
		}
		cols := make([]string, 0, 20)
		vals := make([]any, 0, 20)
		add := func(col string, v any) {
			cols = append(cols, col)
			vals = append(vals, v)
		}
		// JAVA 对照: SysUserMapper.xml:249-307 insertUser 的条件列
		if b.UserNo != nil {
			add("user_no", *b.UserNo)
		}
		if b.DeptID != nil {
			add("dept_id", *b.DeptID)
		}
		if strOr(b.UserName) != "" {
			add("user_name", *b.UserName)
		}
		if strOr(b.NickName) != "" {
			add("nick_name", *b.NickName)
		}
		if b.UserType != nil {
			add("user_type", *b.UserType)
		}
		if b.Email != nil {
			add("email", *b.Email)
		}
		if b.Phonenumber != nil {
			add("phonenumber", *b.Phonenumber)
		}
		if b.Sex != nil {
			add("sex", *b.Sex)
		}
		if b.Avatar != nil {
			add("avatar", *b.Avatar)
		}
		if b.Password != nil {
			add("password", *b.Password)
		}
		if b.Status != nil {
			add("status", *b.Status)
		}
		if b.Remark != nil {
			add("remark", *b.Remark)
		}
		if b.CertEntityID != nil {
			add("cert_entity_id", *b.CertEntityID)
		}
		if b.CertID != nil {
			add("cert_id", *b.CertID)
		}
		if b.BussID != nil {
			add("buss_id", *b.BussID)
		}
		if b.BussName != nil {
			add("buss_name", *b.BussName)
		}
		if b.EpsName != nil {
			add("eps_name", *b.EpsName)
		}
		if b.LoginIP != nil {
			add("login_ip", *b.LoginIP)
		}
		if b.DelFlag != nil {
			add("del_flag", *b.DelFlag)
		}
		if createBy != "" {
			add("create_by", createBy)
		}
		if b.TenantID != nil {
			add("tenant_id", *b.TenantID)
		}
		if b.ImageID != nil {
			add("image_id", *b.ImageID)
		}
		if len(cols) == 0 {
			return web.NewServiceError("新增用户失败，缺少必填字段")
		}
		sql := "insert into sys_user (" + strings.Join(cols, ", ") + ") values (" + placeholders(len(cols)) + ")"
		res := tx.Exec(sql, vals...)
		if res.Error != nil {
			return res.Error
		}
		// 回填自增主键，等价 useGeneratedKeys="true" keyProperty="userId"。
		var newID int64
		if err := tx.Raw("select last_insert_id()").Scan(&newID).Error; err != nil {
			return err
		}
		b.UserID = &newID
		// JAVA 对照: SysUserServiceImpl.java:256-258 —— 先写岗位再写角色。
		if _, err := s.insertUserDeps(tx, b); err != nil {
			return err
		}
		rows = res.RowsAffected
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// insertUserDeps 依次写入用户-岗位、用户-角色关联。
// JAVA 对照: SysUserServiceImpl.insertUserPost / insertUserRole
func (s *service) insertUserDeps(tx *gorm.DB, b *userBody) (int64, error) {
	if b.UserID == nil {
		return 0, nil
	}
	var rows int64
	if len(b.PostIDs) > 0 {
		cols := make([]string, 0, len(b.PostIDs))
		args := make([]any, 0, len(b.PostIDs)*2)
		for _, pid := range b.PostIDs {
			cols = append(cols, "(?,?)")
			args = append(args, *b.UserID, pid)
		}
		res := tx.Exec("insert into sys_user_post (user_id, post_id) values "+strings.Join(cols, ","), args...)
		if res.Error != nil {
			return 0, res.Error
		}
		rows += res.RowsAffected
	}
	if len(b.RoleIDs) > 0 {
		cols := make([]string, 0, len(b.RoleIDs))
		args := make([]any, 0, len(b.RoleIDs)*2)
		for _, rid := range b.RoleIDs {
			cols = append(cols, "(?,?)")
			args = append(args, *b.UserID, rid)
		}
		res := tx.Exec("insert into sys_user_role (user_id, role_id) values "+strings.Join(cols, ","), args...)
		if res.Error != nil {
			return 0, res.Error
		}
		rows += res.RowsAffected
	}
	return rows, nil
}

// applyDeptOfUser 复刻 insertUser/updateUser 中“用部门补 bussName / tenantId”的分支。
// JAVA 对照: SysUserServiceImpl.java:247-251 / 282-286
func (s *service) applyDeptOfUser(tx *gorm.DB, b *userBody) error {
	if b.DeptID == nil || *b.DeptID == 0 {
		return nil
	}
	var dept struct {
		DeptName string `gorm:"column:dept_name"`
		TenantID int64  `gorm:"column:tenant_id"`
	}
	err := tx.Raw("select d.dept_name, ifnull(d.tenant_id, 0) tenant_id from sys_dept d where d.dept_id = ?", *b.DeptID).
		Scan(&dept).Error
	if err != nil {
		return err
	}
	if dept.DeptName == "" {
		// DIFF: Java 在部门不存在时抛 NullPointerException（500）；Go 返回明确的业务错误。
		return web.NewServiceError("部门不存在：%d", *b.DeptID)
	}
	b.BussName = strPtr(dept.DeptName)
	b.TenantID = &dept.TenantID
	return nil
}

// updateUser 对应 SysUserServiceImpl.updateUser（@Transactional）。
func (s *service) updateUser(ctx context.Context, b *userBody, updateBy string) (int64, error) {
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		// uid 为 nil 时按 SQL NULL 传：Java 的 updateUser 不做非空校验，
		// delete/update 各自匹配 0 行，整个事务仍然成功返回。
		uid := userIDArg(b.UserID)
		// 删除用户与角色关联
		if err := tx.Exec("delete from sys_user_role where user_id = ?", uid).Error; err != nil {
			return err
		}
		// 新增用户与角色管理
		if _, err := s.insertUserDeps(tx, &userBody{UserID: b.UserID, RoleIDs: b.RoleIDs}); err != nil {
			return err
		}
		// 删除用户与岗位关联
		if err := tx.Exec("delete from sys_user_post where user_id = ?", uid).Error; err != nil {
			return err
		}
		if _, err := s.insertUserDeps(tx, &userBody{UserID: b.UserID, PostIDs: b.PostIDs}); err != nil {
			return err
		}
		if err := s.applyDeptOfUser(tx, b); err != nil {
			return err
		}
		res, err := s.execUpdateUser(tx, b, updateBy)
		if err != nil {
			return err
		}
		rows = res
		return nil
	})
	if err != nil {
		return 0, err
	}
	return rows, nil
}

// execUpdateUser 生成并执行 update sys_user ... where user_id = ?。
// JAVA 对照: SysUserMapper.xml:309-340 updateUser
func (s *service) execUpdateUser(tx *gorm.DB, b *userBody, updateBy string) (int64, error) {
	// 不再在 Go 侧拦空主键：Java 的 updateUser 直接把它交给 MyBatis，
	// `where user_id = null` 匹配 0 行、接口照样返回成功（导入分支就靠这个形态对齐）。
	sets := make([]string, 0, 20)
	args := make([]any, 0, 22)
	add := func(col string, v any) {
		sets = append(sets, col+" = ?")
		args = append(args, v)
	}
	strCol := func(col string, p *string, requireNonEmpty bool) {
		if p == nil {
			return
		}
		if requireNonEmpty && *p == "" {
			return
		}
		add(col, *p)
	}
	if b.UserNo != nil {
		add("user_no", *b.UserNo)
	}
	if b.DeptID != nil {
		add("dept_id", *b.DeptID)
	}
	strCol("user_name", b.UserName, true)
	strCol("nick_name", b.NickName, true)
	strCol("password", b.Password, true)
	strCol("user_type", b.UserType, false)
	strCol("email", b.Email, false)
	strCol("phonenumber", b.Phonenumber, false)
	strCol("sex", b.Sex, false)
	strCol("avatar", b.Avatar, false)
	strCol("status", b.Status, false)
	strCol("remark", b.Remark, false)
	strCol("cert_entity_id", b.CertEntityID, false)
	strCol("cert_id", b.CertID, false)
	strCol("buss_id", b.BussID, false)
	strCol("buss_name", b.BussName, false)
	strCol("eps_name", b.EpsName, false)
	strCol("login_ip", b.LoginIP, false)
	strCol("del_flag", b.DelFlag, false)
	if updateBy != "" {
		add("update_by", updateBy)
	}
	if b.TenantID != nil {
		add("tenant_id", *b.TenantID)
	}
	if b.ImageID != nil {
		add("image_id", *b.ImageID)
	}
	if len(sets) == 0 {
		// DIFF: Java 在“没有任何可更新列”时会拼出非法 SQL（500）；Go 直接返回 0 行。
		return 0, nil
	}
	sql := "update sys_user set " + strings.Join(sets, ", ") + " where user_id = ?"
	args = append(args, userIDArg(b.UserID))
	res := tx.Exec(sql, args...)
	if res.Error != nil {
		return 0, res.Error
	}
	return res.RowsAffected, nil
}

// userIDArg 把可空主键转成 SQL 参数（nil -> NULL，而不是解引用崩溃）。
func userIDArg(id *int64) any {
	if id == nil {
		return nil
	}
	return *id
}

// resetPwd 对应 SysUserServiceImpl.resetPwd -> userMapper.updateUser（动态更新，不触发关联表重写）。
func (s *service) resetPwd(ctx context.Context, b *userBody, updateBy string) (int64, error) {
	if b.UserID == nil || *b.UserID == 0 {
		return 0, web.NewServiceError("用户ID不能为空")
	}
	return s.execUpdateUser(s.db(ctx), b, updateBy)
}

// updateUserStatus 对应 SysUserServiceImpl.updateUserStatus -> userMapper.updateUser。
// 状态修改 / bindUky 都走这里：只更新 body 提供的列。
func (s *service) updateUserStatus(ctx context.Context, b *userBody, updateBy string) (int64, error) {
	if b.UserID == nil || *b.UserID == 0 {
		return 0, web.NewServiceError("用户ID不能为空")
	}
	return s.execUpdateUser(s.db(ctx), b, updateBy)
}

// deleteUserByIDs 对应 SysUserServiceImpl.deleteUserByIds（@Transactional）。
func (s *service) deleteUserByIDs(ctx context.Context, userIDs []int64) (int64, error) {
	for _, id := range userIDs {
		if err := checkUserAllowed(id); err != nil {
			return 0, err
		}
	}
	var rows int64
	err := s.app.DB.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
		ph := placeholders(len(userIDs))
		args := make([]any, 0, len(userIDs))
		for _, id := range userIDs {
			args = append(args, id)
		}
		if err := tx.Exec("delete from sys_user_role where user_id in ("+ph+")", args...).Error; err != nil {
			return err
		}
		if err := tx.Exec("delete from sys_user_post where user_id in ("+ph+")", args...).Error; err != nil {
			return err
		}
		res := tx.Exec("update sys_user set del_flag = '1' where user_id in ("+ph+")", args...)
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

// ---------------------------------------------------------------------------
// 导入
// JAVA 对照: SysUserServiceImpl.java:456-513 importUser
// ---------------------------------------------------------------------------

// importUser 逐行导入用户，返回 Java 的汇总消息；有失败行时返回 ServiceError（code 500）。
func (s *service) importUser(ctx context.Context, list []*userBody, updateSupport bool, operName string) (string, error) {
	if len(list) == 0 {
		return "", web.NewServiceError("导入用户数据不能为空！")
	}
	var initPwd string
	if err := s.db(ctx).Raw("select config_value from sys_config where config_key = ? limit 1", initPasswordConfigKey).
		Scan(&initPwd).Error; err != nil {
		return "", err
	}
	if initPwd == "" {
		initPwd = defaultPwd
	}
	encPwd, err := encodePassword(initPwd)
	if err != nil {
		return "", err
	}

	successNum, failureNum := 0, 0
	var successMsg, failureMsg strings.Builder
	for _, u := range list {
		name := strOr(u.UserName)
		exist, err := s.selectUserByUserName(ctx, name)
		if err != nil {
			failureNum++
			fmt.Fprintf(&failureMsg, "<br/>%d、账号 %s 导入失败：%s", failureNum, name, err.Error())
			continue
		}
		switch {
		case exist == nil:
			pwd := encPwd
			u.Password = &pwd
			if _, err := s.insertUser(ctx, u, operName); err != nil {
				failureNum++
				fmt.Fprintf(&failureMsg, "<br/>%d、账号 %s 导入失败：%s", failureNum, name, err.Error())
				continue
			}
			successNum++
			fmt.Fprintf(&successMsg, "<br/>%d、账号 %s 导入成功", successNum, name)
		case updateSupport:
			if _, err := s.updateUser(ctx, u, operName); err != nil {
				failureNum++
				fmt.Fprintf(&failureMsg, "<br/>%d、账号 %s 导入失败：%s", failureNum, name, err.Error())
				continue
			}
			successNum++
			fmt.Fprintf(&successMsg, "<br/>%d、账号 %s 更新成功", successNum, name)
		default:
			failureNum++
			fmt.Fprintf(&failureMsg, "<br/>%d、账号 %s 已存在", failureNum, name)
		}
	}
	if failureNum > 0 {
		return "", web.NewServiceError("很抱歉，导入失败！共 %d 条数据格式不正确，错误如下：%s", failureNum, failureMsg.String())
	}
	return fmt.Sprintf("恭喜您，数据已全部导入成功！共 %d 条，数据如下：%s", successNum, successMsg.String()), nil
}

// ---------------------------------------------------------------------------
// 当前用户信息
// JAVA 对照: SysUserServiceImpl.java:558-595 selectCurrentUser
// ---------------------------------------------------------------------------

// selectCurrentUser 返回“是否总公司人员 / 是否采购经理”等前端开关标记。
func (s *service) selectCurrentUser(ctx context.Context, lu *model.LoginUser) (*model.SysUser, error) {
	if lu == nil || lu.User == nil {
		return nil, web.NewServiceErrorCode(401, "获取用户信息异常")
	}
	user := lu.User
	out := &model.SysUser{
		UserID:             user.UserID,
		DeptID:             user.DeptID,
		HeadOffice:         model.BoolPtr(false),
		ProcurementManager: model.BoolPtr(false),
	}

	// 获取总公司列表（tree_leavel ∈ {1,2} 的部门，以及其 tenant_id 指向它们的部门）。
	depts, err := s.selectDeptList(ctx, deptQuery{})
	if err != nil {
		return nil, err
	}
	head := make(map[int64]struct{})
	for _, d := range depts {
		if lv := model.IntVal(d.TreeLeavel); lv == 1 || lv == 2 {
			head[d.DeptID] = struct{}{}
		}
	}
	for _, d := range depts {
		if _, ok := head[model.Int64Val(d.TenantID)]; ok {
			head[d.DeptID] = struct{}{}
		}
	}
	if _, ok := head[user.DeptID]; ok {
		out.HeadOffice = model.BoolPtr(true)
	}

	// 查询采购经理角色信息
	roles, err := s.selectRoleList(ctx, roleQuery{RoleKey: procurementManagerRoleKey}, lu)
	if err != nil {
		return nil, err
	}
	if len(roles) > 0 {
		userRoles, err := s.selectRolesByUserName(ctx, model.Str(user.UserName))
		if err != nil {
			return nil, err
		}
		for _, r := range userRoles {
			if r.RoleID == roles[0].RoleID {
				out.ProcurementManager = model.BoolPtr(true)
				break
			}
		}
	}
	return out, nil
}
