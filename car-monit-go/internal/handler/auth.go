// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysLoginController.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java
// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexController.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/security/handle/LogoutSuccessHandlerImpl.java
// 类/职责: 认证相关 HTTP 入口 — /login /logout /getInfo /getRouters /captchaImage /
// 对应 Go 文件: internal/handler/auth.go
package handler

import (
	"fmt"
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/logx"
	"car-monit-go/internal/model"
	"car-monit-go/internal/service/menusvc"
	"car-monit-go/internal/web"
)

type AuthHandler struct {
	app   *app.App
	menus *menusvc.Service
}

func NewAuthHandler(a *app.App) *AuthHandler {
	return &AuthHandler{app: a, menus: menusvc.New(a.DB)}
}

// Login 对应 SysLoginController.login。
// 注意：密码策略校验在登录服务之前，返回 HTTP 200 + code 500（AjaxResult.error）。
func (h *AuthHandler) Login(c *gin.Context) {
	var body model.LoginBody
	if err := c.ShouldBindJSON(&body); err != nil {
		web.JSON(c, web.ErrorMsg("请求参数解析异常"))
		return
	}
	// JAVA 对照: CommonUtil.isNull(password) + CommonUtil.checkPassword
	password := strings.TrimSpace(body.Password)
	if auth.CheckPasswordPolicy(password) {
		web.JSON(c, web.ErrorMsg("对不起，密码长度8-20位且至少包含大写字母、小写字母、数字和特殊符号！"))
		return
	}

	token, err := h.app.Auth.Login(c.Request.Context(), body, auth.ClientIP(c), auth.UserAgent(c))
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	ajax := web.Success()
	ajax.Put("token", token)
	web.JSON(c, ajax)
}

// Logout 对应 LogoutSuccessHandlerImpl：删除 Redis 登录态并记录退出日志，始终返回成功。
func (h *AuthHandler) Logout(c *gin.Context) {
	lu := h.app.Tokens.GetLoginUser(c.Request.Context(), c)
	if lu != nil {
		h.app.Tokens.DelLoginUser(c.Request.Context(), lu.Token)
		h.app.Auth.RecordLogout(c.Request.Context(), lu.Username(), auth.ClientIP(c), auth.UserAgent(c))
	}
	web.JSON(c, web.SuccessMsg("退出成功"))
}

// GetInfo 对应 SysLoginController.getInfo。
func (h *AuthHandler) GetInfo(c *gin.Context) {
	lu := auth.CurrentUser(c)
	if lu == nil || lu.User == nil {
		web.JSON(c, web.Unauthorized(c.Request.URL.RequestURI()))
		return
	}
	ctx := c.Request.Context()
	roles := h.app.Auth.RolePermissions(ctx, lu.User)
	permissions := h.app.Auth.MenuPermissions(ctx, lu.User)

	ajax := web.Success()
	ajax.Put("user", lu.User)
	ajax.Put("roles", roles)
	ajax.Put("permissions", permissions)
	ajax.Put("pjFlag", 0)
	ajax.Put("overdue", false)
	web.JSON(c, ajax)
}

// GetRouters 对应 SysLoginController.getRouters。
func (h *AuthHandler) GetRouters(c *gin.Context) {
	userID := auth.CurrentUserID(c)
	if userID == 0 {
		userID = -9999
	}
	menus, err := h.menus.SelectMenuTreeByUserId(c.Request.Context(), userID)
	if err != nil {
		logx.WithTrace(c.Request.Context(), h.app.Log).Error("查询菜单失败", "err", err)
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	web.JSON(c, web.SuccessData(h.menus.BuildMenus(menus)))
}

// CaptchaImage 对应 CaptchaController.getCode。
func (h *AuthHandler) CaptchaImage(c *gin.Context) {
	_, uuid, img, err := h.app.Auth.Captcha(c.Request.Context())
	if err != nil {
		web.JSON(c, web.ErrorMsg(err.Error()))
		return
	}
	ajax := web.Success()
	ajax.Put("uuid", uuid)
	ajax.Put("img", img)
	web.JSON(c, ajax)
}

// Index 对应 SysIndexController.index（直接返回纯文本）。
func (h *AuthHandler) Index(c *gin.Context) {
	c.String(http.StatusOK, fmt.Sprintf("欢迎使用%s后台管理框架，请通过前端地址访问。", h.app.Cfg.RuoYi.Name))
}
