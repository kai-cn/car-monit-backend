package com.ruoyi.integration.api;

/**
 * 一次 api HTTP 调用的原始结果：状态码、响应体、解析后的结果或异常。
 *
 * @author car-monit-backend-java-v3
 */
public class ApiHttpResult<T>
{
    private final int status;

    private final String body;

    private final T result;

    private final Throwable exception;

    private ApiHttpResult(int status, String body, T result, Throwable exception)
    {
        this.status = status;
        this.body = body;
        this.result = result;
        this.exception = exception;
    }

    public static <T> ApiHttpResult<T> ok(int status, String body, T result)
    {
        return new ApiHttpResult<T>(status, body, result, null);
    }

    public static <T> ApiHttpResult<T> error(int status, String body, Throwable exception)
    {
        return new ApiHttpResult<T>(status, body, null, exception);
    }

    public int getStatus()
    {
        return status;
    }

    public String getBody()
    {
        return body;
    }

    public T getResult()
    {
        return result;
    }

    public Throwable getException()
    {
        return exception;
    }

    public boolean is2xx()
    {
        return status >= 200 && status < 300;
    }
}
