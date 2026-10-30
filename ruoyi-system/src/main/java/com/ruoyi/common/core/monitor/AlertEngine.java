package com.ruoyi.common.core.monitor;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 告警引擎
 * <p>
 * 【设计目的】
 * 1. 集中管理和触发各类告警（慢请求、异常、错误率等）
 * 2. 实现告警去重、抑制（避免告警风暴）
 * 3. 提供告警统计，供监控面板展示
 * </p>
 *
 * <p>【核心设计原则】</p>
 * <pre>
 * 1. 幂等性：对同一类告警在窗口内不重复通知
 * 2. 抑制性：1分钟内同类告警超过阈值，只通知一次
 * 3. 可扩展：新增告警类型只需调用alertCustom()
 * 4. 统计化：所有告警都被记录，可用于分析
 * </pre>
 *
 * <p>【告警类型定义】</p>
 * <pre>
 * ┌────────────────────┬───────────────────────────┐
 * │ 类型               │ 触发条件          │
 * ├────────────────────┼───────────────────────┤
 * │ SLOW_REQUEST      │ 方法耗时>阈值         │
 * │ EXCEPTION       │ 方法抛出异常          │
 * │ DB_ERROR        │ 数据库连接错误        │
 * │ HIGH_ERROR_RATE   │ 1分钟内错误率>10% │
 * └────────────────────┴───────────────────────┘
 * </pre>
 *
 * @author ruoyi
 */
@Component
public class AlertEngine {

    private static final Logger log = LoggerFactory.getLogger(AlertEngine.class);

    /**
     * 告警窗口大小（毫秒）
     * 在此时间窗口内，同类告警只通知一次，避免告警风暴
     */
    private static final long ALERT_WINDOW_MS = 60 * 1000L; // 60秒

    /**
     * 告警抑制阈值（窗口内同类告警最大通知次数）
     */
    private static final int MAX_ALERTS_PER_WINDOW = 5;

    /**
     * 告警记录容器
     * key = 告警类型
     * value = 该类型告警的时间戳队列
     */
    private final Map<String, LinkedList<Long>> alertTimestamps = new ConcurrentHashMap<String, LinkedList<Long>>();

    /**
     * 告警统计计数器
     * key = 告警类型
     * value = 总告警次数
     */
    private final Map<String, AtomicLong> alertCounters = new ConcurrentHashMap<String, AtomicLong>();

    /**
     * 告警通知渠道
     * 可配置钉钉、企业微信、邮件等渠道
     * （当前版本暂用日志输出替代，便于快速接入真实通知渠道）
     */
    private final List<AlertNotifier> alertNotifiers = new ArrayList<AlertNotifier>();

    // ===================== 公开API：各类告警触发方法 =====================

    /**
     * 慢请求告警
     * <p>
     * 【触发时机】
     * 当某个方法耗时超过阈值时触发。
     * 用于识别系统性能瓶颈、SQL优化分析。
     * </p>
     *
     * @param methodName    方法全名：如 com.ruoyi.base.service.SnapshotFlowService.queryList
     * @param actualCost 实际耗时（毫秒）
     * @param threshold   阈值（毫秒）
     * @param traceId     TraceId
     */
    public void alertSlowRequest(String methodName, long actualCost, long threshold, String traceId) {
        String alertKey = "SLOW_REQUEST:" + methodName;

        // 1. 去重与抑制逻辑
        if (shouldSuppress(alertKey)) {
            // 被抑制的告警只做轻量统计，避免日志过多
            log.debug("[告警已抑制] 慢请求: {}, 耗时:{}ms", methodName, actualCost);
            incrementCounter(alertKey);
            return;
        }

        // 2. 记录告警（此处为轻量统计，真实生产可发送至监控系统）
        log.warn(
                "\n╔══════════════════════════════════════════════════════════\n" +
                "║ 【告警】系统性能告警 - 慢请求\n" +
                "║  方法: {}\n" +
                "║  实际耗时: {} ms\n" +
                "║  阈值: {} ms\n" +
                "║  超出: {} ms (超过阈值 {}%)\n" +
                "║  TraceId: {}\n" +
                "║  时间: {}\n" +
                "╚══════════════════════════════════════════════════════════",
                methodName, actualCost, threshold,
                (actualCost - threshold),
                (actualCost - threshold) * 100 / threshold,
                traceId, formatDate(new Date())
        );

        // 3. 发送至各通知渠道
        notifyAllChannels("SLOW_REQUEST",
                buildMessage("慢请求告警",
                        "方法: " + methodName,
                        "耗时: " + actualCost + "ms(阈值:" + threshold + "ms)",
                        "TraceId: " + traceId));
    }

