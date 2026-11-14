package com.ruoyi.common.core.exception;

import com.ruoyi.common.core.domain.MonitorResponse;
import com.ruoyi.common.core.monitor.AlertEngine;
import com.ruoyi.common.core.context.TraceContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.servlet.NoHandlerFoundException;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.List;
import java.util.Set;

/**
 * 全局异常处理器（增强版）
 * <p>
 * 【设计目的】
 * 1. 统一捕获系统中所有未被业务代码catch的异常
 * 2. 将异常转换为统一的 MonitorResponse 格式返回给前端
 * 3. 自动触发告警（对严重级别异常），并记录完整堆栈
 * 4. 携带TraceId，便于在日志系统中追溯问题
 * </p>
 *
 * <p>【异常分类与处理策略】</p>
 * <pre>
 * ┌────────────────────────────┬──────────┬──────────┐
 * │ 异常类型                    │ HTTP码   │ 告警级别 │
 * ├────────────────────────────┼──────────┼─────────┤
 * │ 业务异常(BusinessException)│ 400/自定义 │ 可选   │
 * │ 参数校验失败                │ 400      │ -        │
 * │ 请求方法不支持              │ 405      │ -        │
 * │ 请求体解析失败              │ 400      │ -        │
 * │ NullPointerException       │ 500      │ ERROR    │
 * │ 数据库连接异常              │ 500      │ ERROR    │
 * │ 其他未分类异常              │ 500      │ WARN     │
 * └────────────────────────────┴──────────┴──────────┘
 * </pre>
 *
 * <p>【使用方式】</p>
 * <pre>
 * 在Spring Boot启动类中无需特殊配置，
 * 只要本类在@ComponentScan扫描范围内，就会自动生效。
 * 所有@RestController方法抛出的异常都会被这里捕获。
 * </pre>
 *
 * @author ruoyi
 */
