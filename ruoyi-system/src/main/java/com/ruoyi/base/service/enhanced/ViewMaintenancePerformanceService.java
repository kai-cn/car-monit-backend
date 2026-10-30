package com.ruoyi.base.service.enhanced;

import com.ruoyi.base.task.ViewMaintenanceTask;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 视图维护性能评估服务
 * <p>
 * 功能：
 * 1. 收集视图维护任务的性能数据
 * 2. 分析性能瓶颈
 * 3. 提供优化建议
 * 4. 生成性能报告
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Service
public class ViewMaintenancePerformanceService {

    @Autowired
    private ViewMaintenanceTask viewMaintenanceTask;

    /**
     * 性能指标历史记录（最近10次执行）
     */
    private static final int MAX_HISTORY_SIZE = 10;
    private final LinkedList<PerformanceRecord> performanceHistory = new LinkedList<>();

    /**
     * 实时统计指标
     */
    private final AtomicLong totalExecutions = new AtomicLong(0);
    private final AtomicLong totalDurationMs = new AtomicLong(0);
    private final AtomicLong successCount = new AtomicLong(0);
    private final AtomicLong failureCount = new AtomicLong(0);

    /**
     * 性能阈值配置
     */
    private static final long WARNING_THRESHOLD_MS = 30000;  // 30秒警告阈值
    private static final long CRITICAL_THRESHOLD_MS = 60000; // 60秒临界阈值
    private static final double DEGRADATION_THRESHOLD = 0.3;  // 性能下降30%警告

    /**
     * 性能记录类
     */
    public static class PerformanceRecord {
        private long timestamp;
        private long durationMs;
        private int tableCount;
        private boolean success;
        private String triggerType;
        private Map<String, Long> phaseDurations; // 各阶段耗时

        // Getters and Setters
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
        public long getDurationMs() { return durationMs; }
        public void setDurationMs(long durationMs) { this.durationMs = durationMs; }
        public int getTableCount() { return tableCount; }
        public void setTableCount(int tableCount) { this.tableCount = tableCount; }
        public boolean isSuccess() { return success; }
        public void setSuccess(boolean success) { this.success = success; }
        public String getTriggerType() { return triggerType; }
        public void setTriggerType(String triggerType) { this.triggerType = triggerType; }
        public Map<String, Long> getPhaseDurations() { return phaseDurations; }
        public void setPhaseDurations(Map<String, Long> phaseDurations) { this.phaseDurations = phaseDurations; }
    }

    /**
     * 记录性能数据
     *
     * @param record 性能记录
     */
    public synchronized void recordPerformance(PerformanceRecord record) {
        // 添加到历史记录
        performanceHistory.addFirst(record);

        // 保持历史记录数量限制
        while (performanceHistory.size() > MAX_HISTORY_SIZE) {
            performanceHistory.removeLast();
        }

        // 更新统计指标
        totalExecutions.incrementAndGet();
        totalDurationMs.addAndGet(record.getDurationMs());

        if (record.isSuccess()) {
            successCount.incrementAndGet();
        } else {
            failureCount.incrementAndGet();
        }

        // 检查性能告警
        checkPerformanceAlerts(record);
    }

    /**
     * 检查性能告警
     *
     * @param record 性能记录
     */
    private void checkPerformanceAlerts(PerformanceRecord record) {
        // 1. 耗时阈值告警
        if (record.getDurationMs() > CRITICAL_THRESHOLD_MS) {
            log.error("[性能告警] 视图维护耗时超过临界阈值: {}ms > {}ms",
                record.getDurationMs(), CRITICAL_THRESHOLD_MS);
        } else if (record.getDurationMs() > WARNING_THRESHOLD_MS) {
            log.warn("[性能警告] 视图维护耗时超过警告阈值: {}ms > {}ms",
                record.getDurationMs(), WARNING_THRESHOLD_MS);
        }

        // 2. 性能退化告警
        if (performanceHistory.size() >= 5) {
            double avgRecent = calculateAverageDuration(3);
            double avgHistorical = calculateAverageDuration(10);

            if (avgHistorical > 0 && avgRecent > avgHistorical * (1 + DEGRADATION_THRESHOLD)) {
                log.warn("[性能告警] 性能明显下降 - 近期平均: {}ms, 历史平均: {}ms",
                    avgRecent, avgHistorical);
            }
        }

        // 3. 成功率告警
        double successRate = calculateSuccessRate();
        if (successRate < 0.9) {
            log.warn("[性能告警] 视图维护成功率低于90%: {}%", Math.round(successRate * 100));
        }
    }

    /**
     * 计算平均耗时
     *
     * @param count 最近N次记录
     * @return 平均耗时（毫秒）
     */
    public double calculateAverageDuration(int count) {
        if (performanceHistory.isEmpty()) {
            return 0;
        }

        int actualCount = Math.min(count, performanceHistory.size());
        long total = 0;

        for (int i = 0; i < actualCount; i++) {
            total += performanceHistory.get(i).getDurationMs();
        }

        return (double) total / actualCount;
    }

    /**
     * 计算成功率
     *
     * @return 成功率（0-1）
     */
    public double calculateSuccessRate() {
        long total = successCount.get() + failureCount.get();
        if (total == 0) {
            return 1.0;
        }
        return (double) successCount.get() / total;
    }

