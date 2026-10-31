// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysProfileController.java:37-151
// JAVA 对照: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysUserServiceImpl.java:133-170,315-333
// JAVA 对照: ruoyi-system/src/main/resources/mapper/system/SysUserMapper.xml:235-247,309-340,386-397
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/utils/file/FileUploadUtils.java:88-135
// 类/职责: 个人信息 — 查询/改资料/改密码/上传头像（均无 @PreAuthorize，登录即可）
// 对应 Go 文件: internal/modules/systemaux/profile.go
//
// DIFF: updatePwd 的两次 BCrypt 加密保持 Java 原样（写库与写缓存是两份不同 salt 的哈希）。
// DIFF: Java 的 SysUser.password 是 @JsonIgnore；Go 侧返回前显式清空 password/salt。
// DIFF: 改资料成功后只回写缓存的 nickName/phonenumber/email/sex 四个字段。
package systemaux

import (
	"context"
	"errors"
	"strings"

	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

// profileBody 对应 @RequestBody SysUser（updateUser 动态 SQL 覆盖到的列）。
type profileBody struct {
	UserID       int64         `json:"userId"`
	UserNo       *int64        `json:"userNo"`
	DeptID       *int64        `json:"deptId"`
	UserName     *string       `json:"userName"`
	NickName     *string       `json:"nickName"`
	Password     *string       `json:"password"`
	UserType     *string       `json:"userType"`
	Email        *string       `json:"email"`
	Phonenumber  *string       `json:"phonenumber"`
	Sex          *string       `json:"sex"`
	Avatar       *string       `json:"avatar"`
	Status       *string       `json:"status"`
	Remark       *string       `json:"remark"`
	CertEntityID *string       `json:"certEntityId"`
	CertID       *string       `json:"certId"`
	BussID       *string       `json:"bussId"`
	BussName     *string       `json:"bussName"`
	EpsName      *string       `json:"epsName"`
	LoginIP      *string       `json:"loginIp"`
	LoginDate    *web.DateTime `json:"loginDate"`
	DelFlag      *string       `json:"delFlag"`
	CreateBy     *string       `json:"createBy"`
	CreateTime   *web.DateTime `json:"createTime"`
	UpdateBy     *string       `json:"updateBy"`
	UpdateTime   *web.DateTime `json:"updateTime"`
	TenantID     *int64        `json:"tenantId"`
	ImageID      *string       `json:"imageId"`
}

// javaNullStr 对应 Java 字符串拼接 null 时输出 "null"。
func javaNullStr(p *string) string {
	if p == nil {
		return "null"
	}
	return *p
}

type profileService struct {
	app *app.App
}

func newProfileService(a *app.App) *profileService { return &profileService{app: a} }

// selectRoleGroup 对应 selectUserRoleGroup：角色名逗号串。
func (s *profileService) selectRoleGroup(ctx context.Context, userName string) (string, error) {
	var names []string
	if err := s.app.DB.WithContext(ctx).Raw(
		`select distinct r.role_name from sys_role r
		 left join sys_user_role ur on ur.role_id = r.role_id
		 left join sys_user u on u.user_id = ur.user_id
		 left join sys_dept d on u.dept_id = d.dept_id
		 where r.del_flag = '0' and u.user_name = ?`, userName).Scan(&names).Error; err != nil {
		return "", err
	}
	return strings.Join(names, ","), nil
}

// selectPostGroup 对应 selectUserPostGroup：岗位名逗号串。
func (s *profileService) selectPostGroup(ctx context.Context, userName string) (string, error) {
	var names []string
	if err := s.app.DB.WithContext(ctx).Raw(
		`select p.post_name from sys_post p
		 left join sys_user_post up on up.post_id = p.post_id
		 left join sys_user u on u.user_id = up.user_id
		 where u.user_name = ?`, userName).Scan(&names).Error; err != nil {
		return "", err
	}
	return strings.Join(names, ","), nil
}

// checkPhoneUnique 对应 checkPhoneUnique(user)：同号且不是自己才算重复。
func (s *profileService) checkPhoneUnique(ctx context.Context, phone string, userID int64) (string, error) {
	var row struct {
		UserID *int64 `gorm:"column:user_id"`
	}
	err := s.app.DB.WithContext(ctx).Raw(
		"select user_id, phonenumber from sys_user where phonenumber = ? and del_flag = '0' limit 1", phone).
		Take(&row).Error
	if err != nil {
		if isNotFound(err) {
			return uniqueOld, nil
		}
		return "", err
	}
	if row.UserID != nil && *row.UserID != userID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// checkEmailUnique 对应 checkEmailUnique(user)。
func (s *profileService) checkEmailUnique(ctx context.Context, email string, userID int64) (string, error) {
	var row struct {
		UserID *int64 `gorm:"column:user_id"`
	}
	err := s.app.DB.WithContext(ctx).Raw(
		"select user_id, email from sys_user where email = ? and del_flag = '0' limit 1", email).
		Take(&row).Error
	if err != nil {
		if isNotFound(err) {
			return uniqueOld, nil
		}
		return "", err
	}
	if row.UserID != nil && *row.UserID != userID {
		return notUniqueOld, nil
	}
	return uniqueOld, nil
}

// updateProfile 对应 userMapper.updateUser（按 body 中非空字段动态 SET，where user_id）。
func (s *profileService) updateProfile(ctx context.Context, b *profileBody) (int64, error) {
	sets := make([]string, 0, 26)
	args := make([]any, 0, 27)
	add := func(col string, v any) {
		sets = append(sets, col+" = ?")
		args = append(args, v)
	}
	if b.UserNo != nil {
		add("user_no", *b.UserNo)
	}
	if b.DeptID != nil {
		add("dept_id", *b.DeptID)
	}
	if v := strVal(b.UserName); v != "" {
		add("user_name", v)
	}
	if v := strVal(b.NickName); v != "" {
		add("nick_name", v)
	}
	if v := strVal(b.Password); v != "" {
		add("password", v)
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
	if b.LoginDate != nil {
		add("login_date", b.LoginDate)
	}
	if b.DelFlag != nil {
		add("del_flag", *b.DelFlag)
	}
	if b.CreateBy != nil {
		add("create_by", *b.CreateBy)
	}
	if b.CreateTime != nil {
		add("create_time", b.CreateTime)
	}
	if b.UpdateBy != nil {
		add("update_by", *b.UpdateBy)
	}
	if b.UpdateTime != nil {
		add("update_time", b.UpdateTime)
	}
	if b.TenantID != nil {
		add("tenant_id", *b.TenantID)
	}
	if b.ImageID != nil {
		add("image_id", *b.ImageID)
	}
	if len(sets) == 0 {
		// MyBatis 会生成非法 SQL 抛异常；这里返回 0 行，呼应控制器“修改个人信息异常”分支。
		return 0, nil
	}
	args = append(args, b.UserID)
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_user set "+strings.Join(sets, ", ")+" where user_id = ?", args...)
	return res.RowsAffected, res.Error
}

// resetPwdByUserName 对应 resetUserPwd：update_time 用 now()。
func (s *profileService) resetPwdByUserName(ctx context.Context, userName, password string) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_user set password = ?, update_time = now() where user_name = ?", password, userName)
	return res.RowsAffected, res.Error
}

// updateAvatar 对应 updateUserAvatar。
func (s *profileService) updateAvatar(ctx context.Context, userName, avatar string) (int64, error) {
	res := s.app.DB.WithContext(ctx).Exec(
		"update sys_user set avatar = ? where user_name = ?", avatar, userName)
	return res.RowsAffected, res.Error
}

// ---------------------------------------------------------------------------
// HTTP 入口
// ---------------------------------------------------------------------------

type profileHandler struct {
	app *app.App
	svc *profileService
}

func newProfileHandler(a *app.App) *profileHandler {
	return &profileHandler{app: a, svc: newProfileService(a)}
}

// Profile 对应 GET /system/user/profile：缓存用户 + 实时角色组/岗位组。
func (h *profileHandler) Profile(c *gin.Context) {
	lu := auth.CurrentUser(c)
	ctx := c.Request.Context()
	roleGroup, err := h.svc.selectRoleGroup(ctx, lu.Username())
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	postGroup, err := h.svc.selectPostGroup(ctx, lu.Username())
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	user := *lu.User
	user.Password = nil
	user.Salt = nil
	// JAVA 对照: BaseEntity.getParams() 惰性建 HashMap，fastjson2 序列化时带 "@type" 标记。
	user.Params = map[string]any{"@type": "java.util.HashMap"}
	if user.Dept != nil {
		dept := *user.Dept
		dept.Params = map[string]any{"@type": "java.util.HashMap"}
		user.Dept = &dept
	}
	roles := make([]*model.SysRole, 0, len(user.Roles))
	for _, role := range user.Roles {
		if role == nil {
			continue
		}
		roleCopy := *role
		roleCopy.Params = map[string]any{"@type": "java.util.HashMap"}
		roles = append(roles, &roleCopy)
	}
	user.Roles = roles
	ajax := web.SuccessData(&user)
	ajax.Put("roleGroup", roleGroup)
	ajax.Put("postGroup", postGroup)
	web.JSON(c, ajax)
}

// UpdateProfile 对应 PUT /system/user/profile。
func (h *profileHandler) UpdateProfile(c *gin.Context) {
	var body profileBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	ctx := c.Request.Context()
	if isNotEmpty(body.Phonenumber) {
		unique, err := h.svc.checkPhoneUnique(ctx, *body.Phonenumber, body.UserID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if unique == notUniqueOld {
			web.JSON(c, web.ErrorMsg("修改用户'"+javaNullStr(body.UserName)+"'失败，手机号码已存在"))
			return
		}
	}
	if isNotEmpty(body.Email) {
		unique, err := h.svc.checkEmailUnique(ctx, *body.Email, body.UserID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		if unique == notUniqueOld {
			web.JSON(c, web.ErrorMsg("修改用户'"+javaNullStr(body.UserName)+"'失败，邮箱账号已存在"))
			return
		}
	}
	rows, err := h.svc.updateProfile(ctx, &body)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if rows <= 0 {
		web.JSON(c, web.ErrorMsg("修改个人信息异常，请联系管理员"))
		return
	}
	lu := auth.CurrentUser(c)
	lu.User.NickName = model.Ptr(strVal(body.NickName))
	lu.User.Phonenumber = model.Ptr(strVal(body.Phonenumber))
	lu.User.Email = model.Ptr(strVal(body.Email))
	lu.User.Sex = model.Ptr(strVal(body.Sex))
	h.app.Tokens.SetLoginUser(ctx, lu)
	web.JSON(c, web.Success())
}

// UpdatePwd 对应 PUT /system/user/profile/updatePwd（形参无注解，query 优先、表单其次）。
func (h *profileHandler) UpdatePwd(c *gin.Context) {
	oldPassword := requestParam(c, "oldPassword")
	newPassword := requestParam(c, "newPassword")
	ctx := c.Request.Context()

	lu := auth.CurrentUser(c)
	userName := lu.Username()
	password := ""
	if lu.User != nil {
		password = model.Str(lu.User.Password)
	}
	if bcrypt.CompareHashAndPassword([]byte(password), []byte(oldPassword)) != nil {
		web.JSON(c, web.ErrorMsg("修改密码失败，旧密码错误"))
		return
	}
	if bcrypt.CompareHashAndPassword([]byte(password), []byte(newPassword)) == nil {
		web.JSON(c, web.ErrorMsg("新密码不能与旧密码相同"))
		return
	}
	// JAVA 对照: CommonUtil.checkPassword 返回 true 表示不合法。
	if auth.CheckPasswordPolicy(newPassword) {
		web.JSON(c, web.ErrorMsg("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"))
		return
	}

	encoded, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		web.JSON(c, web.ErrorMsg("修改密码异常，请联系管理员"))
		return
	}
	rows, err := h.svc.resetPwdByUserName(ctx, userName, string(encoded))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if rows <= 0 {
		web.JSON(c, web.ErrorMsg("修改密码异常，请联系管理员"))
		return
	}
	// Java: 第二次 encryptPassword，salt 与写库那次不同。
	cached, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err == nil {
		lu.User.Password = model.Ptr(string(cached))
		h.app.Tokens.SetLoginUser(ctx, lu)
	}
	web.JSON(c, web.Success())
}

// Avatar 对应 POST /system/user/profile/avatar（字段名 avatarfile）。
func (h *profileHandler) Avatar(c *gin.Context) {
	fh, err := c.FormFile("avatarfile")
	if err == nil && fh.Size > 0 {
		ctx := c.Request.Context()
		lu := auth.CurrentUser(c)
		url, upErr := uploadTo(h.app.Cfg.RuoYi.AvatarPath(), h.app.Cfg.RuoYi.Profile, fh, defaultAllowedExtension)
		if upErr != nil {
			web.JSON(c, web.ErrorMsg(upErr.Error()))
			return
		}
		rows, dbErr := h.svc.updateAvatar(ctx, lu.Username(), url)
		if dbErr != nil {
			web.JSON(c, web.ErrorResult(dbErr))
			return
		}
		if rows > 0 {
			ajax := web.Success()
			ajax.Put("imgUrl", url)
			lu.User.Avatar = model.Ptr(url)
			h.app.Tokens.SetLoginUser(ctx, lu)
			web.JSON(c, ajax)
			return
		}
	}
	web.JSON(c, web.ErrorMsg("上传图片异常，请联系管理员"))
}

// registerProfile 挂载 /system/user/profile/**。
func registerProfile(reg *router.Registry) {
	h := newProfileHandler(reg.App)

	g := reg.Authed.Group("/system/user/profile")
	g.GET("", h.Profile)
	g.PUT("", middleware.OperLog(reg.App, "个人信息", middleware.BusinessUpdate), h.UpdateProfile)
	g.PUT("/updatePwd", middleware.OperLog(reg.App, "个人信息", middleware.BusinessUpdate), h.UpdatePwd)
	g.POST("/avatar", middleware.OperLog(reg.App, "用户头像", middleware.BusinessUpdate), h.Avatar)
}

// isNotFound 对应 MyBatis 查无记录（gorm.ErrRecordNotFound）。
func isNotFound(err error) bool {
	return errors.Is(err, gorm.ErrRecordNotFound)
}
