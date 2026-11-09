package com.ruoyi.web.controller.monitor;

import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.integration.api.ResilientApiExecutor;
import com.ruoyi.manager.service.bigscreen.FeatureSwitchService;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 大屏/查询链路可观测与灰度开关运维入口。
 *
 * <p>指标：熔断状态、api 超时率、降级次数、缓存命中率、导出积压；
 * 开关：Redis 运行期覆盖，无需重启即可灰度/回滚。</p>
 *
 * @author car-monit-backend-java-v3
 */
@RestController
@RequestMapping("/monitor/bigscreen")
public class BigScreenOpsController extends BaseController
{
    @Autowired
    private ResilientApiExecutor resilientApiExecutor;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @GetMapping("/metrics")
    public AjaxResult metrics()
    {
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("counters", MetricsRegistry.counters());
        result.put("gauges", MetricsRegistry.gauges());
        result.put("apiTimeoutRate", ratio(MetricsRegistry.counter("api.timeout"),
                MetricsRegistry.counter("api.request")));
        result.put("apiErrorRate", ratio(MetricsRegistry.counter("api.upstream_error"),
                MetricsRegistry.counter("api.request")));
        result.put("cacheHitRate", cacheHitRate());
        result.put("exportBacklog", MetricsRegistry.gauge("export.active"));
        result.put("circuitState", resilientApiExecutor.getOverallCircuitState().name());
        result.put("circuitScenarios", resilientApiExecutor.getCircuitStates());
        return AjaxResult.success(result);
    }

    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @GetMapping("/switches")
    public AjaxResult switches()
    {
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("effective", featureSwitchService.snapshot());
        result.put("defaults", featureSwitchService.defaults());
        result.put("gray", featureSwitchService.graySnapshot());
        return AjaxResult.success(result);
    }

    /**
     * 运行期灰度：percent=0-100；tenants 非空时仅名单内租户命中（逗号分隔）。
     */
    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @PostMapping("/gray/{name}")
    public AjaxResult overrideGray(@PathVariable String name,
                                   @RequestParam(defaultValue = "100") int percent,
                                   @RequestParam(required = false) String tenants)
    {
        assertSecuritySwitchAllowed(name);
        featureSwitchService.overrideGray(name, percent, tenants);
        return AjaxResult.success(featureSwitchService.snapshot());
    }

    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @DeleteMapping("/gray/{name}")
    public AjaxResult clearGray(@PathVariable String name)
    {
        featureSwitchService.clearGray(name);
        return AjaxResult.success(featureSwitchService.snapshot());
    }

    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @PostMapping("/switches/{name}")
    public AjaxResult override(@PathVariable String name,
                               @RequestParam boolean enabled)
    {
        assertSecuritySwitchAllowed(name);
        featureSwitchService.override(name, enabled);
        return AjaxResult.success(featureSwitchService.snapshot());
    }

    /**
     * 安全类开关（导出审批等）不允许只有「监控查看」权限的账号改动，
     * 否则可以一行运维调用关掉审批，绕过全字段导出的强管控。
     */
    private void assertSecuritySwitchAllowed(String name)
    {
        if (FeatureSwitchService.EXPORT_APPROVAL.equalsIgnoreCase(name)
                && !SecurityUtils.hasPermi("manager:bigscreen:exportApprove"))
        {
            throw new AccessDeniedException("修改 export-approval 需要 manager:bigscreen:exportApprove 权限");
        }
    }

    @PreAuthorize("@ss.hasPermi('monitor:server:list')")
    @DeleteMapping("/switches/{name}")
    public AjaxResult clear(@PathVariable String name)
    {
        featureSwitchService.clearOverride(name);
        return AjaxResult.success(featureSwitchService.snapshot());
    }

    private double cacheHitRate()
    {
        long l1 = MetricsRegistry.counter("cache.hit.L1");
        long l2 = MetricsRegistry.counter("cache.hit.L2");
        long stale = MetricsRegistry.counter("cache.hit.STALE");
        long miss = MetricsRegistry.counter("cache.hit.MISS");
        long total = l1 + l2 + stale + miss;
        return total <= 0L ? 0d : round((double) (l1 + l2 + stale) / total);
    }

    private double ratio(long numerator, long denominator)
    {
        return denominator <= 0L ? 0d : round((double) numerator / denominator);
    }

    private double round(double value)
    {
        return Math.round(value * 10000d) / 10000d;
    }
}
