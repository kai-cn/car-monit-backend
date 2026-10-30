package com.ruoyi.common.core.monitor;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 监控指标收集器
 * <p>
 * 【设计目的】
 * 1. 收集系统运行时的性能指标（调用次数、耗时、错误率等）
 * 2. 在内存中维护滑动窗口统计，供监控面板展示
 * 3. 暴露查询API，支持外部监控系统定时拉取数据
 * </p>
 *
 * <p>【核心能力】</p>
 * <pre>
 * ┌─────────────────────────────────────────────────────────┐
 * │ 指标类型         │ 描述                             │
 * ├────────────────────────┼──────────────────────────────┤
 * │ method_calls    │ 方法调用次数统计                   │
 * │ method_latency │ 方法耗时统计 (P50/P90/P99/平均)    │
 * │ error_rate     │ 错误率统计                           │
 * │ sql_latency    │ SQL执行耗时统计                       │
 * └────────────────────────┴──────────────────────────────┘
 * </pre>
 *
 * @author ruoyi
 */
@Component
public class MetricCollector {

    private static final Logger log = LoggerFactory.getLogger(MetricCollector.class);

    /**
     * 统计窗口大小（秒）= 60秒
     */
    private static final int WINDOW_SECONDS = 60;

    /**
     * 方法调用统计容器
     * key = 方法全名
     * value = 该方法的统计对象
     */
    private final Map<String, MethodStatistics> methodStatsMap =
            new ConcurrentHashMap<String, MethodStatistics>();

    /**
     * SQL执行统计容器
     * key = Mapper名称+方法名
     */
    private final Map<String, SqlStatistics> sqlStatsMap =
            new ConcurrentHashMap<String, SqlStatistics>();

    /**
     * 系统总请求数
     */
    private final AtomicLong totalRequests = new AtomicLong(0);

    /**
     * 系统总异常数
     */
    private final AtomicLong totalErrors = new AtomicLong(0);

    /**
     * 系统启动时间
     */
    private final long startTime = System.currentTimeMillis();

    // ===================== 指标记录API =====================

    /**
     * 记录方法执行指标
     * <p>
     * 【每次AOP拦截后调用】
     * 记录方法的耗时和是否发生异常
     * </p>
     *
     * @param methodName 方法全名
     * @param costMs     耗时（毫秒）
     * @param hasError   是否发生异常
     */
    public void recordMethodExecution(String methodName, long costMs, boolean hasError) {
        // 获取或创建该方法的统计对象
        MethodStatistics stats = methodStatsMap.get(methodName);
        if (stats == null) {
            stats = new MethodStatistics();
            methodStatsMap.putIfAbsent(methodName, stats);
            stats = methodStatsMap.get(methodName);
        }
        stats.record(costMs, hasError);

        // 系统级统计
        totalRequests.incrementAndGet();
        if (hasError) {
            totalErrors.incrementAndGet();
        }
    }

    /**
     * 记录SQL执行指标
     * <p>
     * 【SQL拦截器调用】
     * 记录SQL执行耗时
     * </p>
     *
     * @param sqlIdentifier SQL唯一标识（如 mapper.method）
     * @param costMs        耗时（毫秒）
     */
    public void recordSqlExecution(String sqlIdentifier, long costMs) {
        SqlStatistics stats = sqlStatsMap.get(sqlIdentifier);
        if (stats == null) {
            stats = new SqlStatistics();
            sqlStatsMap.putIfAbsent(sqlIdentifier, stats);
            stats = sqlStatsMap.get(sqlIdentifier);
        }
        stats.record(costMs);
    }

    // ===================== 指标查询API =====================

    /**
     * 获取系统级健康状态汇总
     * <p>
     * 【返回内容】
     * - 总请求数、总异常数
     * - 系统错误率（异常数/请求数）
     * - 系统运行时长
     * - 慢请求总数
     * </p>
     *
     * @return 系统健康状态摘要Map
     */
    public Map<String, Object> getSystemHealthSummary() {
        Map<String, Object> summary = new LinkedHashMap<String, Object>();

        long requests = totalRequests.get();
        long errors = totalErrors.get();
        double errorRate = requests > 0 ? (errors * 100.0 / requests) : 0;
        long uptimeMs = System.currentTimeMillis() - startTime;

        summary.put("total_requests", requests);
        summary.put("total_errors", errors);
        summary.put("error_rate", String.format("%.2f%%", errorRate));
        summary.put("uptime_seconds", uptimeMs / 1000);
        summary.put("uptime_human", formatUptime(uptimeMs));
        summary.put("monitor_methods_count", methodStatsMap.size());
        summary.put("monitor_sql_count", sqlStatsMap.size());
        summary.put("report_time", formatDate(new Date()));

        return summary;
    }