@RestControllerAdvice
public class GlobalExceptionTraceHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionTraceHandler.class);

    /**
     * 告警引擎（注入，用于发送告警）
     */
    @Autowired(required = false) // 允许告警引擎未初始化时也能正常工作
    private AlertEngine alertEngine;

    // ===================== 业务异常处理 =====================

    /**
     * 业务异常处理（自定义业务异常）
     * <p>
     * 【设计】业务代码可主动抛出 BusinessException
     * 例如：throw new BusinessException("用户不存在");
     * 这类异常属于可预期的业务流程异常，通常只需WARN级别日志
     * </p>
     */
    @ExceptionHandler(BusinessException.class)
    public MonitorResponse<?> handleBusinessException(BusinessException e, HttpServletRequest request) {
        log.warn("[业务异常] {}: {}, TraceId={}",
                request.getRequestURI(), e.getMessage(), TraceContext.getTraceId());

        // 对特定严重级别的业务异常触发告警（可根据code灵活配置）
        if (e.isAlert() && alertEngine != null) {
            alertEngine.alertCustom("BUSINESS_WARNING", e.getMessage());
        }

        return MonitorResponse.fail(e.getCode(), e.getMessage());
    }

    // ===================== 参数校验异常处理 =====================

    /**
     * @Valid @RequestBody 注解参数校验失败处理
     * 【场景】POST请求时，请求体对象字段不满足@NotNull/@Size等约束
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MonitorResponse<?> handleValidException(MethodArgumentNotValidException e, HttpServletRequest request) {
        // 收集所有校验失败字段和信息
        StringBuilder msgBuilder = new StringBuilder("参数校验失败:");
        List<FieldError> fieldErrors = e.getBindingResult().getFieldErrors();
        for (FieldError fieldError : fieldErrors) {
            msgBuilder.append("\n  - [")
                    .append(fieldError.getField())
                    .append("] ")
                    .append(fieldError.getDefaultMessage());
        }

        String errorMsg = msgBuilder.toString();
        log.warn("[参数校验异常] {}: {}, TraceId={}",
                request.getRequestURI(), errorMsg, TraceContext.getTraceId());

        return MonitorResponse.fail(MonitorResponse.CODE_VALIDATE_ERROR, errorMsg);
    }

    /**
     * 表单参数绑定失败处理
     * 【场景】GET请求参数不匹配对象字段类型
     */
    @ExceptionHandler(BindException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MonitorResponse<?> handleBindException(BindException e, HttpServletRequest request) {
        StringBuilder msgBuilder = new StringBuilder("参数绑定失败:");
        List<FieldError> fieldErrors = e.getBindingResult().getFieldErrors();
        for (FieldError fieldError : fieldErrors) {
            msgBuilder.append("\n  - [")
                    .append(fieldError.getField())
                    .append("] ")
                    .append(fieldError.getDefaultMessage());
        }

        log.warn("[参数绑定异常] {}: {}, TraceId={}",
                request.getRequestURI(), msgBuilder.toString(), TraceContext.getTraceId());

        return MonitorResponse.fail(MonitorResponse.CODE_VALIDATE_ERROR, msgBuilder.toString());
    }

    /**
     * 方法参数类型不匹配
     * 【场景】URL参数类型不匹配（如期望数字但传入字符串）
     */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MonitorResponse<?> handleTypeMismatchException(MethodArgumentTypeMismatchException e, HttpServletRequest request) {
        String msg = "参数[" + e.getName() + "]类型错误，期望:" + (e.getRequiredType() != null ? e.getRequiredType().getSimpleName() : "未知");
        log.warn("[参数类型异常] {}: {}, TraceId={}",
                request.getRequestURI(), msg, TraceContext.getTraceId());

        return MonitorResponse.fail(MonitorResponse.CODE_VALIDATE_ERROR, msg);
    }

    /**
     * 单参数@Validated校验失败
     * 【场景】Controller方法直接参数上的@Min/@Max等注解校验失败
     */
    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MonitorResponse<?> handleConstraintViolationException(ConstraintViolationException e, HttpServletRequest request) {
        StringBuilder msgBuilder = new StringBuilder("参数校验失败:");
        Set<ConstraintViolation<?>> violations = e.getConstraintViolations();
        for (ConstraintViolation<?> violation : violations) {
            msgBuilder.append("\n  - ")
                    .append(violation.getMessage());
        }

        log.warn("[约束校验异常] {}: {}, TraceId={}",
                request.getRequestURI(), msgBuilder.toString(), TraceContext.getTraceId());

        return MonitorResponse.fail(MonitorResponse.CODE_VALIDATE_ERROR, msgBuilder.toString());
    }

    // ===================== 常见HTTP异常处理 =====================

    /**
     * 请求方法不支持（如GET请求但后端只支持POST）
     */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    @ResponseStatus(HttpStatus.METHOD_NOT_ALLOWED)
    public MonitorResponse<?> handleMethodNotSupported(HttpRequestMethodNotSupportedException e, HttpServletRequest request) {
        log.warn("[请求方法异常] URI:{}, 请求方法:{}, 支持方法:{}",
                request.getRequestURI(), request.getMethod(), e.getSupportedHttpMethods());

        return MonitorResponse.fail(405, "请求方法不支持: " + request.getMethod());
    }

    /**
     * 请求体解析失败（如JSON格式不对）
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MonitorResponse<?> handleNotReadable(HttpMessageNotReadableException e, HttpServletRequest request) {
        log.warn("[请求体解析异常] {}, TraceId={}",
                request.getRequestURI(), TraceContext.getTraceId(), e);

        return MonitorResponse.fail(400, "请求体格式错误");
    }

    /**
     * 404 - 无对应的Controller
     */
    @ExceptionHandler(NoHandlerFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public MonitorResponse<?> handleNoHandlerFound(NoHandlerFoundException e, HttpServletRequest request) {
        log.warn("[404] 未找到接口: {}, 请求方法:{}",
                e.getRequestURL(), request.getMethod());

        return MonitorResponse.fail(MonitorResponse.CODE_NOT_FOUND, "接口不存在: " + e.getRequestURL());
    }

    // ===================== 系统异常处理 =====================

    /**
     * 空指针异常（最高优先级，需要详细堆栈）
     * 【场景】代码bug：对象为null时调用方法或访问字段
     */
    @ExceptionHandler(NullPointerException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public MonitorResponse<?> handleNullPointerException(NullPointerException e, HttpServletRequest request) {
        log.error("[空指针异常] URI:{}, TraceId:{}",
                request.getRequestURI(), TraceContext.getTraceId(), e);

        // 触发告警
        if (alertEngine != null) {
            alertEngine.alertException(request.getRequestURI(), e, TraceContext.getTraceId());
        }

        return MonitorResponse.fail(MonitorResponse.CODE_FAIL, "服务内部错误(空指针)");
    }

    /**
     * 数据库连接异常 / JDBC错误
     * 【场景】数据库连接池耗尽、网络超时、SQL执行错误等
     */
    @ExceptionHandler({java.sql.SQLException.class,
            org.springframework.dao.DataAccessException.class})
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public MonitorResponse<?> handleDatabaseException(Exception e, HttpServletRequest request) {
        log.error("[数据库异常] URI:{}, TraceId:{}",
                request.getRequestURI(), TraceContext.getTraceId(), e);

        // 触发数据库告警
        if (alertEngine != null) {
            alertEngine.alertDatabaseError(request.getRequestURI(), e.getMessage(), TraceContext.getTraceId());
        }

        return MonitorResponse.fail(MonitorResponse.CODE_FAIL, "数据库服务异常");
    }

    /**
     * 兜底异常处理（所有其他未被catch的异常都走到这里）
     * <p>
     * 【设计】这是最后一道防线，必须记录完整的堆栈信息
     * 即使在开发阶段也应该立即修复这类异常
     * </p>
     */
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public MonitorResponse<?> handleException(Exception e, HttpServletRequest request) {
        log.error("[系统异常] URI:{}, Method:{}, TraceId:{}",
                request.getRequestURI(), request.getMethod(), TraceContext.getTraceId(), e);

        // 所有未分类异常都触发告警
        if (alertEngine != null) {
            alertEngine.alertException(request.getRequestURI(), e, TraceContext.getTraceId());
        }

        return MonitorResponse.fail(MonitorResponse.CODE_FAIL, "服务内部错误，请稍后重试");
    }
}
