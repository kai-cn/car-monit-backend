// JAVA 对照: ruoyi-admin/.../monitor/SysUserOnlineController.java
// JAVA 对照: ruoyi-system/.../service/impl/SysUserOnlineServiceImpl.java
// 类/职责: 在线用户 — 列表（扫描 login_tokens:*）/ 强退
// 对应 Go 文件: internal/modules/ops/online.go
//
// DIFF: Java 用 RedisCache.keys("login_tokens:*") 后逐个 getCacheObject；Go 同样用
// KEYS + JSON 反序列化。KEYS 在大库上有阻塞风险，Java 侧本来就是这样，保持一致。
// DIFF: Java 用 Collections.reverse 反转结果；Redis KEYS 的顺序本身不保证稳定，这里同样反转。
package ops

import (
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

type onlineHandler struct {
	app *app.App
}

// List 对应 GET /monitor/online/list?ipaddr=&userName=。
func (h *onlineHandler) List(c *gin.Context) {
	ipaddr := c.Query("ipaddr")
	userName := c.Query("userName")
	ctx := c.Request.Context()

	keys, err := h.app.Redis.Keys(ctx, auth.LoginTokenKey+"*").Result()
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}

	list := make([]*model.SysUserOnline, 0, len(keys))
	for _, key := range keys {
		var lu model.LoginUser
		if !h.app.Cache.Get(ctx, key, &lu) {
			continue
		}
		// JAVA 对照: StringUtils.isNotEmpty / isNotNull 的短路判断顺序。
		ipMatch := ipaddr != "" && strings.EqualFold(ipaddr, lu.IPAddr)
		nameMatch := lu.Username() != "" && strings.EqualFold(userName, lu.Username())
		switch {
		case ipaddr != "" && userName != "":
			if ipMatch && nameMatch {
				list = append(list, loginUserToOnline(&lu))
			}
		case ipaddr != "":
			if ipMatch {
				list = append(list, loginUserToOnline(&lu))
			}
		case userName != "" && lu.User != nil:
			if nameMatch {
				list = append(list, loginUserToOnline(&lu))
			}
		default:
			list = append(list, loginUserToOnline(&lu))
		}
	}

	// Java: Collections.reverse + removeAll(singleton(null))。
	for i, j := 0, len(list)-1; i < j; i, j = i+1, j-1 {
		list[i], list[j] = list[j], list[i]
	}
	out := make([]*model.SysUserOnline, 0, len(list))
	for _, item := range list {
		if item != nil {
			out = append(out, item)
		}
	}
	// 在线用户不分页，getDataTable(list) 的 total 即集合长度。
	web.JSON(c, web.Table(out, int64(len(out))))
}

// ForceLogout 对应 DELETE /monitor/online/{tokenId}：删除 login_tokens:<tokenId>。
func (h *onlineHandler) ForceLogout(c *gin.Context) {
	tokenID := c.Param("tokenId")
	if err := h.app.Redis.Del(c.Request.Context(), auth.LoginTokenKey+tokenID).Err(); err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.Success())
}

// loginUserToOnline 对应 SysUserOnlineServiceImpl.loginUserToUserOnline。
func loginUserToOnline(lu *model.LoginUser) *model.SysUserOnline {
	if lu == nil || lu.User == nil {
		return nil
	}
	out := &model.SysUserOnline{
		TokenID:       lu.Token,
		SessionID:     lu.SessionID,
		UserName:      lu.Username(),
		IPAddr:        lu.IPAddr,
		LoginLocation: lu.LoginLocation,
		Browser:       lu.Browser,
		OS:            lu.OS,
		LoginTime:     lu.LoginTime,
	}
	if lu.User.Dept != nil {
		out.DeptName = model.Str(lu.User.Dept.DeptName)
	} else {
		out.DeptName = model.Str(lu.User.DeptName)
	}
	return out
}

// newOnlineRoutes 注册 /monitor/online/**。
func newOnlineRoutes(reg gin.IRouter, a *app.App) {
	h := &onlineHandler{app: a}
	g := reg.Group("/monitor/online")
	g.GET("/list", middleware.Perm("monitor:online:list"), h.List)
	g.DELETE("/:tokenId", middleware.Perm("monitor:online:forceLogout"),
		middleware.OperLog(a, "在线用户", middleware.BusinessForce), h.ForceLogout)
}
