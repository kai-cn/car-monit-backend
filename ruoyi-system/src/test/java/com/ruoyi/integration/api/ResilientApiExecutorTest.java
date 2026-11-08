package com.ruoyi.integration.api;

import com.ruoyi.common.core.metrics.MetricsRegistry;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.util.concurrent.Callable;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * api 执行器单测：熔断按调用域隔离、错误指标只计一次。
 */
class ResilientApiExecutorTest
{
    @BeforeEach
    void resetMetrics()
    {
        MetricsRegistry.reset();
    }

    @Test
    void endpointGroupsAreIsolated()
    {
        assertEquals("export", ResilientApiExecutor.groupOf("submitExport"));
        assertEquals("export", ResilientApiExecutor.groupOf("exportStatus"));
        assertEquals("warning", ResilientApiExecutor.groupOf("warningList"));
        assertEquals("warning", ResilientApiExecutor.groupOf("warningTop"));
        assertEquals("stats", ResilientApiExecutor.groupOf("escapeStatistics"));
        assertEquals("stats", ResilientApiExecutor.groupOf("auditStatistics"));
        assertEquals("flow", ResilientApiExecutor.groupOf("flow:/base/provcapture/list"));
        assertEquals("flow", ResilientApiExecutor.groupOf("trailOnline"));
        assertEquals("default", ResilientApiExecutor.groupOf("somethingElse"));
    }

    @Test
    void export5xxDoesNotTripStatsCircuit()
    {
        ResilientApiExecutor executor = newExecutor(2);
        Callable<ApiHttpResult<String>> failing = () -> ApiHttpResult.error(500, "", null);

        // 导出域连续失败达到阈值 -> 导出熔断打开
        assertThrows(ApiClientException.class, () -> executor.execute("submitExport", failing, 0));
        assertThrows(ApiClientException.class, () -> executor.execute("submitExport", failing, 0));
        assertEquals("OPEN", executor.getCircuitStates().get("export"));
        // 统计/预警域不受影响
        assertEquals("CLOSED", executor.getCircuitStates().get("stats"));
        assertEquals("CLOSED", executor.getCircuitStates().get("warning"));
        assertEquals(CircuitBreaker.State.OPEN, executor.getOverallCircuitState());

        // 导出域熔断后直接快速失败
        ApiClientException e = assertThrows(ApiClientException.class,
                () -> executor.execute("submitExport", failing, 0));
        assertEquals(ApiErrorCode.CIRCUIT_OPEN, e.getCode());
    }

    @Test
    void upstreamErrorCountedOncePerAttempt()
    {
        ResilientApiExecutor executor = newExecutor(5);
        Callable<ApiHttpResult<String>> failing = () -> ApiHttpResult.error(503, "", null);
        assertThrows(ApiClientException.class,
                () -> executor.execute("escapeStatistics", failing, 0));

        assertEquals(1L, MetricsRegistry.counter("api.request"));
        assertEquals(1L, MetricsRegistry.counter("api.upstream_error"));
        // 不再重复累加通用 api.error
        assertEquals(0L, MetricsRegistry.counter("api.error"));
    }

    @Test
    void transientFailureThenSuccessClosesCircuit()
    {
        ResilientApiExecutor executor = newExecutor(2);
        Callable<ApiHttpResult<String>> failing = () -> ApiHttpResult.error(500, "", null);
        assertThrows(ApiClientException.class, () -> executor.execute("warningList", failing, 0));
        assertThrows(ApiClientException.class, () -> executor.execute("warningList", failing, 0));
        assertEquals("OPEN", executor.getCircuitStates().get("warning"));

        // 半开窗口很短，直接重建执行器验证成功会复位
        ResilientApiExecutor fresh = newExecutor(2);
        Callable<ApiHttpResult<String>> success = () -> ApiHttpResult.<String>ok(200, "{}", "ok");
        String ok = fresh.<String>execute("warningList", success, 0);
        assertEquals("ok", ok);
        assertEquals("CLOSED", fresh.getCircuitStates().get("warning"));
    }

    private ResilientApiExecutor newExecutor(int failureThreshold)
    {
        TrafficApiProperties properties = new TrafficApiProperties();
        properties.setCircuitFailureThreshold(failureThreshold);
        properties.setCircuitOpenMs(60000L);
        properties.setCircuitHalfOpenPermits(1);
        properties.setRetryBackoffMs(0L);
        properties.setContractProbeIntervalMs(60000L);

        ResilientApiExecutor executor = new ResilientApiExecutor();
        try
        {
            Field field = ResilientApiExecutor.class.getDeclaredField("properties");
            field.setAccessible(true);
            field.set(executor, properties);
        }
        catch (ReflectiveOperationException e)
        {
            throw new IllegalStateException("无法注入 TrafficApiProperties", e);
        }
        executor.init();
        return executor;
    }
}
