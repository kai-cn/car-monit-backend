// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysMenuController.java:33-170
// 类/职责: /system/menu/** 全部 HTTP 入口
// 对应 Go 文件: internal/modules/system/menu_handler.go
package system

import (
	"fmt"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/router"
	"car-monit-go/internal/web"
)

type menuHandler struct {
	app *app.App
	svc *service
}

func newMenuHandler(a *app.App, svc *service) *menuHandler {
	return &menuHandler{app: a, svc: svc}
}

// List 对应 SysMenuController.list：返回扁平列表（非树）。
func (h *menuHandler) List(c *gin.Context) {
	menus, err := h.svc.selectMenuList(c.Request.Context(), parseMenuQuery(c), auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(menus))
}

// GetInfo 对应 SysMenuController.getInfo。
func (h *menuHandler) GetInfo(c *gin.Context) {
	id, err := parseLongParam("menuId", c.Param("menuId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	menu, err := h.svc.selectMenuByID(c.Request.Context(), id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(menu))
}

// TreeSelect 对应 SysMenuController.treeselect。
func (h *menuHandler) TreeSelect(c *gin.Context) {
	menus, err := h.svc.selectMenuList(c.Request.Context(), parseMenuQuery(c), auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(buildMenuTreeSelect(menus)))
}

// RoleMenuTreeSelect 对应 SysMenuController.roleMenuTreeselect。
func (h *menuHandler) RoleMenuTreeSelect(c *gin.Context) {
	roleID, err := parseLongParam("roleId", c.Param("roleId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	menus, err := h.svc.selectMenuList(ctx, menuQuery{}, auth.CurrentUserID(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	checked, err := h.svc.selectMenuListByRoleID(ctx, roleID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ajax := web.Success()
	ajax.Put("checkedKeys", checked)
	ajax.Put("menus", buildMenuTreeSelect(menus))
	web.JSON(c, ajax)
}

// validateMenuPath 复刻“外链地址必须以 http(s):// 开头”的校验。
func validateMenuPath(b *menuBody) bool {
	if strOr(b.IsFrame) != "0" {
		return true
	}
	path := strOr(b.Path)
	return strings.HasPrefix(path, "http://") || strings.HasPrefix(path, "https://")
}

// Add 对应 SysMenuController.add。
func (h *menuHandler) Add(c *gin.Context) {
	var body menuBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	ctx := c.Request.Context()
	parentID := int64(0)
	if body.ParentID != nil {
		parentID = *body.ParentID
	}
	name := strOr(body.MenuName)
	exist, err := h.svc.checkMenuNameUnique(ctx, name, parentID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if exist != nil {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增菜单'%s'失败，菜单名称已存在", name)))
		return
	}
	if !validateMenuPath(&body) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("新增菜单'%s'失败，地址必须以http(s)://开头", name)))
		return
	}
	rows, err := h.svc.insertMenu(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Edit 对应 SysMenuController.edit。
func (h *menuHandler) Edit(c *gin.Context) {
	var body menuBody
	if err := bindBody(c, &body); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if msg := body.validate(); msg != "" {
		web.JSON(c, web.ErrorMsg(msg))
		return
	}
	if body.MenuID == nil {
		web.JSON(c, web.ErrorMsg("菜单ID不能为空"))
		return
	}
	ctx := c.Request.Context()
	parentID := int64(0)
	if body.ParentID != nil {
		parentID = *body.ParentID
	}
	name := strOr(body.MenuName)
	exist, err := h.svc.checkMenuNameUnique(ctx, name, parentID)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if exist != nil && exist.MenuID != *body.MenuID {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改菜单'%s'失败，菜单名称已存在", name)))
		return
	}
	if !validateMenuPath(&body) {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改菜单'%s'失败，地址必须以http(s)://开头", name)))
		return
	}
	if body.ParentID != nil && *body.ParentID == *body.MenuID {
		web.JSON(c, web.ErrorMsg(fmt.Sprintf("修改菜单'%s'失败，上级菜单不能选择自己", name)))
		return
	}
	rows, err := h.svc.updateMenu(ctx, &body, auth.CurrentUsername(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

// Remove 对应 SysMenuController.remove。
func (h *menuHandler) Remove(c *gin.Context) {
	id, err := parseLongParam("menuId", c.Param("menuId"))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ctx := c.Request.Context()
	child, err := h.svc.hasChildByMenuID(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if child {
		web.JSON(c, web.ErrorMsg("存在子菜单,不允许删除"))
		return
	}
	used, err := h.svc.checkMenuExistRole(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	if used {
		web.JSON(c, web.ErrorMsg("菜单已分配,不允许删除"))
		return
	}
	rows, err := h.svc.deleteMenuByID(ctx, id)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.ToAjax(rows))
}

func registerMenu(reg *router.Registry, svc *service) {
	h := newMenuHandler(reg.App, svc)
	g := reg.Authed.Group("/system/menu")

	g.GET("/list", middleware.Perm("system:menu:list"), h.List)
	g.GET("/treeselect", h.TreeSelect)
	g.GET("/roleMenuTreeselect/:roleId", h.RoleMenuTreeSelect)
	g.GET("/:menuId", middleware.Perm("system:menu:query"), h.GetInfo)
	g.POST("", middleware.Perm("system:menu:add"),
		middleware.OperLog(reg.App, "菜单管理", middleware.BusinessInsert), h.Add)
	g.PUT("", middleware.Perm("system:menu:edit"),
		middleware.OperLog(reg.App, "菜单管理", middleware.BusinessUpdate), h.Edit)
	g.DELETE("/:menuId", middleware.Perm("system:menu:remove"),
		middleware.OperLog(reg.App, "菜单管理", middleware.BusinessDelete), h.Remove)
}
