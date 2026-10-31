// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysRoleController.java:39-190
// 类/职责: /system/role/** 全部 HTTP 入口
// 对应 Go 文件: internal/modules/system/role_handler.go
package system

import (
	"fmt"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type roleHandler struct {
	app *app.App
	svc *service
}

func newRoleHandler(a *app.App, svc *service) *roleHandler {
	return &roleHandler{app: a, svc: svc}
}

// validateRole 对应 SysRole 上的 @Validated 约束。
func validateRole(b *roleBody) string {
	switch {
	case strOr(b.RoleName) == "":
		return "角色名称不能为空"
	case len([]rune(strOr(b.RoleName))) > 30:
		return "角色名称长度不能超过30个字符"
	case strOr(b.RoleKey) == "":
		return "权限字符不能为空"
	case len([]rune(strOr(b.RoleKey))) > 100:
		return "权限字符长度不能超过100个字符"
	case strOr(b.RoleSort) == "":
		return "显示顺序不能为空"
	}
	return ""
}

// List 对应 SysRoleController.list（@PreAuthorize 被注释，登录即可）。
func (h *roleHandler) List(c *gin.Context) {
	rows, total, err := h.svc.selectRoleListPaged(c.Request.Context(), parseRoleQuery(c), auth.CurrentUser(c), web.Page(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Table(rows, total))
}

// Export 对应 SysRoleController.export。
func (h *roleHandler) Export(c *gin.Context) {
	filename, err := h.svc.exportRoles(c.Request.Context(), parseRoleQuery(c), auth.CurrentUser(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessMsg(filename))
}

// GetInfo 对应 SysRoleController.getInfo。
func (h *roleHandler) GetInfo(c *gin.Context) {
	id, err := parseLongParam("roleId", c.Param("roleId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	role, err := h.svc.selectRoleByID(c.Request.Context(), id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(role))
}

// Add 对应 SysRoleController.add。
func (h *roleHandler) Add(c *gin.Context) {
	var body roleBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := validateRole(&body); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	res, err := h.svc.checkRoleNameUnique(ctx, strOr(body.RoleName), int64Or(body.RoleID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增角色'%s'失败，角色名称已存在", strOr(body.RoleName))))
		return
	}
	res, err = h.svc.checkRoleKeyUnique(ctx, strOr(body.RoleKey), int64Or(body.RoleID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增角色'%s'失败，角色权限已存在", strOr(body.RoleName))))
		return
	}
	rows, err := h.svc.insertRole(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysRoleController.edit（含更新后刷新当前登录用户权限缓存）。
func (h *roleHandler) Edit(c *gin.Context) {
	var body roleBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := validateRole(&body); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	if body.RoleID != nil {
		if err := checkRoleAllowed(*body.RoleID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	ctx := c.Request.Context()
	res, err := h.svc.checkRoleNameUnique(ctx, strOr(body.RoleName), int64Or(body.RoleID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改角色'%s'失败，角色名称已存在", strOr(body.RoleName))))
		return
	}
	res, err = h.svc.checkRoleKeyUnique(ctx, strOr(body.RoleKey), int64Or(body.RoleID))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if res == notUniqueOld {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改角色'%s'失败，角色权限已存在", strOr(body.RoleName))))
		return
	}
	rows, err := h.svc.updateRole(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if rows > 0 {
		// JAVA 对照: 更新缓存用户权限（仅非管理员）。
		if lu := auth.CurrentUser(c); lu != nil && lu.User != nil && !lu.User.IsAdmin() {
			lu.Permissions = h.app.Auth.MenuPermissions(ctx, lu.User)
			if user, err := h.svc.selectUserByUserName(ctx, model.Str(lu.User.UserName)); err == nil && user != nil {
				lu.User = user
			}
			h.app.Tokens.SetLoginUser(ctx, lu)
		}
		web.JSON(c, web.Success())
		return
	}
	web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改角色'%s'失败，请联系管理员", strOr(body.RoleName))))
}

// DataScope 对应 SysRoleController.dataScope。
func (h *roleHandler) DataScope(c *gin.Context) {
	var body roleBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if body.RoleID != nil {
		if err := checkRoleAllowed(*body.RoleID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	rows, err := h.svc.authDataScope(c.Request.Context(), &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// ChangeStatus 对应 SysRoleController.changeStatus。
func (h *roleHandler) ChangeStatus(c *gin.Context) {
	var body roleBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if body.RoleID != nil {
		if err := checkRoleAllowed(*body.RoleID); err != nil {
			web.JSON(c, web.ErrorResult(err))
			return
		}
	}
	rows, err := h.svc.updateRoleStatus(c.Request.Context(), &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysRoleController.remove。
func (h *roleHandler) Remove(c *gin.Context) {
	ids, err := parseIDList(c.Param("roleIds"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	rows, err := h.svc.deleteRoleByIDs(c.Request.Context(), ids)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// OptionSelect 对应 SysRoleController.optionselect（数据权限过滤后的角色下拉）。
func (h *roleHandler) OptionSelect(c *gin.Context) {
	rows, err := h.svc.selectRoleAll(c.Request.Context(), auth.CurrentUser(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

// SelectList 对应 SysRoleController.selectlist（无权限点，不抛业务异常）。
func (h *roleHandler) SelectList(c *gin.Context) {
	rows, err := h.svc.selectRoleList(c.Request.Context(), parseRoleQuery(c), auth.CurrentUser(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(rows))
}

func registerRole(reg *router.Registry, svc *service) {
	h := newRoleHandler(reg.App, svc)
	g := reg.Authed.Group("/system/role")

	g.GET("/list", h.List)
	g.GET("/export", middleware.Perm("system:role:export"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessExport), h.Export)
	g.GET("/optionselect", middleware.Perm("system:role:query"), h.OptionSelect)
	g.GET("/selectlist", h.SelectList)
	g.GET("/:roleId", middleware.Perm("system:role:query"), h.GetInfo)
	g.POST("", middleware.Perm("system:role:add"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:role:edit"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessUpdate), h.Edit)
	g.PUT("/dataScope", middleware.Perm("system:role:edit"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessUpdate), h.DataScope)
	g.PUT("/changeStatus", middleware.Perm("system:role:edit"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessUpdate), h.ChangeStatus)
	g.DELETE("/:roleIds", middleware.Perm("system:role:remove"),
		middleware.OperLog(reg.App, "角色管理", middleware.BusinessDelete), h.Remove)
}
