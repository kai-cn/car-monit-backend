// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysUserController.java:42-350
// 类/职责: /system/user/** 全部 HTTP 入口
// 对应 Go 文件: internal/modules/system/user_handler.go
// 关键映射:
//
//	@PreAuthorize("@ss.hasPermi('system:user:xxx')") -> middleware.Perm
//	@Log(title="用户管理", businessType=...)        -> middleware.OperLog
//	startPage()/getDataTable(list)                   -> web.Page/web.Table
//
// DIFF: Java 的 @Validated SysUser 约束在实体里全部被注释，故只有新增/重置密码的密码策略校验。
package system

import (
	"fmt"
	"strconv"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type userHandler struct {
	app *app.App
	svc *service
}

func newUserHandler(a *app.App, svc *service) *userHandler {
	return &userHandler{app: a, svc: svc}
}

// List 对应 SysUserController.list（GET /system/user/list，无 @PreAuthorize）。
func (h *userHandler) List(c *gin.Context) {
	q := parseUserQuery(c)
	q.UserType = userTypeOrg
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListAll 对应 SysUserController.listAll：固定按当前租户过滤。
func (h *userHandler) ListAll(c *gin.Context) {
	q := parseUserQuery(c)
	tenant := currentTenantID(c)
	q.TenantID = &tenant
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListTenantIdAll 对应 SysUserController.listTenantIdAll：tenantId 缺省为 -1（查不到数据）。
func (h *userHandler) ListTenantIdAll(c *gin.Context) {
	q := parseUserQuery(c)
	if q.TenantID == nil {
		v := int64(-1)
		q.TenantID = &v
	}
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListUtil 对应 SysUserController.listutil：按 flag 组装固定过滤条件。
func (h *userHandler) ListUtil(c *gin.Context) {
	q := parseUserQuery(c)
	switch q.Flag {
	case "myDept", "myDeptCg":
		q.Status = statusNormal
		q.UserType = userTypeOrg
		tenant := currentTenantID(c)
		q.TenantID = &tenant
	case "sjzbDept", "sjzbDeptCg":
		q.DataID = strconv.FormatInt(currentTenantID(c), 10)
	case "allDept":
		// 不加条件
	default:
		none := int64(-1)
		q.UserID = &none
	}
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListSameUtil 对应 SysUserController.listSameUtil：本单位同部门用户。
func (h *userHandler) ListSameUtil(c *gin.Context) {
	q := parseUserQuery(c)
	q.Status = statusNormal
	q.UserType = userTypeOrg
	tenant := currentTenantID(c)
	q.TenantID = &tenant
	dept := currentDeptID(c)
	q.DeptID = &dept
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListMy 对应 SysUserController.listMy：只查当前用户。
func (h *userHandler) ListMy(c *gin.Context) {
	q := parseUserQuery(c)
	uid := auth.CurrentUserID(c)
	q.UserID = &uid
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// ListByDept 对应 SysUserController.listByDept（GET /system/user/list/dept）。
func (h *userHandler) ListByDept(c *gin.Context) {
	q := parseUserQuery(c)
	if dept := currentDeptID(c); dept >= 0 {
		q.DeptID = &dept
	}
	// JAVA 对照: user.getExcludeSelf() != null && user.getExcludeSelf()
	if queryBool(c, "excludeSelf") {
		self := auth.CurrentUserID(c)
		q.ExcludeID = &self
	}
	q.UserType = userTypeOrg
	rows, total, err := h.svc.selectUserList(c.Request.Context(), q, web.PageAlways(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	// JAVA 对照: listByDept 查询后把 dept.deptName 回填到扁平的 deptName。
	for _, row := range rows {
		if row.Dept != nil && model.Str(row.Dept.DeptName) != "" {
			row.DeptName = row.Dept.DeptName
		}
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysUserController.export。
func (h *userHandler) Export(c *gin.Context) {
	filename, err := h.svc.exportUsers(c.Request.Context(), parseUserQuery(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// ImportTemplate 对应 SysUserController.importTemplate（登录即可，无权限点）。
func (h *userHandler) ImportTemplate(c *gin.Context) {
	filename, err := h.svc.userImportTemplate()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// ImportData 对应 SysUserController.importData。
func (h *userHandler) ImportData(c *gin.Context) {
	file, err := c.FormFile("file")
	if err != nil {
		web.JSON(c, web.ErrorMsg("导入用户数据不能为空！"))
		return
	}
	f, err := file.Open()
	if err != nil {
		web.JSON(c, web.ErrorMsg("导入Excel失败："+err.Error()))
		return
	}
	defer func() { _ = f.Close() }()
	list, err := parseUserImport(f)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	updateSupport := false
	switch strings.ToLower(strings.TrimSpace(c.PostForm("updateSupport"))) {
	case "true", "1", "on", "yes":
		updateSupport = true
	}
	msg, err := h.svc.importUser(c.Request.Context(), list, updateSupport, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(msg))
}

// MethodNotAllowed 对应 Spring 对 GET /system/user 的处理：
// HttpRequestMethodNotSupportedException -> AjaxResult.error("Request method 'GET' not supported")。
func (h *userHandler) MethodNotAllowed(c *gin.Context) {
	web.JSON(c, web.ErrorMsg("Request method 'GET' not supported"))
}

// GetInfo 对应 SysUserController.getInfo（GET /system/user、/system/user/{userId}）。
func (h *userHandler) GetInfo(c *gin.Context) {
	var userID *int64
	if raw := c.Param("userId"); raw != "" {
		id, err := parseLongParam("userId", raw)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		userID = &id
	}
	ctx := c.Request.Context()
	lu := auth.CurrentUser(c)

	roles, err := h.svc.selectRoleAll(ctx, lu)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if userID == nil || *userID != 1 {
		filtered := make([]model.SysRole, 0, len(roles))
		for _, r := range roles {
			if r.RoleID != 1 {
				filtered = append(filtered, r)
			}
		}
		roles = filtered
	}
	posts, err := h.svc.selectPostAll(ctx)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ajax := web.Success()
	ajax.Put("roles", roles)
	ajax.Put("posts", posts)
	if userID != nil {
		user, err := h.svc.selectUserByID(ctx, *userID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		postIDs, err := h.svc.selectPostListByUserID(ctx, *userID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		roleIDs, err := h.svc.selectRoleListByUserId(ctx, *userID)
		if err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
		ajax.Put(web.TagData, user)
		ajax.Put("postIds", postIDs)
		ajax.Put("roleIds", roleIDs)
	}
	web.JSON(c, ajax)
}

// Add 对应 SysUserController.add。
func (h *userHandler) Add(c *gin.Context) {
	var body userBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	userName := strOr(body.UserName)
	if res, err := h.svc.checkUserNameUnique(ctx, userName); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	} else if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增用户'%s'失败，登录账号已存在", userName)))
		return
	}
	if phone := strOr(body.Phonenumber); phone != "" {
		if res, err := h.svc.checkPhoneUnique(ctx, phone, 0); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		} else if res == notUniqueOld {
			web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增用户'%s'失败，手机号码已存在", userName)))
			return
		}
	}
	if email := strOr(body.Email); email != "" {
		if res, err := h.svc.checkEmailUnique(ctx, email, 0); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		} else if res == notUniqueOld {
			web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增用户'%s'失败，邮箱账号已存在", userName)))
			return
		}
	}
	password := strOr(body.Password)
	// JAVA 对照: CommonUtil.checkPassword —— true 表示不符合策略。
	if auth.CheckPasswordPolicy(strings.TrimSpace(password)) {
		web.JSON(c, web.ErrorMsg("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号"))
		return
	}
	enc, err := encodePassword(password)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	body.Password = &enc
	rows, err := h.svc.insertUser(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysUserController.edit。
func (h *userHandler) Edit(c *gin.Context) {
	var body userBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	userName := strOr(body.UserName)
	if body.UserID != nil {
		if err := checkUserAllowed(*body.UserID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	if phone := strOr(body.Phonenumber); phone != "" {
		if res, err := h.svc.checkPhoneUnique(ctx, phone, int64Or(body.UserID)); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		} else if res == notUniqueOld {
			web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改用户'%s'失败，手机号码已存在", userName)))
			return
		}
	}
	if email := strOr(body.Email); email != "" {
		if res, err := h.svc.checkEmailUnique(ctx, email, int64Or(body.UserID)); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		} else if res == notUniqueOld {
			web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改用户'%s'失败，邮箱账号已存在", userName)))
			return
		}
	}
	rows, err := h.svc.updateUser(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysUserController.remove。
func (h *userHandler) Remove(c *gin.Context) {
	ids, err := parseIDList(c.Param("userIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteUserByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// ResetPwd 对应 SysUserController.resetPwd。
func (h *userHandler) ResetPwd(c *gin.Context) {
	var body userBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	password := strOr(body.Password)
	if auth.CheckPasswordPolicy(strings.TrimSpace(password)) {
		web.JSON(c, web.ErrorMsg("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号"))
		return
	}
	if body.UserID != nil {
		if err := checkUserAllowed(*body.UserID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	enc, err := encodePassword(password)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	body.Password = &enc
	rows, err := h.svc.resetPwd(c.Request.Context(), &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// ChangeStatus 对应 SysUserController.changeStatus。
func (h *userHandler) ChangeStatus(c *gin.Context) {
	var body userBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if body.UserID != nil {
		if err := checkUserAllowed(*body.UserID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	rows, err := h.svc.updateUserStatus(c.Request.Context(), &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// BindUky 对应 SysUserController.bindUky：绑定唯一实体标识 / 密码卡序列号。
func (h *userHandler) BindUky(c *gin.Context) {
	var body userBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	if body.UserID == nil {
		uid := auth.CurrentUserID(c)
		body.UserID = &uid
	}
	if strOr(body.CertEntityID) == "" {
		web.JSON(c, web.ErrorMsg("唯一实体标识不能为空"))
		return
	}
	if strOr(body.CertID) == "" {
		web.JSON(c, web.ErrorMsg("密码卡/USD-Key序列号不能为空"))
		return
	}
	entity := strOr(body.CertEntityID)
	exist, _, err := h.svc.selectUserList(ctx, userQuery{CertEntityID: entity}, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(exist) > 0 && exist[0].UserID != *body.UserID {
		web.JSON(c, web.ErrorMsg("唯一实体标识已绑定，请确认！"))
		return
	}
	cert := strOr(body.CertID)
	exist, _, err = h.svc.selectUserList(ctx, userQuery{CertID: cert}, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if len(exist) > 0 && exist[0].UserID != *body.UserID {
		web.JSON(c, web.ErrorMsg("密码卡/USD-Key序列号已绑定，请确认！"))
		return
	}
	// JAVA 对照: newUser.setCertId(user.getCertId()); newUser.setCertEntityId(user.getCertEntityId());
	update := userBody{
		UserID:       body.UserID,
		CertID:       body.CertID,
		CertEntityID: body.CertEntityID,
	}
	rows, err := h.svc.updateUserStatus(ctx, &update, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// GetRoleUser 对应 SysUserController.getroleUser（按角色编码 + 当前租户查询）。
func (h *userHandler) GetRoleUser(c *gin.Context) {
	q := userQuery{RoleCode: c.Param("roleCode")}
	tenant := currentTenantID(c)
	q.TenantID = &tenant
	rows, _, err := h.svc.selectUserList(c.Request.Context(), q, web.PageDomain{})
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// CurrentUser 对应 SysUserController.selectCurrentUser。
func (h *userHandler) CurrentUser(c *gin.Context) {
	lu := auth.CurrentUser(c)
	current, err := h.svc.selectCurrentUser(c.Request.Context(), lu)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(current))
}

// registerUser 挂载 /system/user/**。
func registerUser(reg *router.Registry, svc *service) {
	h := newUserHandler(reg.App, svc)
	g := reg.Authed.Group("/system/user")

	g.GET("/list", h.List)
	g.GET("/listAll", h.ListAll)
	g.GET("/listTenantIdAll", h.ListTenantIdAll)
	g.GET("/listutil", h.ListUtil)
	g.GET("/listSameUtil", h.ListSameUtil)
	g.GET("/listMy", h.ListMy)
	g.GET("/list/dept", h.ListByDept)

	g.GET("/export", middleware.Perm("system:user:export"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessExport), h.Export)
	g.GET("/importTemplate", h.ImportTemplate)
	g.POST("/importData", middleware.Perm("system:user:import"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessImport), h.ImportData)

	g.GET("/currentUser", h.CurrentUser)
	g.GET("/getroleUser/:roleCode", h.GetRoleUser)
	g.GET("/:userId", middleware.Perm("system:user:query"), h.GetInfo)
	// JAVA 对照: SysUserController:174 @GetMapping(value = {"/", "/{userId}"})
	// 前端新增用户表单走 getUser('') -> GET /system/user/（带斜杠），缺它就无法取 roles/posts。
	g.GET("/", middleware.Perm("system:user:query"), h.GetInfo)
	// 精确路径 /system/user 在 Java 只注册了 POST/PUT，GET 会命中 Spring 的
	// HttpRequestMethodNotSupportedException，被 GlobalExceptionHandler 包成 500。
	g.GET("", h.MethodNotAllowed)

	g.POST("", middleware.Perm("system:user:add"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:user:edit"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessUpdate), h.Edit)
	g.PUT("/resetPwd", middleware.Perm("system:user:resetPwd"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessUpdate), h.ResetPwd)
	g.PUT("/changeStatus", middleware.Perm("system:user:edit"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessUpdate), h.ChangeStatus)
	g.PUT("/bindUky", h.BindUky)
	g.DELETE("/:userIds", middleware.Perm("system:user:remove"),
		middleware.OperLog(reg.App, "用户管理", middleware.BusinessDelete), h.Remove)
}
