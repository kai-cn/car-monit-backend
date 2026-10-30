package com.ruoyi.common.core.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 链路追踪注解
 * <p>
 * 【设计目的】
 * 1. 标记需要进行性能监控和日志追踪的方法
 * 2. 支持自定义慢请求阈值、是否记录参数等
 * 3. 与AOP切面配合，实现无侵入式的方法级监控
 * </p>
 *
 * <p>【使用示例】
 * <pre>
 * // 基础用法：记录方法执行耗时
 * {@literal @}Trace
 * public R listSnapshotData() { ... }
 *
 * // 自定义慢请求阈值：超过2秒记录警告
 * {@literal @}Trace(slowThreshold = 2000)
 * public List<SnapshotFlow> queryBigData() { ... }
 *
 * // 不记录方法参数（避免敏感数据泄露）
 * {@literal @}Trace(logParams = false)
 * public void processPassword(String password) { ... }
 *
 * // 不记录返回值
 * {@literal @}Trace(logResult = false)
 * public User getUser(String id) { ... }
 * </pre>
 * </p>
 *
 * @author ruoyi
 */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface Trace {

    /**
     * 慢请求阈值（毫秒）
     * <p>
     * 【触发规则】
     * 方法执行时间超过此值时，记录WARN级别日志并触发告警机制
     * </p>
     * 默认值：500ms，对普通查询友好；大数据/IO密集方法可以调大
     */
    long slowThreshold() default 500L;

    /**
     * 是否记录方法参数
     * <p>
     * 【安全考虑】
     * 对于密码、身份证号、手机号等敏感数据，应设置为false，
     * 避免敏感信息泄露到日志文件
     * </p>
     */
    boolean logParams() default true;

    /**
     * 是否记录方法返回值
     * <p>
     * 【性能考虑】
     * 对于返回大对象或长列表的方法，应设置为false以避免
     * 大量toString开销和日志文件膨胀
     * </p>
     */
    boolean logResult() default true;

    /**
     * 是否记录异常
     * <p>
     * 【用途】
     * 方法抛出异常时，自动记录ERROR级别日志，包含异常堆栈信息
     * </p>
     */
    boolean logException() default true;

    /**
     * 业务模块名称
     * <p>
     * 【用于日志聚合】
     * 便于按模块统计/筛选日志，例如"卡口抓拍""用户管理"
     * </p>
     */
    String module() default "";

    /**
     * 操作描述
     * <p>
     * 【用于人类阅读】
     * 对方法的功能做简单描述，便于非开发人员理解日志
     * </p>
     */
    String description() default "";
}
