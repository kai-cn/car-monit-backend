package com.ruoyi.integration.api;

/**
 * 调用 car-monit-api 的错误码。backend 只暴露稳定语义，不向上层泄漏 HTTP 细节。
 *
 * @author car-monit-backend-java-v3
 */
public enum ApiErrorCode
{
    /** 请求参数不符合查询契约 */
    INVALID_ARGUMENT(false),

    /** 未认证 */
    UNAUTHORIZED(false),

    /** 无权限 */
    FORBIDDEN(false),

    /** api 契约尚未实现（404） */
    NOT_FOUND(false),

    /** 被限流 */
    RATE_LIMITED(false),

    /** 读超时 */
    TIMEOUT(true),

    /** 连接失败 / 服务不可用 */
    UNAVAILABLE(true),

    /** 上游 5xx 或业务错误码 */
    UPSTREAM_ERROR(true),

    /** 熔断打开，直接降级 */
    CIRCUIT_OPEN(false),

    /** 响应不符合契约（结构/业务码异常） */
    CONTRACT_VIOLATION(false);

    private final boolean retryable;

    ApiErrorCode(boolean retryable)
    {
        this.retryable = retryable;
    }

    public boolean isRetryable()
    {
        return retryable;
    }
}