    /**
     * 获取性能报告
     *
     * @return 性能报告
     */
    public Map<String, Object> generatePerformanceReport() {
        Map<String, Object> report = new LinkedHashMap<>();

        // 基本统计
        report.put("totalExecutions", totalExecutions.get());
        report.put("successCount", successCount.get());
        report.put("failureCount", failureCount.get());
        report.put("successRate", String.format("%.2f%%", calculateSuccessRate() * 100));

        // 耗时统计
        report.put("avgDurationMs", Math.round(calculateAverageDuration(MAX_HISTORY_SIZE)));
        report.put("recentAvgDurationMs", Math.round(calculateAverageDuration(3)));

        if (!performanceHistory.isEmpty()) {
            report.put("maxDurationMs", performanceHistory.stream()
                .mapToLong(PerformanceRecord::getDurationMs)
                .max().orElse(0));
            report.put("minDurationMs", performanceHistory.stream()
                .mapToLong(PerformanceRecord::getDurationMs)
                .min().orElse(0));
        }

        // 历史记录
        List<Map<String, Object>> history = new ArrayList<>();
        for (PerformanceRecord record : performanceHistory) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("timestamp", record.getTimestamp());
            item.put("durationMs", record.getDurationMs());
            item.put("tableCount", record.getTableCount());
            item.put("success", record.isSuccess());
            item.put("triggerType", record.getTriggerType());
            history.add(item);
        }
        report.put("history", history);

        // 优化建议
        report.put("optimizationSuggestions", generateOptimizationSuggestions());

        return report;
    }

    /**
     * 生成优化建议
     *
     * @return 优化建议列表
     */
    public List<String> generateOptimizationSuggestions() {
        List<String> suggestions = new ArrayList<>();

        double avgDuration = calculateAverageDuration(MAX_HISTORY_SIZE);
        double successRate = calculateSuccessRate();

        // 1. 耗时优化建议
        if (avgDuration > CRITICAL_THRESHOLD_MS) {
            suggestions.add("【高优先级】视图维护耗时超过60秒，建议：");
            suggestions.add("  - 考虑使用物化视图替代普通视图");
            suggestions.add("  - 检查数据库服务器资源使用情况");
            suggestions.add("  - 考虑分阶段更新视图（增量更新）");
        } else if (avgDuration > WARNING_THRESHOLD_MS) {
            suggestions.add("【中优先级】视图维护耗时超过30秒，建议：");
            suggestions.add("  - 评估是否需要包含所有历史表");
            suggestions.add("  - 考虑增加执行频率减少单次处理量");
        }

        // 2. 成功率建议
        if (successRate < 0.9) {
            suggestions.add("【高优先级】视图维护成功率低于90%，建议：");
            suggestions.add("  - 检查数据库连接稳定性");
            suggestions.add("  - 增加重试机制");
            suggestions.add("  - 检查数据库权限配置");
        }

        // 3. 表数量增长建议
        if (!performanceHistory.isEmpty()) {
            int maxTableCount = performanceHistory.stream()
                .mapToInt(PerformanceRecord::getTableCount)
                .max().orElse(0);

            if (maxTableCount > 30) {
                suggestions.add("【中优先级】分表数量超过30个，建议：");
                suggestions.add("  - 考虑归档历史数据");
                suggestions.add("  - 使用分区表替代分表");
                suggestions.add("  - 创建多个视图（按年份分组）");
            }
        }

        // 4. 通用建议
        suggestions.add("【通用】建议定期清理历史数据，保持视图简洁");
        suggestions.add("【通用】建议在低峰期执行视图维护任务");
        suggestions.add("【通用】建议监控视图查询性能，及时调整策略");

        return suggestions;
    }

    /**
     * 预测未来性能
     *
     * @param expectedTableCount 预期表数量
     * @return 预测耗时（毫秒）
     */
    public long predictDuration(int expectedTableCount) {
        if (performanceHistory.isEmpty()) {
            return 60000; // 默认60秒
        }

        // 基于历史数据线性预测
        double avgDuration = calculateAverageDuration(MAX_HISTORY_SIZE);
        int avgTableCount = (int) performanceHistory.stream()
            .mapToInt(PerformanceRecord::getTableCount)
            .average().orElse(10);

        // 假设耗时与表数量成正比
        return (long) (avgDuration * ((double) expectedTableCount / avgTableCount));
    }

    /**
     * 重置统计数据
     */
    public void resetStatistics() {
        totalExecutions.set(0);
        totalDurationMs.set(0);
        successCount.set(0);
        failureCount.set(0);
        performanceHistory.clear();
        log.info("[性能评估服务] 统计数据已重置");
    }

    /**
     * 获取实时指标
     *
     * @return 实时指标
     */
    public Map<String, Object> getRealtimeMetrics() {
        Map<String, Object> metrics = new LinkedHashMap<>();
        metrics.put("totalExecutions", totalExecutions.get());
        metrics.put("successRate", String.format("%.2f%%", calculateSuccessRate() * 100));
        metrics.put("avgDurationMs", Math.round(calculateAverageDuration(MAX_HISTORY_SIZE)));
        metrics.put("historySize", performanceHistory.size());
        metrics.put("lastExecuteTime", viewMaintenanceTask.getMetrics().get("lastExecuteTime"));
        metrics.put("nextScheduleTime", viewMaintenanceTask.getMetrics().get("nextScheduleTime"));
        return metrics;
    }
}
