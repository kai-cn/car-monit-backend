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
	"time"

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

// AnonymousOnly 对应 SecurityConfig 里的 anonymous() 规则（不是 permitAll）。
// Spring 的 AuthenticatedVoter 对 IS_AUTHENTICATED_ANONYMOUSLY 只在「匿名令牌」时放行：
// 带着**有效** token 的请求反而 403，而无效 token 会被 JwtAuthenticationTokenFilter 忽略、
// 按匿名放行 —— 所以判定条件是令牌能否解析出登录态，而不是有没有 Authorization 头。
//
// 这些路由挂在 reg.Engine（Auth 只挂在 reg.Authed 上），所以要自己解析一次。
func AnonymousOnly(a *app.App) gin.HandlerFunc {
	return func(c *gin.Context) {
		if a.Tokens.GetLoginUser(c.Request.Context(), c) == nil {
			c.Next()
			return
		}
		c.AbortWithStatusJSON(403, gin.H{
			"timestamp": time.Now().Format("2006-01-02T15:04:05.000-07:00"),
			"status":    403,
			"error":     "Forbidden",
			"path":      c.Request.URL.Path,
		})
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
