package com.ruoyi.common.core.config;

import com.ruoyi.common.core.monitor.AlertEngine;
import com.ruoyi.common.core.monitor.MetricCollector;
import com.ruoyi.common.core.monitor.SqlLogInterceptor;
import com.ruoyi.common.core.context.TraceContext;
import com.ruoyi.common.core.filter.TraceIdFilter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnMissingBean;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.annotation.PostConstruct;

/**
 * 监控组件自动装配配置类
 * <p>
 * 【设计目的】
 * 将所有监控相关组件（TraceIdFilter、SQL拦截器、指标收集器、告警引擎）
 * 统一在一处进行Bean定义和初始化，避免业务代码分散引用
 * </p>
 *
 * <p>【组件初始化顺序】</p>
 * <pre>
 * 1. TraceContext（静态工具类，无需Bean）
 * 2. AlertEngine（告警引擎，依赖简单）
 * 3. MetricCollector（指标收集器，依赖简单）
 * 4. SqlLogInterceptor（SQL拦截器，注入上面2个组件）
 * 5. TraceIdFilter（Web过滤器，最先拦截请求）
 * </pre>
 *
 * <p>【配置项说明】</p>
 * <pre>
 * monitor.enabled: true/false，是否启用监控
 * monitor.slow-sql-threshold: 慢SQL阈值（毫秒）
 * monitor.slow-method-threshold: 慢方法阈值（毫秒）
 * monitor.trace-id-header: TraceId请求头名称
 * </pre>
 *
 * @author ruoyi
 */
@Configuration
public class MonitorAutoConfiguration {

    private static final Logger log = LoggerFactory.getLogger(MonitorAutoConfiguration.class);

    /**
     * 是否启用监控（默认启用）
     */
    @Value("${monitor.enabled:true}")
    private boolean enabled;

    /**
     * 慢SQL阈值（毫秒，默认1000ms）
     */
    @Value("${monitor.slow-sql-threshold:1000}")
    private long slowSqlThreshold;

    /**
     * 慢方法阈值（毫秒，默认500ms）
     */
    @Value("${monitor.slow-method-threshold:500}")
    private long slowMethodThreshold;

    /**
     * TraceId请求头名称（默认X-Trace-Id）
     */
    @Value("${monitor.trace-id-header:X-Trace-Id}")
    private String traceIdHeader;

    /**
     * 初始化方法，打印配置信息
     */
    @PostConstruct
    public void init() {
        if (enabled) {
            log.info(
                    "\n╔══════════════════════════════════════════════════════════\n" +
                    "║ 【监控组件】监控系统已启动\n" +
                    "║  慢SQL阈值: {} ms\n" +
                    "║  慢方法阈值: {} ms\n" +
                    "║  TraceId请求头: {}\n" +
                    "╚══════════════════════════════════════════════════════════",
                    slowSqlThreshold, slowMethodThreshold, traceIdHeader
            );

            // 将配置项传递到TraceContext（供Filter读取）
            TraceContext.setTraceIdHeaderName(traceIdHeader);
        } else {
            log.warn("[监控组件]监控系统已禁用(monitor.enabled=false)");
        }
    }

    /**
     * 注册告警引擎Bean
     * <p>
     * 【设计】单例模式，全局共享一个告警引擎
     * 所有需要发送告警的组件（如AOP切面、SQL拦截器）都注入同一个实例
     * </p>
     */
    @Bean
    @ConditionalOnMissingBean
    public AlertEngine alertEngine() {
        return new AlertEngine();
    }

    /**
     * 注册指标收集器Bean
     * <p>
     * 【设计】单例模式，用于集中收集系统性能指标
     * 同时暴露给监控面板查询
     * </p>
     */
    @Bean
    @ConditionalOnMissingBean
    public MetricCollector metricCollector() {
        return new MetricCollector();
    }

    /**
     * 注册SQL日志拦截器Bean
     * <p>
     * 【设计】实现MyBatis Interceptor接口
     * 在SQL执行前后拦截，记录执行时间和完整SQL
     * 同时收集到 MetricCollector，并在超时后触发告警
     * </p>
     */
    @Bean
    @ConditionalOnMissingBean
    public SqlLogInterceptor sqlLogInterceptor() {
        SqlLogInterceptor interceptor = new SqlLogInterceptor();
        interceptor.setSlowSqlThreshold(slowSqlThreshold);
        return interceptor;
    }

    /**
     * 注册TraceId过滤器
     * <p>
     * 【设计】FilterRegistrationBean用于在Spring Boot中注册Servlet Filter
     * 拦截所有请求，在请求进入时生成/读取TraceId，响应时回传TraceId
     * </p>
     */
    @Bean
    public FilterRegistrationBean<TraceIdFilter> traceIdFilterRegistration() {
        FilterRegistrationBean<TraceIdFilter> registration = new FilterRegistrationBean<TraceIdFilter>();

        // 创建并配置Filter实例
        TraceIdFilter filter = new TraceIdFilter();
        registration.setFilter(filter);

        // 设置拦截路径（所有请求）
        registration.addUrlPatterns("/*");

        // 设置Filter名称
        registration.setName("traceIdFilter");

        // 设置优先级（越小越先执行，设为最高优先级，确保TraceId最先生成）
        registration.setOrder(1);

        log.info("[监控组件]TraceIdFilter已注册，优先级=1，拦截路径=/*");
        return registration;
    }

    /**
     * 输出最终配置（方便排查问题）
     */
    @Bean
    public String monitorConfigSummary() {
        if (enabled) {
            log.info("[监控组件配置]\n" +
                    "  - 监控开关: enabled = {}\n" +
                    "  - 慢SQL阈值: slow-sql-threshold = {}ms\n" +
                    "  - 慢方法阈值: slow-method-threshold = {}ms\n" +
                    "  - TraceId请求头: trace-id-header = {}",
                    enabled, slowSqlThreshold, slowMethodThreshold, traceIdHeader);
        }
        return "monitor-config-initialized";
    }
}
