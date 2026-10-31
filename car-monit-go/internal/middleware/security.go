// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/SecurityConfig.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/security/filter/JwtAuthenticationTokenFilter.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/service/PermissionService.java
// 类/职责: 认证/授权中间件
// 对应 Go 文件: internal/middleware/security.go
//
// DIFF: Spring Security 是过滤器链 + SpEL @PreAuthorize；Go 是 gin 中间件 + 每条路由显式挂载。
package middleware

import (
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/web"
)

// Anonymous 对应 SecurityConfig 中 permitAll/anonymous 的 URL。
// 支持前缀匹配（RuoYi 用 AntPathMatcher，这里对固定前缀做等价简化）。
var anonymousPrefixes = []string{
	"/login",
	"/register",
	"/captchaImage",
	"/common/download",
	"/system/file/view/",
	"/system/notice/view/",
	"/manager/suspicious/syncSuspiciousCarTask",
	"/profile/",
	"/swagger-ui.html",
	"/swagger-resources/",
	"/webjars/",
	"/druid/",
}

func isAnonymous(path string) bool {
	if path == "/" || strings.HasSuffix(path, ".html") || strings.HasSuffix(path, ".css") || strings.HasSuffix(path, ".js") {
		return true
	}
	for _, p := range anonymousPrefixes {
		if strings.HasPrefix(path, p) {
			return true
		}
	}
	return false
}

// Auth 对应 JwtAuthenticationTokenFilter + AuthenticationEntryPointImpl。
func Auth(a *app.App) gin.HandlerFunc {
	return func(c *gin.Context) {
		if isAnonymous(c.Request.URL.Path) {
			// 匿名路径仍尝试解析 token，便于 /common/download 等需要登录态的接口读取当前用户。
			if lu := a.Tokens.GetLoginUser(c.Request.Context(), c); lu != nil {
				auth.SetLoginUser(c, lu)
			}
			c.Next()
			return
		}
		lu := a.Tokens.GetLoginUser(c.Request.Context(), c)
		if lu == nil {
			web.RenderString(c, web.Unauthorized(c.Request.URL.RequestURI()))
			c.Abort()
			return
		}
		auth.SetLoginUser(c, lu)
		c.Next()
	}
}

// Perm 对应 @PreAuthorize("@ss.hasPermi('xxx')")。
// 支持 "*:*:*" 超级权限；多个权限之间为“任一满足”。
func Perm(perms ...string) gin.HandlerFunc {
	return func(c *gin.Context) {
		lu := auth.CurrentUser(c)
		if lu == nil {
			web.RenderString(c, web.Unauthorized(c.Request.URL.RequestURI()))
			c.Abort()
			return
		}
		for _, p := range perms {
			if lu.HasPermission(p) {
				c.Next()
				return
			}
		}
		web.RenderString(c, web.Forbidden())
		c.Abort()
	}
}
