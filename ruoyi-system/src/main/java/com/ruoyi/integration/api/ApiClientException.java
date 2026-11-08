package com.ruoyi.integration.api;

/**
 * api 调用异常。上层按 {@link #getCode()} 决定降级路径，不直接解析 HTTP 文本。
 *
 * @author car-monit-backend-java-v3
 */
public class ApiClientException extends RuntimeException
{
    private static final long serialVersionUID = 1L;

    private final ApiErrorCode code;

    private final String endpoint;

    private final int httpStatus;

    private final String upstreamCode;

    public ApiClientException(ApiErrorCode code, String endpoint, String message)
    {
        this(code, endpoint, message, 0, null, null);
    }

    public ApiClientException(ApiErrorCode code, String endpoint, String message, Throwable cause)
    {
        this(code, endpoint, message, 0, null, cause);
    }

    public ApiClientException(ApiErrorCode code, String endpoint, String message, int httpStatus,
                              String upstreamCode, Throwable cause)
    {
        super(message, cause);
        this.code = code;
        this.endpoint = endpoint;
        this.httpStatus = httpStatus;
        this.upstreamCode = upstreamCode;
    }

    public ApiErrorCode getCode()
    {
        return code;
    }

    public String getEndpoint()
    {
        return endpoint;
    }

    public int getHttpStatus()
    {
        return httpStatus;
    }

    public String getUpstreamCode()
    {
        return upstreamCode;
    }

    public boolean isRetryable()
    {
        return code != null && code.isRetryable();
    }
}
