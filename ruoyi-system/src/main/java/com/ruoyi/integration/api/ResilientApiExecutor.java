package com.ruoyi.integration.api;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.ruoyi.common.core.metrics.MetricsRegistry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.net.ConnectException;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;

/**
 * api 调用执行器：统一重试、熔断与错误码映射。
 *
 * <p>超时由 {@link TrafficApiHttpClient} 按 {@link TrafficApiScenario} 配置；重试次数由
 * {@link TrafficApiProperties#retries(TrafficApiScenario)} 决定；本执行器只负责退避与熔断状态。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
public class ResilientApiExecutor
{
    private static final Logger log = LoggerFactory.getLogger(ResilientApiExecutor.class);

    @Autowired
    private TrafficApiProperties properties;

    /** 按调用域隔离熔断，避免导出 5xx 连坐统计/预警等其它链路 */
    private final ConcurrentHashMap<String, CircuitBreaker> circuitBreakers =
            new ConcurrentHashMap<String, CircuitBreaker>();

    /** 404（契约未实现）冷却，避免每个缓存周期都打一次无效请求 */
    private final ConcurrentHashMap<String, Long> contractCooldowns = new ConcurrentHashMap<String, Long>();

    private static final String GROUP_DEFAULT = "default";

    private static final String GROUP_FLOW = "flow";

    private static final String GROUP_STATS = "stats";

    private static final String GROUP_WARNING = "warning";

    private static final String GROUP_EXPORT = "export";

    @PostConstruct
    public void init()
    {
        for (String group : new String[] { GROUP_DEFAULT, GROUP_FLOW, GROUP_STATS, GROUP_WARNING,
                GROUP_EXPORT })
        {
            breakerFor(group);
        }
    }

    /**
     * 按 endpoint 归组：同组共享熔断状态，不同组互不影响。
     */
    static String groupOf(String endpoint)
    {
        String name = endpoint == null ? "" : endpoint;
        String lower = name.toLowerCase();
        if (lower.startsWith("submitexport") || lower.startsWith("exportstatus")
                || lower.startsWith("export"))
        {
            return GROUP_EXPORT;
        }
        if (lower.startsWith("warning"))
        {
            return GROUP_WARNING;
        }
        if (lower.startsWith("escape") || lower.startsWith("audit")
                || lower.startsWith("income") || lower.startsWith("stats"))
        {
            return GROUP_STATS;
        }
        if (lower.startsWith("flow") || lower.startsWith("snapshot")
                || lower.startsWith("fee") || lower.startsWith("trailonline")
                || lower.startsWith("trailfitting"))
        {
            return GROUP_FLOW;
        }
        return GROUP_DEFAULT;
    }

    private CircuitBreaker breakerFor(String group)
    {
        CircuitBreaker breaker = circuitBreakers.get(group);
        if (breaker == null)
        {
            CircuitBreaker created = new CircuitBreaker(properties.getCircuitFailureThreshold(),
                    properties.getCircuitOpenMs(), properties.getCircuitHalfOpenPermits());
            breaker = circuitBreakers.putIfAbsent(group, created);
            if (breaker == null)
            {
                breaker = created;
            }
        }
        return breaker;
    }

    public <T> T execute(String endpoint, Callable<ApiHttpResult<T>> call, int retries)
    {
        MetricsRegistry.increment("api.request");
        Long cooldownUntil = contractCooldowns.get(endpoint);
        if (cooldownUntil != null && cooldownUntil > System.currentTimeMillis())
        {
            MetricsRegistry.increment("api.not_found");
            throw new ApiClientException(ApiErrorCode.NOT_FOUND, endpoint,
                    "api 契约未实现（冷却中）: " + endpoint);
        }
        CircuitBreaker breaker = breakerFor(groupOf(endpoint));
        if (!breaker.allowRequest())
        {
            MetricsRegistry.increment("api.circuit_open");
            throw new ApiClientException(ApiErrorCode.CIRCUIT_OPEN, endpoint,
                    "api 熔断中，直接降级: " + endpoint);
        }
        MetricsRegistry.setGauge("api.circuit.state", circuitStateValue());
        int maxAttempts = Math.max(1, retries + 1);
        ApiClientException lastError = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++)
        {
            boolean marked = false;
            try
            {
                ApiHttpResult<T> response = call.call();
                if (response == null)
                {
                    throw new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, endpoint,
                            "api 返回空响应: " + endpoint);
                }
                if (response.is2xx())
                {
                    if (response.getException() != null)
                    {
                        MetricsRegistry.increment("api.parse_error");
                        throw new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, endpoint,
                                "api 响应解析失败: " + response.getException().getMessage(),
                                response.getException());
                    }
                    breaker.onSuccess();
                    MetricsRegistry.increment("api.success");
                    MetricsRegistry.setGauge("api.circuit.state", circuitStateValue());
                    return response.getResult();
                }
                ApiClientException error = mapResponse(endpoint, response);
                markError(error);
                marked = true;
                if (error.getCode() == ApiErrorCode.NOT_FOUND)
                {
                    contractCooldowns.put(endpoint,
                            System.currentTimeMillis() + properties.getContractProbeIntervalMs());
                }
                lastError = error;
                if (attempt < maxAttempts && error.isRetryable())
                {
                    sleepBackoff(attempt);
                    continue;
                }
                throw error;
            }
            catch (ApiClientException e)
            {
                if (!marked)
                {
                    // 同一次尝试只计一次错误，避免响应分支与 catch 重复计数
                    markError(e);
                }
                if (e.getCode().isRetryable())
                {
                    lastError = e;
                    if (attempt < maxAttempts)
                    {
                        sleepBackoff(attempt);
                        continue;
                    }
                    // 熔断按「请求」而非「尝试」计数：重试用尽才记一次失败，
                    // 避免一次抖动被重试放大成整域 30 秒熔断。
                    breaker.onFailure();
                    MetricsRegistry.setGauge("api.circuit.state", circuitStateValue());
                }
                throw e;
            }
            catch (Throwable t)
            {
                ApiClientException error = mapThrowable(endpoint, t);
                markError(error);
                lastError = error;
                if (attempt < maxAttempts && error.isRetryable())
                {
                    sleepBackoff(attempt);
                    continue;
                }
                breaker.onFailure();
                MetricsRegistry.setGauge("api.circuit.state", circuitStateValue());
                throw error;
            }
        }
        throw lastError != null ? lastError
                : new ApiClientException(ApiErrorCode.UPSTREAM_ERROR, endpoint, "api 调用失败: " + endpoint);
    }

    /**
     * 兼容旧调用：返回默认域熔断器；跨域状态请用 {@link #getCircuitStates()}。
     */
    public CircuitBreaker getCircuitBreaker()
    {
        return breakerFor(GROUP_DEFAULT);
    }

    /** 各调用域熔断状态快照（运维排查用）。 */
    public java.util.Map<String, String> getCircuitStates()
    {
        java.util.Map<String, String> result = new java.util.LinkedHashMap<String, String>();
        for (String group : new String[] { GROUP_DEFAULT, GROUP_FLOW, GROUP_STATS, GROUP_WARNING,
                GROUP_EXPORT })
        {
            result.put(group, breakerFor(group).getState().name());
        }
        return result;
    }

    /** 任一域 OPEN 即视为整体 OPEN；否则任一 HALF_OPEN 为 HALF_OPEN。 */
    public CircuitBreaker.State getOverallCircuitState()
    {
        boolean halfOpen = false;
        for (String group : new String[] { GROUP_DEFAULT, GROUP_FLOW, GROUP_STATS, GROUP_WARNING,
                GROUP_EXPORT })
        {
            CircuitBreaker.State state = breakerFor(group).getState();
            if (state == CircuitBreaker.State.OPEN)
            {
                return CircuitBreaker.State.OPEN;
            }
            if (state == CircuitBreaker.State.HALF_OPEN)
            {
                halfOpen = true;
            }
        }
        return halfOpen ? CircuitBreaker.State.HALF_OPEN : CircuitBreaker.State.CLOSED;
    }

    private long circuitStateValue()
    {
        CircuitBreaker.State state = getOverallCircuitState();
        if (state == CircuitBreaker.State.OPEN)
        {
            return 1L;
        }
        return state == CircuitBreaker.State.HALF_OPEN ? 2L : 0L;
    }

    /**
     * 按错误码记录指标：超时率、上游错误率、限流等。
     */
    private void markError(ApiClientException error)
    {
        if (error == null || error.getCode() == null)
        {
            MetricsRegistry.increment("api.error");
            return;
        }
        switch (error.getCode())
        {
            case TIMEOUT:
                MetricsRegistry.increment("api.timeout");
                break;
            case UNAVAILABLE:
                MetricsRegistry.increment("api.unavailable");
                break;
            case UPSTREAM_ERROR:
                MetricsRegistry.increment("api.upstream_error");
                break;
            case NOT_FOUND:
                MetricsRegistry.increment("api.not_found");
                break;
            case RATE_LIMITED:
                MetricsRegistry.increment("api.rate_limited");
                break;
            case CIRCUIT_OPEN:
                MetricsRegistry.increment("api.circuit_open");
                break;
            case CONTRACT_VIOLATION:
                MetricsRegistry.increment("api.contract_violation");
                break;
            default:
                MetricsRegistry.increment("api.error");
                break;
        }
    }

    private <T> ApiClientException mapResponse(String endpoint, ApiHttpResult<T> response)
    {
        int status = response.getStatus();
        Throwable exception = response.getException();
        if (status == 0 && exception != null)
        {
            return mapThrowable(endpoint, exception);
        }
        if (status == 401)
        {
            return new ApiClientException(ApiErrorCode.UNAUTHORIZED, endpoint,
                    "api 未认证: " + endpoint, status, null, exception);
        }
        if (status == 403)
        {
            return new ApiClientException(ApiErrorCode.FORBIDDEN, endpoint,
                    "api 无权限: " + endpoint, status, null, exception);
        }
        if (status == 404)
        {
            return new ApiClientException(ApiErrorCode.NOT_FOUND, endpoint,
                    "api 契约未实现: " + endpoint, status, null, exception);
        }
        if (status == 409)
        {
            return new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, endpoint,
                    "api 状态冲突: " + endpoint + " status=" + status, status, null, exception);
        }
        if (status == 429)
        {
            return new ApiClientException(ApiErrorCode.RATE_LIMITED, endpoint,
                    "api 限流: " + endpoint, status, null, exception);
        }
        if (status >= 500)
        {
            return new ApiClientException(ApiErrorCode.UPSTREAM_ERROR, endpoint,
                    "api 5xx: " + endpoint + " status=" + status, status, null, exception);
        }
        if (status >= 400)
        {
            return new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, endpoint,
                    "api 4xx: " + endpoint + " status=" + status, status, null, exception);
        }
        return new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, endpoint,
                "api 响应异常: " + endpoint + " status=" + status, status, null, exception);
    }

    private ApiClientException mapThrowable(String endpoint, Throwable throwable)
    {
        if (throwable instanceof JsonProcessingException)
        {
            return new ApiClientException(ApiErrorCode.CONTRACT_VIOLATION, endpoint,
                    "api 响应解析失败: " + throwable.getMessage(), throwable);
        }
        Throwable current = throwable;
        while (current != null)
        {
            if (current instanceof SocketTimeoutException)
            {
                return new ApiClientException(ApiErrorCode.TIMEOUT, endpoint,
                        "api 读超时: " + endpoint, throwable);
            }
            if (current instanceof ConnectException || current instanceof UnknownHostException
                    || current instanceof SocketException)
            {
                return new ApiClientException(ApiErrorCode.UNAVAILABLE, endpoint,
                        "api 连接失败: " + endpoint, throwable);
            }
            current = current.getCause();
        }
        return new ApiClientException(ApiErrorCode.UNAVAILABLE, endpoint,
                "api 调用失败: " + endpoint, throwable);
    }

    private void sleepBackoff(int attempt)
    {
        long sleep = properties.getRetryBackoffMs() * attempt;
        if (sleep <= 0L)
        {
            return;
        }
        try
        {
            Thread.sleep(sleep);
        }
        catch (InterruptedException e)
        {
            Thread.currentThread().interrupt();
            log.warn("[api] 重试等待被中断 sleep={}ms", sleep);
        }
    }
}
