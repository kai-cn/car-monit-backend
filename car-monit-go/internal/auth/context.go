// JAVA 对照: com/ruoyi/common/utils/SecurityUtils.java
// JAVA 对照: com/ruoyi/framework/security/filter/JwtAuthenticationTokenFilter.java
// 类/职责: 登录用户上下文 — 对应 SecurityContextHolder / RequestContextHolder
// 对应 Go 文件: internal/auth/context.go
//
// DIFF: Java 把登录态放 SecurityContextHolder（ThreadLocal）；Go 放 gin.Context，
// 并由中间件显式向下传 context.Context，避免 goroutine 间串号。
package auth

import (
	"net"
	"strings"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/model"
)

const loginUserKey = "loginUser"

func SetLoginUser(c *gin.Context, lu *model.LoginUser) {
	c.Set(loginUserKey, lu)
}

func CurrentUser(c *gin.Context) *model.LoginUser {
	if v, ok := c.Get(loginUserKey); ok {
		if lu, ok := v.(*model.LoginUser); ok {
			return lu
		}
	}
	return nil
}

func CurrentUserID(c *gin.Context) int64 {
	if lu := CurrentUser(c); lu != nil {
		return lu.UserID()
	}
	return 0
}

func CurrentUsername(c *gin.Context) string {
	if lu := CurrentUser(c); lu != nil {
		return lu.Username()
	}
	return ""
}

func IsAdmin(c *gin.Context) bool {
	lu := CurrentUser(c)
	return lu != nil && lu.IsAdmin()
}

// ClientIP 对应 IpUtils.getIpAddr：优先代理头，再取 RemoteAddr。
func ClientIP(c *gin.Context) string {
	if xff := c.GetHeader("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		if ip := strings.TrimSpace(parts[0]); ip != "" {
			return ip
		}
	}
	if xri := strings.TrimSpace(c.GetHeader("X-Real-IP")); xri != "" {
		return xri
	}
	host, _, err := net.SplitHostPort(c.Request.RemoteAddr)
	if err == nil {
		return host
	}
	return c.ClientIP()
}

// UserAgent 返回请求 UA。
func UserAgent(c *gin.Context) string { return c.GetHeader("User-Agent") }
