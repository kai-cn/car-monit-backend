package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.integration.api.CircuitBreaker;
import com.ruoyi.integration.api.ResilientApiExecutor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import jakarta.annotation.PostConstruct;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/**
 * 指标告警：每分钟检查 api 超时率、降级次数、缓存命中率、熔断状态与导出积压。
 *
 * <p>只做日志告警 + 指标计数，不阻塞业务；阈值可通过 {@code traffic-api.metrics.*} 配置。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
public class TrafficMetricsAlertTask
{
    private static final Logger log = LoggerFactory.getLogger(TrafficMetricsAlertTask.class);

    @Value("${traffic-api.metrics.enabled:true}")
    private boolean enabled;

    @Value("${traffic-api.metrics.timeout-rate-threshold:0.2}")
    private double timeoutRateThreshold;

    @Value("${traffic-api.metrics.cache-hit-rate-threshold:0.5}")
    private double cacheHitRateThreshold;

    @Value("${traffic-api.metrics.degrade-per-minute-threshold:10}")
    private long degradePerMinuteThreshold;

    @Value("${traffic-api.metrics.export-backlog-threshold:20}")
    private long exportBacklogThreshold;

    @Autowired
    private ResilientApiExecutor resilientApiExecutor;

    /**
     * 说明：本工程没有 {@code @EnableScheduling}，@Scheduled 不会触发；
     * 复用 RuoYi 的 scheduledExecutorService 显式调度。
     */
    @Autowired
    @Qualifier("scheduledExecutorService")
    private ScheduledExecutorService scheduler;

    private long lastApiRequests;

    private long lastApiTimeouts;

    private long lastDegrades;

    private long lastCacheHits;

    private long lastCacheMisses;

    @PostConstruct
    public void start()
    {
        if (enabled && scheduler != null)
        {
            scheduler.scheduleWithFixedDelay(new Runnable()
            {
                @Override
                public void run()
                {
                    check();
                }
            }, 60L, 60L, TimeUnit.SECONDS);
        }
    }

    public void check()
    {
        if (!enabled)
        {
            return;
        }
        try
        {
            long requests = MetricsRegistry.counter("api.request");
            long timeouts = MetricsRegistry.counter("api.timeout");
            long degrades = MetricsRegistry.counter("degrade");
            long cacheHits = MetricsRegistry.counter("cache.hit") - MetricsRegistry.counter("cache.hit.MISS");
            long cacheMisses = MetricsRegistry.counter("cache.hit.MISS");

            long requestDelta = requests - lastApiRequests;
            long timeoutDelta = timeouts - lastApiTimeouts;
            long degradeDelta = degrades - lastDegrades;
            long cacheHitDelta = cacheHits - lastCacheHits;
            long cacheMissDelta = cacheMisses - lastCacheMisses;

            lastApiRequests = requests;
            lastApiTimeouts = timeouts;
            lastDegrades = degrades;
            lastCacheHits = cacheHits;
            lastCacheMisses = cacheMisses;

            if (requestDelta > 0L && (double) timeoutDelta / requestDelta >= timeoutRateThreshold)
            {
                alert("API_TIMEOUT_RATE", "api 超时率 " + timeoutDelta + "/" + requestDelta);
            }
            if (degradeDelta >= degradePerMinuteThreshold)
            {
                alert("DEGRADE_RATE", "降级次数/分钟 " + degradeDelta);
            }
            long cacheTotal = cacheHitDelta + cacheMissDelta;
            if (cacheTotal >= 10L
                    && (double) cacheHitDelta / cacheTotal < cacheHitRateThreshold)
            {
                alert("CACHE_HIT_RATE", "缓存命中率 " + cacheHitDelta + "/" + cacheTotal);
            }
            long backlog = MetricsRegistry.gauge("export.active");
            if (backlog >= exportBacklogThreshold)
            {
                alert("EXPORT_BACKLOG", "导出任务积压 " + backlog);
            }
            CircuitBreaker.State state = resilientApiExecutor.getOverallCircuitState();
            if (state == CircuitBreaker.State.OPEN)
            {
                alert("CIRCUIT_OPEN", "api 熔断已打开: " + resilientApiExecutor.getCircuitStates());
            }
        }
        catch (RuntimeException e)
        {
            log.warn("[指标告警] 检查失败: {}", e.getMessage());
        }
    }

    private void alert(String type, String detail)
    {
        MetricsRegistry.increment("alert." + type);
        log.warn("[指标告警] type={} detail={}", type, detail);
    }
}
