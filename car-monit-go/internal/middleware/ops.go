// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/RateLimiterAspect.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java
// 类/职责: 防重复提交 / 限流 / 操作日志
// 对应 Go 文件: internal/middleware/ops.go
//
// DIFF: Java 通过 @RepeatSubmit / @RateLimiter / @Log 注解 + AOP 生效；
// Go 在路由注册处显式挂载中间件，语义一一对应。
//
// DIFF: LogAspect 在 Java 里由 AsyncManager 线程池异步落库，且对 MultipartFile / 文件响应
// 显式跳过内容采集；Go 侧原来为每个请求起一个 goroutine 并把完整响应体复制进内存，
// 在 59 条导出路由上会把峰值内存放大 2~3 倍。现在改为：
//  1. 固定 worker 池 + 有界队列（进程内单例，绑定第一个 App）；
//  2. 响应体只在 Content-Type 为 JSON 且未超过上限时采集；
//  3. 请求体跳过 multipart，非 multipart 也只读取前 operLogBodyLimit 字节再拼回。
package middleware

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"log/slog"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"gorm.io/gorm"

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

// operLogBodyLimit 对应 LogAspect 的 StringUtils.substring(x, 0, 2000)：
// 请求参数与响应体最多各留 2000 字节，超过后不再继续缓冲。
const operLogBodyLimit = 2000

