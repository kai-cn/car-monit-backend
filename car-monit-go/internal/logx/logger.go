// JAVA 对照: ruoyi-admin/src/main/resources/logback.xml
// 类/职责: 日志 — 对应 SLF4J + Logback
// 对应 Go 文件: internal/logx/logger.go
// 关键映射: LoggerFactory.getLogger -> slog.New；MDC -> context.Context 中的 trace 字段
//
// DIFF: Go 标准库 log/slog 没有 logback.xml 式外部配置文件；
// 级别在这里由 application.yml 的 logging.level 段推导。
package logx

import (
	"context"
	"log/slog"
	"os"
	"strings"

	"car-monit-go/internal/config"
)

type ctxKey struct{}

// New 根据 logging.level 创建 slog.Logger。
// 多个 logger 配置时取最详细级别：debug/trace > info > warn > error。
func New(cfg *config.Config) *slog.Logger {
	seen := make(map[string]bool)
	collectLevels(cfg.Logging.Level, seen)
	level := slog.LevelInfo
	switch {
	case seen["debug"] || seen["trace"]:
		level = slog.LevelDebug
	case seen["warn"]:
		level = slog.LevelWarn
	case seen["error"]:
		level = slog.LevelError
	}
	h := slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{Level: level})
	return slog.New(h)
}

// collectLevels 递归展开 Viper 对含点号键（com.ruoyi）生成的嵌套 map。
func collectLevels(v any, seen map[string]bool) {
	switch t := v.(type) {
	case map[string]any:
		for _, vv := range t {
			collectLevels(vv, seen)
		}
	case map[any]any:
		for _, vv := range t {
			collectLevels(vv, seen)
		}
	case string:
		seen[strings.ToLower(strings.TrimSpace(t))] = true
	}
}

// WithTrace 把 traceId 注入日志上下文。
// JAVA 对照: TraceContext / TraceIdFilter（MDC.put("traceId", ...)）
func WithTrace(ctx context.Context, logger *slog.Logger) *slog.Logger {
	if v, ok := ctx.Value(ctxKey{}).(string); ok && v != "" {
		return logger.With("traceId", v)
	}
	return logger
}

// ContextWithTrace 保存 traceId，供日志与下游调用读取。
func ContextWithTrace(ctx context.Context, traceID string) context.Context {
	return context.WithValue(ctx, ctxKey{}, traceID)
}

// TraceFromContext 读取 traceId。
func TraceFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(ctxKey{}).(string); ok {
		return v
	}
	return ""
}
