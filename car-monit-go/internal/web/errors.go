// JAVA 对照: com/ruoyi/common/exception/ServiceException.java
// JAVA 对照: com/ruoyi/common/exception/CustomException.java
// JAVA 对照: com/ruoyi/framework/web/exception/GlobalExceptionHandler.java
// 类/职责: 业务异常 — 对应 Spring 的 RuntimeException + @RestControllerAdvice
// 对应 Go 文件: internal/web/errors.go
//
// DIFF: Java 用异常穿透 AOP；Go 用 error 返回值，HTTP 层统一转换成 AjaxResult。
package web

import (
	"errors"
	"fmt"
)

// ServiceError 对应 ServiceException（可带业务 code）。
type ServiceError struct {
	Code    *int
	Message string
	// NilMsg 对应 Java 的 AjaxResult.error(e.getMessage())：NPE 的 message 是 null，
	// 响应里 msg 键存在但值为 null，而不是空串。
	NilMsg bool
	Err    error
}

func (e *ServiceError) Error() string {
	if e.NilMsg {
		if e.Err != nil {
			return "java.lang.NullPointerException: " + e.Err.Error()
		}
		return "java.lang.NullPointerException"
	}
	if e.Err != nil {
		return e.Message + ": " + e.Err.Error()
	}
	return e.Message
}

func (e *ServiceError) Unwrap() error { return e.Err }

func NewServiceError(format string, args ...any) *ServiceError {
	return &ServiceError{Message: fmt.Sprintf(format, args...)}
}

func NewServiceErrorCode(code int, format string, args ...any) *ServiceError {
	c := code
	return &ServiceError{Code: &c, Message: fmt.Sprintf(format, args...)}
}

func WrapServiceError(err error, format string, args ...any) *ServiceError {
	return &ServiceError{Message: fmt.Sprintf(format, args...), Err: err}
}

// NewNilMessageError 对应 Java 里未捕获的 NPE：code 500、msg 为 null。
func NewNilMessageError() *ServiceError { return &ServiceError{NilMsg: true} }

// ErrorResult 把 error 转为 AjaxResult，等价 GlobalExceptionHandler 的分支：
// ServiceException 带 code 时使用业务 code，其余 500。
func ErrorResult(err error) *AjaxResult {
	var se *ServiceError
	if errors.As(err, &se) {
		if se.NilMsg {
			return ErrorNilMsg()
		}
		if se.Code != nil {
			return ErrorCode(*se.Code, se.Message)
		}
		return ErrorMsg(se.Message)
	}
	// DIFF: Java 的 RuntimeException 在 GlobalExceptionHandler 中返回 e.getMessage()，
	// Go 找不到同类兜底，统一返回 err.Error()。
	return ErrorMsg(err.Error())
}

// Forbidden 对应 AccessDeniedException 的处理（HTTP 200 + code 403）。
func Forbidden() *AjaxResult {
	return ErrorCode(StatusForbidden, "没有权限，请联系管理员授权")
}

// Unauthorized 对应 AuthenticationEntryPointImpl。
func Unauthorized(uri string) *AjaxResult {
	return ErrorCode(StatusUnauthorized, fmt.Sprintf("请求访问：%s，认证失败，无法访问系统资源", uri))
}