    /**
     * 异常告警
     * <p>
     * 【触发时机】
     * 当AOP切面捕获方法抛出异常时触发。
     * 用于快速定位代码缺陷或环境问题。
     * </p>
     *
     * @param methodName 方法全名
     * @param exception  异常对象
     * @param traceId    TraceId
     */
    public void alertException(String methodName, Throwable exception, String traceId) {
        // 按异常类型分组
        String exceptionType = exception == null ? "Unknown" : exception.getClass().getSimpleName();
        String alertKey = "EXCEPTION:" + methodName + ":" + exceptionType;

        if (shouldSuppress(alertKey)) {
            log.debug("[告警已抑制] 异常: {}, 类型:{}", methodName, exceptionType);
            incrementCounter(alertKey);
            return;
        }

        // 构建异常信息（限制长度，避免日志过长）
        String exceptionMsg = exception == null ? "null" : exception.getMessage();
        if (exceptionMsg.length() > 200) {
            exceptionMsg = exceptionMsg.substring(0, 200) + "...(已截断)";
        }

        // ERROR级别的错误信息
        log.error(
                "\n╔══════════════════════════════════════════════════════════\n" +
                "║ 【告警】系统异常告警\n" +
                "║  方法: {}\n" +
                "║  异常类型: {}\n" +
                "║  异常信息: {}\n" +
                "║  TraceId: {}\n" +
                "║  时间: {}\n" +
                "╚══════════════════════════════════════════════════════════",
                methodName, exceptionType, exceptionMsg, traceId, formatDate(new Date()), exception);

        notifyAllChannels("EXCEPTION",
                buildMessage("异常告警",
                        "方法: " + methodName,
                        "类型: " + exceptionType,
                        "信息: " + exceptionMsg,
                        "TraceId: " + traceId));
    }

    /**
     * 数据库错误告警
     * <p>
     * 【触发时机】
     * 数据库连接异常、SQL错误、连接池耗尽等场景
     * </p>
     *
     * @param dataSourceName 数据源名称
     * @param errorMessage   错误信息
     * @param traceId        TraceId
     */
    public void alertDatabaseError(String dataSourceName, String errorMessage, String traceId) {
        String alertKey = "DB_ERROR:" + dataSourceName;

        if (shouldSuppress(alertKey)) {
            log.debug("[告警已抑制] 数据库错误: {}", dataSourceName);
            incrementCounter(alertKey);
            return;
        }

        log.error("[数据库告警] 数据源: {}, 错误: {}, TraceId: {}",
                dataSourceName, errorMessage, traceId);

        notifyAllChannels("DB_ERROR",
                buildMessage("数据库告警",
                        "数据源: " + dataSourceName,
                        "错误: " + errorMessage,
                        "TraceId: " + traceId));
    }

    /**
     * 自定义告警
     * <p>
     * 【使用场景】
     * 业务代码中需要触发告警时调用（如"库存不足、订单异常等）
     * </p>
     *
     * @param alertType 告警类型（自定义字符串，如 "INVENTORY_LOW"）
     * @param message    告警详细信息
     */
    public void alertCustom(String alertType, String message) {
        String alertKey = "CUSTOM:" + alertType;

        if (shouldSuppress(alertKey)) {
            log.debug("[告警已抑制] 自定义告警: {}", alertType);
            incrementCounter(alertKey);
            return;
        }

        log.warn("[自定义告警] 类型: {}, 信息: {}", alertType, message);
        notifyAllChannels(alertType, buildMessage("业务告警", message));
    }

    // ===================== 核心逻辑：去重与抑制 =====================

