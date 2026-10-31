// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/RateLimiterAspect.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java
// 类/职责: 防重复提交 / 限流 / 操作日志
// 对应 Go 文件: internal/middleware/ops.go
//
// DIFF: Java 通过 @RepeatSubmit / @RateLimiter / @Log 注解 + AOP 生效；
// Go 在路由注册处显式挂载中间件，语义一一对应。
package middleware

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"car-monit-go/internal/app"
	"car-monit-go/internal/auth"
	"car-monit-go/internal/model"
	"car-monit-go/internal/web"
)

// 对应 com.ruoyi.common.enums.BusinessType
const (
	BusinessOther   = 0
	BusinessInsert  = 1
	BusinessUpdate  = 2
	BusinessDelete  = 3
	BusinessGrant   = 4
	BusinessExport  = 5
	BusinessImport  = 6
	BusinessForce   = 7
	BusinessGenCode = 8
	BusinessClean   = 9
)

type repeatEntry struct {
	Params string `json:"params"`
	Time   int64  `json:"time"`
}

// RepeatSubmit 对应 @RepeatSubmit(interval)。默认 interval=5000ms。
func RepeatSubmit(a *app.App, interval time.Duration) gin.HandlerFunc {
	if interval <= 0 {
		interval = 5 * time.Second
	}
	return func(c *gin.Context) {
		if c.Request.Method != "POST" && c.Request.Method != "PUT" {
			c.Next()
			return
		}
		params := requestParams(c)
		key := auth.RepeatSubmitKey + c.Request.URL.Path + strings.TrimSpace(c.GetHeader(a.Cfg.Token.Header))
		var prev repeatEntry
		if a.Cache.Get(c.Request.Context(), key, &prev) {
			same := prev.Params == params
			within := time.Now().UnixMilli()-prev.Time < interval.Milliseconds()
			if same && within {
				web.RenderString(c, web.ErrorMsg("不允许重复提交，请稍后再试"))
				c.Abort()
				return
			}
		}
		_ = a.Cache.Set(c.Request.Context(), key, repeatEntry{Params: params, Time: time.Now().UnixMilli()}, interval)
		c.Next()
	}
}

func requestParams(c *gin.Context) string {
	var body []byte
	if c.Request.Body != nil {
		body, _ = io.ReadAll(c.Request.Body)
		c.Request.Body = io.NopCloser(bytes.NewReader(body))
	}
	var b strings.Builder
	b.WriteString(c.Request.URL.RawQuery)
	b.WriteByte('|')
	b.Write(body)
	sum := sha256.Sum256([]byte(b.String()))
	return hex.EncodeToString(sum[:])
}

// RateLimit 对应 @RateLimiter(time, count)：固定窗口计数（Redis INCR）。
func RateLimit(a *app.App, keyPrefix string, seconds, count int) gin.HandlerFunc {
	if seconds <= 0 {
		seconds = 60
	}
	return func(c *gin.Context) {
		key := fmt.Sprintf("%s%s:%s:%s", auth.RateLimitKey, keyPrefix, auth.ClientIP(c), c.Request.URL.Path)
		n, err := a.Cache.Incr(c.Request.Context(), key, time.Duration(seconds)*time.Second)
		if err != nil {
			web.RenderString(c, web.ErrorMsg("服务器限流异常，请稍候再试"))
			c.Abort()
			return
		}
		if n > int64(count) {
			web.RenderString(c, web.ErrorMsg("访问过于频繁，请稍候再试"))
			c.Abort()
			return
		}
		c.Next()
	}
}

type bodyWriter struct {
	gin.ResponseWriter
	buf bytes.Buffer
}

func (w *bodyWriter) Write(b []byte) (int, error) {
	w.buf.Write(b)
	return w.ResponseWriter.Write(b)
}

func (w *bodyWriter) WriteString(s string) (int, error) {
	w.buf.WriteString(s)
	return w.ResponseWriter.WriteString(s)
}

// OperLog 对应 @Log(title, businessType)：请求结束后异步写 sys_oper_log。
func OperLog(a *app.App, title string, businessType int) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		params := readBodyForLog(c)
		bw := &bodyWriter{ResponseWriter: c.Writer}
		c.Writer = bw
		c.Next()

		lu := auth.CurrentUser(c)
		userName, deptName := "", ""
		if lu != nil {
			userName = lu.Username()
			if lu.User != nil {
				deptName = model.Str(lu.User.DeptName)
			}
		}
		status := 0
		errMsg := ""
		if c.Writer.Status() >= 400 || strings.Contains(bw.buf.String(), `"code":500`) {
			status = 1
			errMsg = bw.buf.String()
		}
		result := bw.buf.String()
		if len(result) > 2000 {
			result = result[:2000]
		}
		entry := map[string]any{
			"title":          title,
			"business_type":  businessType,
			"method":         c.Request.Method + " " + c.Request.URL.Path,
			"request_method": c.Request.Method,
			"operator_type":  1,
			"oper_name":      userName,
			"dept_name":      deptName,
			"oper_url":       c.Request.URL.Path,
			"oper_ip":        auth.ClientIP(c),
			"oper_location":  "",
			"oper_param":     params,
			"json_result":    result,
			"status":         status,
			"error_msg":      errMsg,
			"oper_time":      time.Now(),
		}
		cost := time.Since(start).Milliseconds()
		_ = cost
		go func() {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			sql := `insert into sys_oper_log
				(title, business_type, method, request_method, operator_type, oper_name, dept_name,
				 oper_url, oper_ip, oper_location, oper_param, json_result, status, error_msg, oper_time)
				values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
			if err := a.DB.WithContext(ctx).Exec(sql,
				entry["title"], entry["business_type"], entry["method"], entry["request_method"],
				entry["operator_type"], entry["oper_name"], entry["dept_name"], entry["oper_url"],
				entry["oper_ip"], entry["oper_location"], entry["oper_param"], entry["json_result"],
				entry["status"], entry["error_msg"], entry["oper_time"]).Error; err != nil {
				a.Log.Warn("写入操作日志失败", "err", err)
			}
		}()
	}
}

func readBodyForLog(c *gin.Context) string {
	if c.Request.Body == nil {
		return c.Request.URL.RawQuery
	}
	body, _ := io.ReadAll(c.Request.Body)
	c.Request.Body = io.NopCloser(bytes.NewReader(body))
	s := string(body)
	if len(s) > 2000 {
		s = s[:2000]
	}
	return s
}
