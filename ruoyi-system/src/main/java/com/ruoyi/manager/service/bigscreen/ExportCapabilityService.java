package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.integration.api.ApiHttpResult;
import com.ruoyi.integration.api.TrafficApiHttpClient;
import com.ruoyi.integration.api.TrafficApiScenario;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.Map;

/**
 * api 能力探测：全字段导出维度过滤是否已支持。
 *
 * <p>api 当前全字段路径只下推车牌；backend 通过 {@code /api/v3/export/capabilities} 探测，
 * 返回 200 且 {@code fullDimensionFilters=true} 时自动放开维度过滤，404 时保持拒绝。
 * 探测结果缓存 5 分钟；配置 {@code bigscreen.export.full-dimension-filters=true/false}
 * 可强制覆盖（运维灰度/回滚）。</p>
 *
 * <p>降级：api 不可达/非 2xx 一律按“未支持”处理，宁可不放行也不导出全量。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class ExportCapabilityService
{
    private static final Logger log = LoggerFactory.getLogger(ExportCapabilityService.class);

    private static final long PROBE_INTERVAL_MS = 5L * 60L * 1000L;

    private static final String CAPABILITIES_PATH = "/api/v3/export/capabilities";

    /** auto / true / false */
    @Value("${bigscreen.export.full-dimension-filters:auto}")
    private String mode;

    @Autowired
    private TrafficApiHttpClient httpClient;

    private volatile Boolean cached;

    private volatile long nextProbeAt = 0L;

    public boolean fullDimensionFiltersEnabled()
    {
        String value = mode == null ? "auto" : mode.trim();
        if ("true".equalsIgnoreCase(value) || "on".equalsIgnoreCase(value))
        {
            return true;
        }
        if ("false".equalsIgnoreCase(value) || "off".equalsIgnoreCase(value))
        {
            return false;
        }
        long now = System.currentTimeMillis();
        Boolean current = cached;
        if (current != null && now < nextProbeAt)
        {
            return current;
        }
        boolean enabled = probe();
        cached = enabled;
        nextProbeAt = now + PROBE_INTERVAL_MS;
        return enabled;
    }

    private boolean probe()
    {
        try
        {
            ApiHttpResult<Map> result = httpClient.get(TrafficApiScenario.EXPORT_STATUS,
                    CAPABILITIES_PATH, Collections.<String, String>emptyMap(), Map.class);
            if (result == null || !result.is2xx() || result.getResult() == null)
            {
                MetricsRegistry.increment("export.capability.gate_closed");
                return false;
            }
            Object value = result.getResult().get("fullDimensionFilters");
            boolean enabled = value != null && ("true".equalsIgnoreCase(String.valueOf(value))
                    || "1".equals(String.valueOf(value)));
            if (enabled)
            {
                log.info("[导出能力] api 已支持全字段维度过滤，自动放开");
            }
            return enabled;
        }
        catch (RuntimeException e)
        {
            log.debug("[导出能力] 探测失败，按未支持处理: {}", e.getMessage());
            return false;
        }
    }
}