    /**
     * 判断是否应该抑制当前告警
     * <p>
     * 【算法】滑动窗口抑制
     * 维护一个最近1分钟的告警时间戳队列，
     * 如果窗口内已超过最大告警数，则抑制此次通知
     * </p>
     *
     * @param alertKey 告警唯一标识key
     * @return true=抑制(不通知); false=正常发送
     */
    private boolean shouldSuppress(String alertKey) {
        long now = System.currentTimeMillis();

        // 时间窗口开始时间
        long windowStart = now - ALERT_WINDOW_MS;

        // 获取或创建当前类型的时间戳队列
        LinkedList<Long> timestamps = alertTimestamps.get(alertKey);
        if (timestamps == null) {
            timestamps = new LinkedList<Long>();
            alertTimestamps.put(alertKey, timestamps);
        }

        // 同步操作：保证多线程安全
        synchronized (timestamps) {
            // 1. 清理过期的时间戳（早于1分钟前的）
            while (!timestamps.isEmpty() && timestamps.getFirst() < windowStart) {
                timestamps.removeFirst();
            }

            // 2. 判断窗口内是否已超出告警阈值
            if (timestamps.size() >= MAX_ALERTS_PER_WINDOW) {
                // 已超出阈值，抑制告警，但仍记录一个时间戳用于统计
                timestamps.addLast(now);
                return true;
            }

            // 3. 记录当前时间戳，允许发送本次告警
            timestamps.addLast(now);
            return false;
        }
    }

    /**
     * 递增告警计数器
     */
    private void incrementCounter(String alertKey) {
        AtomicLong counter = alertCounters.get(alertKey);
        if (counter == null) {
            counter = new AtomicLong(0);
            alertCounters.put(alertKey, counter);
        }
        counter.incrementAndGet();
    }

    // ===================== 通知分发机制 =====================

    /**
     * 通知所有注册的告警渠道
     * <p>
     * 【说明】
     * 可在系统启动时注册通知渠道，如：
     * - 企业微信机器人
     * - 钉钉通知
     * - 邮件通知
     * - 短信通知
     * </p>
     *
     * @param alertType 告警类型
     * @param message   告警消息
     */
    private void notifyAllChannels(String alertType, String message) {
        for (AlertNotifier notifier : alertNotifiers) {
            try {
                notifier.notify(alertType, message);
            } catch (Exception e) {
                // 通知渠道异常，不影响主流程
                log.warn("[告警通知失败] 渠道: {}, 异常: {}",
                        notifier.getClass().getSimpleName(), e.getMessage());
            }
        }
    }

    /**
     * 注册一个新的告警通知渠道
     *
     * @param notifier 通知渠道实现
     */
    public void registerNotifier(AlertNotifier notifier) {
        alertNotifiers.add(notifier);
        log.info("[告警引擎] 注册通知渠道: {}", notifier.getClass().getSimpleName());
    }

    // ===================== 工具方法 =====================

    /**
     * 构建格式化告警消息（可被ELK等系统索引）
     */
    private String buildMessage(String title, String... lines) {
        StringBuilder sb = new StringBuilder();
        sb.append("【").append(title).append("】");
        for (String line : lines) {
            if (line != null && !line.isEmpty()) {
                sb.append("\n  - ").append(line);
            }
        }
        return sb.toString();
    }

    /**
     * 格式化日期（输出格式: yyyy-MM-dd HH:mm:ss）
     */
    private String formatDate(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    /**
     * 获取告警统计（供监控面板使用）
     */
    public Map<String, Long> getAlertStatistics() {
        Map<String, Long> result = new HashMap<String, Long>();
        for (Map.Entry<String, AtomicLong> entry : alertCounters.entrySet()) {
            result.put(entry.getKey(), entry.getValue().get());
        }
        return result;
    }

    /**
     * 告警通知渠道接口
     * 实现此接口以接入新的通知渠道（钉钉、企业微信、邮件等）
     */
    public interface AlertNotifier {
        /**
         * 发送告警通知
         *
         * @param alertType 告警类型
         * @param message   告警消息
         */
        void notify(String alertType, String message);
    }
}