// operLogQueueSize / operLogWorkers 是异步落库的队列与并发度。
// 队列满时丢弃并告警——审计日志不能让业务请求阻塞或 OOM。
const (
	operLogQueueSize = 1024
	operLogWorkers   = 2
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

// repeatSubmitBodyLimit 是防重摘要读取请求体的上限。
// Java 里 request.getInputStream() 被包装后整体参与摘要；这里上限取 1MB，
// 超过部分不参与摘要（仅影响超大请求的重复提交判定，不改变正常请求语义）。
const repeatSubmitBodyLimit = 1 << 20

func requestParams(c *gin.Context) string {
	var body []byte
	if c.Request.Body != nil && !isMultipartRequest(c) {
		limited := io.LimitReader(c.Request.Body, repeatSubmitBodyLimit)
		body, _ = io.ReadAll(limited)
		c.Request.Body = io.NopCloser(io.MultiReader(bytes.NewReader(body), c.Request.Body))
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

// operLogWriter 只在响应是 JSON 时缓冲前 operLogBodyLimit 字节。
// 导出接口返回 octet-stream / xlsx，会直接透传、不复制内容。
type operLogWriter struct {
	gin.ResponseWriter
	buf      bytes.Buffer
	overflow bool
}

func (w *operLogWriter) Write(b []byte) (int, error) {
	w.capture(b)
	return w.ResponseWriter.Write(b)
}

func (w *operLogWriter) WriteString(s string) (int, error) {
	w.capture([]byte(s))
	return w.ResponseWriter.WriteString(s)
}

func (w *operLogWriter) capture(b []byte) {
	if w.overflow {
		return
	}
	if w.buf.Len()+len(b) > operLogBodyLimit {
		// 超过上限后立即放弃缓冲，避免导出/大响应被整份复制。
		w.overflow = true
		w.buf.Reset()
		return
	}
	w.buf.Write(b)
}

// body 返回可落库的响应文本：非 JSON（文件流）或超限时给空串。
func (w *operLogWriter) body(contentType string) string {
	if w.overflow || !strings.Contains(strings.ToLower(contentType), "json") {
		return ""
	}
	return w.buf.String()
}

// OperLog 对应 @Log(title, businessType)：请求结束后异步写 sys_oper_log。
func OperLog(a *app.App, title string, businessType int) gin.HandlerFunc {
	sink := operLogSinkFor(a)
	return func(c *gin.Context) {
		start := time.Now()
		params := readBodyForLog(c)
		bw := &operLogWriter{ResponseWriter: c.Writer}
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
		result := bw.body(c.Writer.Header().Get("Content-Type"))
		status := 0
		errMsg := ""
		if c.Writer.Status() >= 400 || strings.Contains(result, `"code":500`) {
			status = 1
			errMsg = result
		}
		if len(result) > operLogBodyLimit {
			result = result[:operLogBodyLimit]
		}
		if len(errMsg) > operLogBodyLimit {
			errMsg = errMsg[:operLogBodyLimit]
		}
		if len(params) > operLogBodyLimit {
			params = params[:operLogBodyLimit]
		}
		sink.Submit(operLogEntry{
			Title:         title,
			BusinessType:  businessType,
			Method:        c.Request.Method + " " + c.Request.URL.Path,
			RequestMethod: c.Request.Method,
			OperatorType:  1, // OperatorType.MANAGE
			OperName:      userName,
			DeptName:      deptName,
			OperURL:       c.Request.URL.Path,
			OperIP:        auth.ClientIP(c),
			OperParam:     params,
			JSONResult:    result,
			Status:        status,
			ErrorMsg:      errMsg,
			OperTime:      start,
		})
	}
}

// ---------------------------------------------------------------------------
// 异步落库：固定 worker 池 + 有界队列
// ---------------------------------------------------------------------------

type operLogEntry struct {
	Title         string
	BusinessType  int
	Method        string
	RequestMethod string
	OperatorType  int
	OperName      string
	DeptName      string
	OperURL       string
	OperIP        string
	OperParam     string
	JSONResult    string
	Status        int
	ErrorMsg      string
	OperTime      time.Time
}

type operLogSink struct {
	db  *gorm.DB
	log *slog.Logger

	mu     sync.RWMutex
	closed bool
	ch     chan operLogEntry
	wg     sync.WaitGroup
}

func newOperLogSink(db *gorm.DB, log *slog.Logger) *operLogSink {
	s := &operLogSink{
		db:  db,
		log: log,
		ch:  make(chan operLogEntry, operLogQueueSize),
	}
	s.wg.Add(operLogWorkers)
	for i := 0; i < operLogWorkers; i++ {
		go s.worker()
	}
	return s
}

func (s *operLogSink) worker() {
	defer s.wg.Done()
	for entry := range s.ch {
		s.write(entry)
	}
}

func (s *operLogSink) write(entry operLogEntry) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	const sqlText = `insert into sys_oper_log
		(title, business_type, method, request_method, operator_type, oper_name, dept_name,
		 oper_url, oper_ip, oper_location, oper_param, json_result, status, error_msg, oper_time)
		values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`
	if err := s.db.WithContext(ctx).Exec(sqlText,
		entry.Title, entry.BusinessType, entry.Method, entry.RequestMethod,
		entry.OperatorType, entry.OperName, entry.DeptName, entry.OperURL,
		entry.OperIP, "", entry.OperParam, entry.JSONResult,
		entry.Status, entry.ErrorMsg, entry.OperTime).Error; err != nil {
		s.log.Warn("写入操作日志失败", "err", err)
	}
}

// Submit 入队；队列满时丢弃并告警，绝不阻塞业务请求。
func (s *operLogSink) Submit(entry operLogEntry) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if s.closed {
		return
	}
	select {
	case s.ch <- entry:
	default:
		s.log.Warn("操作日志队列已满，丢弃本条记录", "url", entry.OperURL)
	}
}

// Stop 关闭队列并等待在途日志写完（优雅停机用）。
func (s *operLogSink) Stop(ctx context.Context) {
	s.mu.Lock()
	if s.closed {
		s.mu.Unlock()
		return
	}
	s.closed = true
	close(s.ch)
	s.mu.Unlock()

	done := make(chan struct{})
	go func() {
		s.wg.Wait()
		close(done)
	}()
	select {
	case <-done:
	case <-ctx.Done():
	}
}

var (
	operLogSinkOnce sync.Once
	operLogSinkInst *operLogSink
)

// operLogSinkFor 返回进程内唯一的操作日志 sink（懒加载）。
// DIFF: Java 的 AsyncManager 是 Spring 单例；Go 侧进程只有一个 App，因此用 sync.Once 绑定首个实例。
func operLogSinkFor(a *app.App) *operLogSink {
	operLogSinkOnce.Do(func() {
		operLogSinkInst = newOperLogSink(a.DB, a.Log)
	})
	return operLogSinkInst
}

// StopOperLog 在优雅停机时排空操作日志队列。
func StopOperLog(ctx context.Context) {
	if operLogSinkInst != nil {
		operLogSinkInst.Stop(ctx)
	}
}

// readBodyForLog 采集 @Log 的 operParam：multipart 直接跳过（Java 也过滤 MultipartFile），
// 其余只读取前 operLogBodyLimit 字节，并把未读部分拼回请求体。
func readBodyForLog(c *gin.Context) string {
	if c.Request.Body == nil || isMultipartRequest(c) {
		return c.Request.URL.RawQuery
	}
	limited := io.LimitReader(c.Request.Body, operLogBodyLimit)
	body, _ := io.ReadAll(limited)
	c.Request.Body = io.NopCloser(io.MultiReader(bytes.NewReader(body), c.Request.Body))
	if len(body) == 0 {
		return c.Request.URL.RawQuery
	}
	return string(body)
}

func isMultipartRequest(c *gin.Context) bool {
	return strings.HasPrefix(strings.ToLower(c.GetHeader("Content-Type")), "multipart/")
}
