// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysLoginService.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/UserDetailsServiceImpl.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/SysPermissionService.java
// 类/职责: 登录校验 + 权限装载
// 对应 Go 文件: internal/auth/service.go
// 关键映射: AuthenticationManager.authenticate -> LoadUserByUsername + bcrypt 校验
//
// DIFF: Java 的 SysPasswordService（密码重试计数）在项目中未被任何 Provider 使用，
// 因此 Go 侧同样不实现锁定计数，保持登录路径无状态（除 Redis 验证码/登录态外）。
// DIFF: 登录日志 Java 用 AsyncManager 线程池异步写；Go 用 goroutine + 独立超时 context，
// 写失败只记录日志，不影响登录结果。
package auth

import (
	"context"
	"log/slog"
	"strings"
	"time"
	"unicode/utf8"

	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"

	"car-monit-go/internal/cache"
	"car-monit-go/internal/config"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

const (
	LoginSuccess = "Success"
	LoginFail    = "Error"
	LogoutFlag   = "Logout"
)

type Service struct {
	db     *gorm.DB
	cache  *cache.Cache
	tokens *TokenService
	cfg    *config.Config
	log    *slog.Logger
}

func NewService(db *gorm.DB, c *cache.Cache, tokens *TokenService, cfg *config.Config, log *slog.Logger) *Service {
	return &Service{db: db, cache: c, tokens: tokens, cfg: cfg, log: log}
}

func (s *Service) Tokens() *TokenService { return s.tokens }

// CheckPasswordPolicy 对应 com.ruoyi.web.util.CommonUtil.checkPassword：
// true 表示“不符合策略”（注意语义与函数名相反）。
//
// JAVA 对照: 正则 ^(?![A-Za-z0-9]+$)(?![a-z0-9\W]+$)(?![A-Za-z\W]+$)(?![A-Z0-9\W]+$)[a-zA-Z0-9\W]{8,20}$
// DIFF: Java 的 [a-zA-Z0-9\W] 不包含下划线（_ 属于 \w 但不属于字母数字），
// 因此含下划线的密码在 Java 侧一定不通过；这里显式拒绝 '_'。支持 Unicode（非 ASCII 视为 \W）。
func CheckPasswordPolicy(p string) bool {
	n := utf8.RuneCountInString(p)
	if n < 8 || n > 20 {
		return true
	}
	var hasUpper, hasLower, hasDigit, hasSpecial bool
	for _, r := range p {
		switch {
		case r == '_':
			return true
		case r >= 'A' && r <= 'Z':
			hasUpper = true
		case r >= 'a' && r <= 'z':
			hasLower = true
		case r >= '0' && r <= '9':
			hasDigit = true
		default:
			hasSpecial = true
		}
	}
	return !hasUpper || !hasLower || !hasDigit || !hasSpecial
}

// Login 对应 SysLoginService.login。
func (s *Service) Login(ctx context.Context, body model.LoginBody, ip, ua string) (string, error) {
	if err := s.validateCaptcha(ctx, body.Username, body.Code, body.UUID); err != nil {
		return "", err
	}
	user, err := s.LoadUserByUsername(ctx, body.Username)
	if err != nil {
		if err == gorm.ErrRecordNotFound {
			s.recordLogininfor(context.Background(), body.Username, LoginFail, "用户不存在/密码错误", ip, ua)
			return "", web.NewServiceError("用户不存在/密码错误")
		}
		return "", err
	}
	if model.Str(user.DelFlag) == "2" {
		msg := "对不起，您的账号：" + body.Username + " 已被删除"
		s.recordLogininfor(context.Background(), body.Username, LoginFail, msg, ip, ua)
		return "", web.NewServiceError("%s", msg)
	}
	if model.Str(user.Status) == "1" {
		msg := "对不起，您的账号：" + body.Username + " 已停用"
		s.recordLogininfor(context.Background(), body.Username, LoginFail, msg, ip, ua)
		return "", web.NewServiceError("%s", msg)
	}
	if bcrypt.CompareHashAndPassword([]byte(model.Str(user.Password)), []byte(body.Password)) != nil {
		s.recordLogininfor(context.Background(), body.Username, LoginFail, "用户不存在/密码错误", ip, ua)
		return "", web.NewServiceError("用户不存在/密码错误")
	}

	perms := s.MenuPermissions(ctx, user)
	lu := &model.LoginUser{User: user, Permissions: perms}
	token, err := s.tokens.CreateToken(ctx, lu, ip, ua)
	if err != nil {
		return "", web.WrapServiceError(err, "生成令牌失败")
	}
	s.recordLogininfor(context.Background(), body.Username, LoginSuccess, "登录成功", ip, ua)
	return token, nil
}

// validateCaptcha 对应 SysLoginService 的验证码分支：code 为空时完全跳过。
func (s *Service) validateCaptcha(ctx context.Context, username, code, uuid string) error {
	if strings.TrimSpace(code) == "" {
		return nil
	}
	key := CaptchaCodeKey + uuid
	stored, ok := s.cache.GetString(ctx, key)
	// 无论是否匹配都消费验证码（Java 先 delete 再比较）。
	s.cache.Delete(ctx, key)
	if !ok || stored == "" {
		s.recordLogininfor(context.Background(), username, LoginFail, "验证码已失效", "", "")
		return web.NewServiceError("验证码已失效")
	}
	if !strings.EqualFold(code, stored) {
		s.recordLogininfor(context.Background(), username, LoginFail, "验证码错误", "", "")
		return web.NewServiceError("验证码错误")
	}
	return nil
}

// LoadUserByUsername 对应 UserDetailsServiceImpl.loadUserByUsername + SysUserMapper.selectUserByUserName。
func (s *Service) LoadUserByUsername(ctx context.Context, username string) (*model.SysUser, error) {
	// JAVA 对照: UserDetailsServiceImpl -> SysUserMapper.selectUserByUserName（selectUserVo + deptResult）。
	var row struct {
		model.SysUser
		JoinDeptID   *int64  `gorm:"column:join_dept_id"`
		JoinDeptName *string `gorm:"column:join_dept_name"`
		DeptParentID *int64  `gorm:"column:dept_parent_id"`
		DeptOrderNum *string `gorm:"column:dept_order_num"`
		DeptStatus   *string `gorm:"column:dept_status"`
	}
	err := s.db.WithContext(ctx).Raw(`
		select u.user_id, u.user_no, u.dept_id, u.user_name, u.nick_name, u.email, u.avatar, u.phonenumber,
		       u.password, u.sex, u.status, u.del_flag, u.login_ip, u.login_date, u.create_by, u.create_time,
		       u.remark, u.user_type, u.cert_entity_id, u.cert_id, u.buss_id, u.buss_name, u.eps_name, u.image_id,
		       ifnull(d.tenant_id, -1) tenant_id, d.sub_code,
		       d.dept_id as join_dept_id, d.dept_name as join_dept_name,
		       d.parent_id as dept_parent_id, d.order_num as dept_order_num, d.status as dept_status
		from sys_user u
		left join sys_dept d on u.dept_id = d.dept_id
		where u.user_name = ? and u.del_flag = '0'
		limit 1`, username).Scan(&row).Error
	if err != nil {
		return nil, err
	}
	if row.UserID == 0 {
		return nil, gorm.ErrRecordNotFound
	}
	user := row.SysUser
	if row.JoinDeptID != nil {
		user.Dept = &model.SysDept{
			DeptID:   *row.JoinDeptID,
			DeptName: row.JoinDeptName,
			Status:   row.DeptStatus,
			OrderNum: row.DeptOrderNum,
		}
		if row.DeptParentID != nil {
			user.Dept.ParentID = row.DeptParentID
		}
	}
	roles, err := s.selectRolesByUserID(ctx, user.UserID)
	if err != nil {
		return nil, err
	}
	if roles == nil {
		roles = []*model.SysRole{}
	}
	user.Roles = roles
	return &user, nil
}

func (s *Service) selectRolesByUserID(ctx context.Context, userID int64) ([]*model.SysRole, error) {
	var roles []*model.SysRole
	// JAVA 对照: selectUserVo 的 RoleResult 只映射这 6 列。
	err := s.db.WithContext(ctx).Raw(`
		select distinct r.role_id, r.role_name, r.role_key, r.role_sort, r.data_scope, r.status
		from sys_role r
		left join sys_user_role ur on ur.role_id = r.role_id
		where r.del_flag = '0' and ur.user_id = ?`, userID).Scan(&roles).Error
	return roles, err
}

// RolePermissions 对应 SysPermissionService.getRolePermission。
func (s *Service) RolePermissions(ctx context.Context, user *model.SysUser) []string {
	if user.IsAdmin() {
		return []string{"admin"}
	}
	var keys []string
	s.db.WithContext(ctx).Raw(`
		select distinct r.role_key
		from sys_role r
		left join sys_user_role ur on ur.role_id = r.role_id
		where r.del_flag = '0' and r.status = '0' and ur.user_id = ?`, user.UserID).Scan(&keys)
	return keys
}

// MenuPermissions 对应 SysPermissionService.getMenuPermission。
func (s *Service) MenuPermissions(ctx context.Context, user *model.SysUser) []string {
	if user.IsAdmin() {
		return []string{"*:*:*"}
	}
	var perms []string
	s.db.WithContext(ctx).Raw(`
		select distinct m.perms
		from sys_menu m
		left join sys_role_menu rm on m.menu_id = rm.menu_id
		left join sys_user_role ur on rm.role_id = ur.role_id
		left join sys_role r on r.role_id = ur.role_id
		where m.status = '0' and r.status = '0' and ur.user_id = ?`, user.UserID).Scan(&perms)
	out := make([]string, 0, len(perms))
	for _, p := range perms {
		if strings.TrimSpace(p) != "" {
			out = append(out, p)
		}
	}
	return out
}

// logininforStatus 对应 AsyncFactory.recordLogininfor:71-80 的状态映射：
// Success/Logout（Java 还包含 Register，本工程无注册流程）-> Constants.SUCCESS("0")，
// Error -> Constants.FAIL("1")，其它值 Java 不设置状态（列为 NULL）。
// sys_logininfor.status 是 char(1)，直接把语义串写进去会被 MySQL 以 Data too long
// 拒绝，整条审计日志丢失。
func logininforStatus(status string) any {
	switch status {
	case LoginSuccess, LogoutFlag:
		return "0"
	case LoginFail:
		return "1"
	default:
		return nil
	}
}

// recordLogininfor 对应 AsyncFactory.recordLogininfor + SysLogininforMapper.insertLogininfor。
func (s *Service) recordLogininfor(ctx context.Context, username, status, msg, ip, ua string) {
	if username == "" {
		username = ""
	}
	go func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		err := s.db.WithContext(ctx).Exec(`
			insert into sys_logininfor (user_name, status, ipaddr, login_location, browser, os, msg, login_time)
			values (?, ?, ?, ?, ?, ?, ?, ?)`,
			username, logininforStatus(status), ip, addressByIP(ip), browserName(ua), osName(ua), msg, time.Now(),
		).Error
		if err != nil {
			s.log.Warn("写入登录日志失败", "err", err)
		}
	}()
}

// RecordLogout 对应 LogoutSuccessHandlerImpl 的登录日志。
func (s *Service) RecordLogout(ctx context.Context, username, ip, ua string) {
	s.recordLogininfor(ctx, username, LogoutFlag, "退出成功", ip, ua)
}

// Captcha 生成验证码，返回 (enabled, uuid, img)。
// JAVA 对照: CaptchaController.getCode + CaptchaConfig/KaptchaTextCreator
func (s *Service) Captcha(ctx context.Context) (bool, string, string, error) {
	uuid, img, answer, err := newCaptchaImage(s.cfg.RuoYi.CaptchaType)
	if err != nil {
		return false, "", "", err
	}
	// Constants.CAPTCHA_EXPIRATION = 2 分钟。
	if err := s.cache.SetString(ctx, CaptchaCodeKey+uuid, answer, 2*time.Minute); err != nil {
		return false, "", "", err
	}
	return true, uuid, img, nil
}

// FormatAddr 为日志输出统一 IP。
func FormatAddr(ip string) string { return ip }