    /**
     * 获取TOP N最慢方法（性能瓶颈分析）
     * <p>
     * 【返回结构】每个方法包含：
     * - 调用次数
     * - 平均耗时
     * - P90/P99耗时
     * - 错误率
     * </p>
     *
     * @param limit 返回前多少条
     * @return 方法性能排序列表
     */
    public List<Map<String, Object>> getTopSlowMethods(int limit) {
        List<Map<String, Object>> list = new ArrayList<Map<String, Object>>();

        // 将所有方法按平均耗时排序
        List<Map.Entry<String, MethodStatistics>> sortedEntries =
                new ArrayList<Map.Entry<String, MethodStatistics>>(methodStatsMap.entrySet());

        // 按平均耗时降序排序
        Collections.sort(sortedEntries, new Comparator<Map.Entry<String, MethodStatistics>>() {
            @Override
            public int compare(Map.Entry<String, MethodStatistics> o1, Map.Entry<String, MethodStatistics> o2) {
                double avg1 = o1.getValue().getAvgCost();
                double avg2 = o2.getValue().getAvgCost();
                return Double.compare(avg2, avg1); // 降序
            }
        });

        // 取TOP N
        for (int i = 0; i < Math.min(limit, sortedEntries.size()); i++) {
            Map.Entry<String, MethodStatistics> entry = sortedEntries.get(i);
            Map<String, Object> methodInfo = new LinkedHashMap<String, Object>();

            MethodStatistics stats = entry.getValue();
            long totalCalls = stats.getTotalCalls();
            long totalCost = stats.getTotalCost();
            long errorCalls = stats.getErrorCalls();
            double avgCost = stats.getAvgCost();
            double errorRate = totalCalls > 0 ? (errorCalls * 100.0 / totalCalls) : 0;

            methodInfo.put("method", entry.getKey());
            methodInfo.put("calls", totalCalls);
            methodInfo.put("avg_cost_ms", String.format("%.1f", avgCost));
            methodInfo.put("total_cost_ms", totalCost);
            methodInfo.put("errors", errorCalls);
            methodInfo.put("error_rate", String.format("%.2f%%", errorRate));

            list.add(methodInfo);
        }
        return list;
    }

    /**
     * 获取所有方法的详细统计
     */
    public Map<String, Map<String, Object>> getAllMethodStats() {
        Map<String, Map<String, Object>> result = new LinkedHashMap<String, Map<String, Object>>();
        for (Map.Entry<String, MethodStatistics> entry : methodStatsMap.entrySet()) {
            Map<String, Object> info = new LinkedHashMap<String, Object>();
            MethodStatistics stats = entry.getValue();

            info.put("total_calls", stats.getTotalCalls());
            info.put("total_cost_ms", stats.getTotalCost());
            info.put("avg_cost_ms", String.format("%.1f", stats.getAvgCost()));
            info.put("max_cost_ms", stats.getMaxCost());
            info.put("error_calls", stats.getErrorCalls());

            result.put(entry.getKey(), info);
        }
        return result;
    }

    /**
     * 获取所有SQL统计
     */
    public Map<String, Map<String, Object>> getAllSqlStats() {
        Map<String, Map<String, Object>> result = new LinkedHashMap<String, Map<String, Object>>();
        for (Map.Entry<String, SqlStatistics> entry : sqlStatsMap.entrySet()) {
            Map<String, Object> info = new LinkedHashMap<String, Object>();
            SqlStatistics stats = entry.getValue();

            info.put("total_calls", stats.getTotalCalls());
            info.put("total_cost_ms", stats.getTotalCost());
            info.put("avg_cost_ms", String.format("%.1f", stats.getAvgCost()));
            info.put("max_cost_ms", stats.getMaxCost());

            result.put(entry.getKey(), info);
        }
        return result;
    }

    /**
     * 重置所有指标（用于定期重置数据）
     */
    public void resetAll() {
        methodStatsMap.clear();
        sqlStatsMap.clear();
        totalRequests.set(0);
        totalErrors.set(0);
        log.info("[指标收集器] 已重置所有指标");
    }

    // ===================== 辅助方法 =====================

    /**
     * 格式化运行时长为人类可读格式
     */
    private String formatUptime(long uptimeMs) {
        long seconds = uptimeMs / 1000;
        long minutes = seconds / 60;
        long hours = minutes / 60;
        long days = hours / 24;

        StringBuilder sb = new StringBuilder();
        if (days > 0) sb.append(days).append("天");
        if (hours % 24 > 0) sb.append(hours % 24).append("小时");
        if (minutes % 60 > 0) sb.append(minutes % 60).append("分");
        if (seconds % 60 > 0) sb.append(seconds % 60).append("秒");
        if (sb.length() == 0) sb.append("刚刚启动");
        return sb.toString();
    }

    /**
     * 格式化日期
     */
    private String formatDate(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    // ===================== 内部统计类 =====================

    /**
     * 方法级性能统计
     */
    private static class MethodStatistics {
        private final AtomicLong totalCalls = new AtomicLong(0);
        private final AtomicLong totalCost = new AtomicLong(0);
        private final AtomicLong maxCost = new AtomicLong(0);
        private final AtomicLong errorCalls = new AtomicLong(0);

        /**
         * 记录一次方法调用
         */
        public synchronized void record(long cost, boolean hasError) {
            totalCalls.incrementAndGet();
            totalCost.addAndGet(cost);
            if (cost > maxCost.get()) {
                maxCost.set(cost);
            }
            if (hasError) {
                errorCalls.incrementAndGet();
            }
        }

        public long getTotalCalls() { return totalCalls.get(); }
        public long getTotalCost() { return totalCost.get(); }
        public long getMaxCost() { return maxCost.get(); }
        public long getErrorCalls() { return errorCalls.get(); }
        public double getAvgCost() {
            long calls = totalCalls.get();
            return calls > 0 ? totalCost.get() / (double) calls : 0;
        }
    }

    /**
     * SQL级性能统计
     */
    private static class SqlStatistics {
        private final AtomicLong totalCalls = new AtomicLong(0);
        private final AtomicLong totalCost = new AtomicLong(0);
        private final AtomicLong maxCost = new AtomicLong(0);

        public synchronized void record(long cost) {
            totalCalls.incrementAndGet();
            totalCost.addAndGet(cost);
            if (cost > maxCost.get()) {
                maxCost.set(cost);
            }
        }

        public long getTotalCalls() { return totalCalls.get(); }
        public long getTotalCost() { return totalCost.get(); }
        public long getMaxCost() { return maxCost.get(); }
        public double getAvgCost() {
            long calls = totalCalls.get();
            return calls > 0 ? totalCost.get() / (double) calls : 0;
        }
    }
}
