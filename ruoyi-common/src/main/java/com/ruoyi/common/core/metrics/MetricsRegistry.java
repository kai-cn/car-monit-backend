package com.ruoyi.common.core.metrics;

import java.util.Collections;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

/**
 * 轻量进程内指标注册表。
 *
 * <p>不引入 Prometheus/Micrometer 依赖，只提供计数器与瞬时值，
 * 由后台监控端点导出为 JSON，供接入 Prometheus（文本格式）或告警任务读取。</p>
 *
 * <p>指标命名规范：{@code 域.指标[.标签]}，例如：
 * {@code api.request}、{@code api.timeout}、{@code cache.hit.L1}、{@code degrade.CIRCUIT_OPEN}。</p>
 *
 * @author car-monit-backend-java-v3
 */
public final class MetricsRegistry
{
    private static final ConcurrentHashMap<String, LongAdder> COUNTERS =
            new ConcurrentHashMap<String, LongAdder>();

    private static final ConcurrentHashMap<String, AtomicLong> GAUGES =
            new ConcurrentHashMap<String, AtomicLong>();

    private MetricsRegistry()
    {
    }

    public static void increment(String name)
    {
        add(name, 1L);
    }

    public static void add(String name, long delta)
    {
        if (name == null || delta == 0L)
        {
            return;
        }
        LongAdder adder = COUNTERS.get(name);
        if (adder == null)
        {
            LongAdder created = new LongAdder();
            adder = COUNTERS.putIfAbsent(name, created);
            if (adder == null)
            {
                adder = created;
            }
        }
        adder.add(delta);
    }

    public static void setGauge(String name, long value)
    {
        if (name == null)
        {
            return;
        }
        AtomicLong gauge = GAUGES.get(name);
        if (gauge == null)
        {
            AtomicLong created = new AtomicLong(value);
            gauge = GAUGES.putIfAbsent(name, created);
            if (gauge == null)
            {
                gauge = created;
            }
        }
        gauge.set(value);
    }

    public static long counter(String name)
    {
        LongAdder adder = COUNTERS.get(name);
        return adder == null ? 0L : adder.sum();
    }

    public static long gauge(String name)
    {
        AtomicLong value = GAUGES.get(name);
        return value == null ? 0L : value.get();
    }

    /** 计数器快照（按名称排序，便于稳定输出）。 */
    public static Map<String, Long> counters()
    {
        Map<String, Long> result = new TreeMap<String, Long>();
        for (Map.Entry<String, LongAdder> entry : COUNTERS.entrySet())
        {
            result.put(entry.getKey(), entry.getValue().sum());
        }
        return Collections.unmodifiableMap(result);
    }

    /** 瞬时值快照。 */
    public static Map<String, Long> gauges()
    {
        Map<String, Long> result = new TreeMap<String, Long>();
        for (Map.Entry<String, AtomicLong> entry : GAUGES.entrySet())
        {
            result.put(entry.getKey(), entry.getValue().get());
        }
        return Collections.unmodifiableMap(result);
    }

    public static void reset()
    {
        COUNTERS.clear();
        GAUGES.clear();
    }
}
