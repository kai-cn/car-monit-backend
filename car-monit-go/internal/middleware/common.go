// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/core/filter/TraceIdFilter.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ResourcesConfig.java (CORS)
// JAVA 对照: ruoyi-common/src/main/java/com/ruoyi/common/filter/XssFilter.java
// 类/职责: 通用中间件 — TraceId / 异常兜底 / CORS / XSS
// 对应 Go 文件: internal/middleware/common.go
package middleware

import (
	"net/http"
	"runtime/debug"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"car-monit-go/internal/app"
	"car-monit-go/internal/logx"
	"car-monit-go/internal/web"
)

// TraceID 对应 TraceIdFilter：读取/生成 X-Trace-Id 并写入日志上下文。
func TraceID(a *app.App) gin.HandlerFunc {
	header := a.Cfg.Monitor.TraceIDHeader
	if header == "" {
		header = "X-Trace-Id"
	}
	return func(c *gin.Context) {
		id := c.GetHeader(header)
		if id == "" {
			id = uuid.NewString()
		}
		c.Header(header, id)
		c.Set("traceId", id)
		c.Request = c.Request.WithContext(logx.ContextWithTrace(c.Request.Context(), id))
		c.Next()
	}
}

// Recovery 对应 GlobalExceptionHandler 的 RuntimeException/Exception 分支。
func Recovery(a *app.App) gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if r := recover(); r != nil {
				a.Log.Error("请求发生未知异常", "panic", r, "path", c.Request.URL.Path, "stack", string(debug.Stack()))
				if !c.Writer.Written() {
					web.RenderString(c, web.ErrorMsg("系统异常"))
				}
				c.Abort()
			}
		}()
		c.Next()
	}
}

// CORS 对应 ResourcesConfig 注册的 CorsFilter。
func CORS() gin.HandlerFunc {
	return func(c *gin.Context) {
		origin := c.GetHeader("Origin")
		if origin != "" {
			c.Header("Access-Control-Allow-Origin", origin)
			c.Header("Access-Control-Allow-Credentials", "true")
			c.Header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS,PATCH")
			c.Header("Access-Control-Allow-Headers", "Authorization,Content-Type,X-Requested-With,X-Trace-Id,Accept,Origin")
			c.Header("Access-Control-Expose-Headers", "Authorization,Content-Disposition,X-Trace-Id")
			c.Header("Access-Control-Max-Age", "3600")
		}
		if c.Request.Method == http.MethodOptions {
			c.AbortWithStatus(http.StatusNoContent)
			return
		}
		c.Next()
	}
}

// XSS 对应 XssFilter：仅对 urlPatterns 命中的路径清理请求参数中的 HTML。
// DIFF: Java 包装 HttpServletRequest 过滤 parameter；Go 侧重建 query string，
// 请求体（JSON）与 Java 一致不做 HTML 转义。
func XSS(a *app.App) gin.HandlerFunc {
	if !a.Cfg.Xss.Enabled {
		return func(c *gin.Context) { c.Next() }
	}
	patterns := splitPatterns(a.Cfg.Xss.URLPatterns)
	excludes := splitPatterns(a.Cfg.Xss.Excludes)
	return func(c *gin.Context) {
		path := c.Request.URL.Path
		if !matchAny(path, patterns) || matchAny(path, excludes) {
			c.Next()
			return
		}
		q := c.Request.URL.Query()
		changed := false
		for k, vals := range q {
			for i, v := range vals {
				cleaned := cleanXSS(v)
				if cleaned != v {
					vals[i] = cleaned
					changed = true
				}
			}
			q[k] = vals
		}
		if changed {
			c.Request.URL.RawQuery = q.Encode()
		}
		c.Next()
	}
}

// NoRoute 对应 Spring 的默认 404 响应。
func NoRoute(c *gin.Context) {
	c.JSON(http.StatusNotFound, gin.H{
		"timestamp": web.FormatNow(),
		"status":    http.StatusNotFound,
		"error":     "Not Found",
		"path":      c.Request.URL.Path,
	})
}

func splitPatterns(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			out = append(out, p)
		}
	}
	return out
}

// matchAny 支持 RuoYi 使用的前缀通配 "/system/*"。
func matchAny(path string, patterns []string) bool {
	for _, p := range patterns {
		if strings.HasSuffix(p, "*") {
			if strings.HasPrefix(path, strings.TrimSuffix(p, "*")) {
				return true
			}
			continue
		}
		if path == p {
			return true
		}
	}
	return false
}

func cleanXSS(v string) string {
	replacer := strings.NewReplacer(
		"<", "&lt;",
		">", "&gt;",
		`"`, "&quot;",
		"'", "&#39;",
		"(", "&#40;",
		")", "&#41;",
	)
	return replacer.Replace(v)
}
