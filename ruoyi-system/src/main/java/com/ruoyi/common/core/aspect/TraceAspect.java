package com.ruoyi.common.core.aspect;

import com.ruoyi.common.core.annotation.Trace;
import com.ruoyi.common.core.context.TraceContext;
import com.ruoyi.common.core.monitor.AlertEngine;
import com.ruoyi.common.core.monitor.MetricCollector;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.Signature;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;

/**
 * 链路追踪AOP切面
 * <p>
 * 【设计目的】
 * 1. 对标记了@Trace注解的方法进行自动性能监控和日志记录
 * 2. 自动识别慢请求、异常并触发告警
 * 3. 收集方法级性能指标，供监控系统展示
 * </p>
 *
 * <p>【执行流程】
 * <pre>
 * ┌─────────────────────────────────────────────────────────────┐
 * │ 方法调用进入AOP                                               │
 * │     ↓                                                         │
 * │ 1. 读取@Trace注解属性                                         │
 * │ 2. 记录开始时间戳                                             │
 * │ 3. (可选) 记录方法参数到日志                                   │
 * │     ↓                                                         │
 * │ 执行目标方法 → 捕获异常                                         │
 * │     ↓                                                         │
 * │ 4. 计算方法耗时 = 当前时间 - 开始时间                           │
 * │ 5. 判断是否超过阈值 → 是 → 记录WARN日志 + 触发告警              │
 * │                       → 否 → 记录INFO日志                      │
 * │ 6. (可选) 记录返回值                                           │
 * │ 7. 上报性能指标到监控系统                                       │
 * │     ↓                                                         │
 * │ 返回方法结果                                                   │
 * └─────────────────────────────────────────────────────────────┘
 * </pre>
 * </p>
 *
 * @author ruoyi
 */
@Aspect
@Component
public class TraceAspect {

    private static final Logger log = LoggerFactory.getLogger(TraceAspect.class);

    /**
     * 告警引擎：检测异常/慢请求后触发告警通知
     */
    @Autowired
    private AlertEngine alertEngine;

    /**
     * 指标收集器：统计方法调用次数、耗时等数据
     */
    @Autowired
    private MetricCollector metricCollector;

    // ===================== AOP核心逻辑 =====================

    /**
     * 环绕通知：拦截所有标记@Trace注解的方法
     * <p>
     * 【Pointcut匹配规则】
     * - @annotation(Trace)：方法级别标注了@Trace注解
     * - @within(Trace)：类级别标注了@Trace注解，该类所有方法均被拦截
     * </p>
     *
     * <p>【核心职责】
     * <pre>
     * 1. 计时：记录方法执行开始、结束时间，计算耗时
     * 2. 日志：按配置记录参数/返回值/异常信息
     * 3. 告警：当方法耗时超过阈值或抛出异常时触发告警
     * 4. 指标：将方法调用次数和耗时上报至监控系统
     * </pre>
     * </p>
     *
     * @param joinPoint 连接点：包含被拦截方法的所有元信息
     * @param trace     @Trace注解实例：包含配置参数
     * @return 方法返回值
     * @throws Throwable 方法抛出的异常（原样抛出，不做吞异常处理）
     */
    @Around("@annotation(trace) || @within(trace)")
    public Object traceMethod(ProceedingJoinPoint joinPoint, Trace trace) throws Throwable {

        // ========== 第1步：解析上下文信息 ==========
        // 获取方法签名和类名（便于日志可读）
        Signature signature = joinPoint.getSignature();
        String className = signature.getDeclaringTypeName();
        String methodName = signature.getName();
        String fullMethodName = className + "." + methodName;

        // 如果@Trace标注在类级别上，需要从方法或类上读取具体配置
        // 此处trace参数如果为null（类级别注解时），需要手动获取
        if (trace == null) {
            trace = getTraceFromTarget(joinPoint, className, methodName);
        }

        // 读取注解配置（默认值见@Trace注解定义）
        long slowThreshold = trace.slowThreshold();
        boolean needLogParams = trace.logParams();
        boolean needLogResult = trace.logResult();
        boolean needLogException = trace.logException();
        String module = trace.module();
        String description = trace.description();

        // ========== 第2步：记录请求日志（参数可选） ==========
        if (needLogParams && log.isDebugEnabled()) {
            Object[] args = joinPoint.getArgs();
            log.debug("[方法进入] {}.{}({}), TraceId={}, 模块={}, 描述={}",
                    className, methodName, formatArgs(args),
                    TraceContext.getTraceId(), module, description);
        }

        // ========== 第3步：计时并执行目标方法 ==========
        long startTime = System.currentTimeMillis();
        Object result = null;
        Throwable caughtException = null;

        try {
            // 执行被拦截的方法（这是真正的业务逻辑）
            result = joinPoint.proceed();
            return result;

        } catch (Throwable t) {
            // 记录异常引用，在finally中做统一处理（不在此处吞异常）
            caughtException = t;
            throw t;  // 原样抛出，让上层或全局异常处理器处理

        } finally {
            // ========== 第4步：计算耗时并记录结束日志 ==========
            long cost = System.currentTimeMillis() - startTime;

            // 4.1 记录返回值（可选，由注解配置控制）
            if (needLogResult && result != null && log.isDebugEnabled()) {
                log.debug("[方法结束] {}.{}, 耗时={}ms, 返回值类型={}, TraceId={}",
                        className, methodName, cost,
                        result.getClass().getSimpleName(), TraceContext.getTraceId());
            }

            // 4.2 记录异常（可选，由注解配置控制）
            if (caughtException != null && needLogException) {
                // 异常时使用ERROR级别，并上报告警
                log.error("[方法异常] {}.{}, 耗时={}ms, TraceId={}, 异常={}",
                        fullMethodName, cost,
                        TraceContext.getTraceId(), caughtException.getMessage(), caughtException);

                // 触发异常告警
                alertEngine.alertException(fullMethodName, caughtException, TraceContext.getTraceId());
            }

            // 4.3 判断是否为慢请求 → 触发慢请求告警和日志
            if (cost >= slowThreshold) {
                // 慢请求时使用WARN级别，便于日志系统筛选
                log.warn("[慢请求告警] {}.{}, 耗时={}ms(阈值={}ms), TraceId={}, 模块={}",
                        fullMethodName, cost, slowThreshold, TraceContext.getTraceId(), module);

                // 触发慢请求告警（发送到告警引擎，由引擎决定通知渠道）
                alertEngine.alertSlowRequest(fullMethodName, cost, slowThreshold, TraceContext.getTraceId());
            } else if (log.isInfoEnabled()) {
                // 正常速度请求，记录INFO级别日志
                log.info("[方法完成] {}.{}, 耗时={}ms, TraceId={}",
                        fullMethodName, cost, TraceContext.getTraceId());
            }

            // ========== 第5步：上报性能指标 ==========
            // 用于监控系统展示方法调用次数、平均耗时等指标
            // 指标收集器内部做了异步处理，不会阻塞主流程
            metricCollector.recordMethodExecution(
                    fullMethodName,      // 方法全名
                    cost,                 // 耗时（毫秒）
                    caughtException != null  // 是否发生异常
            );
        }
    }

    // ===================== 辅助方法 =====================

    /**
     * 从方法或类上读取@Trace注解
     * <p>
     * 【为什么需要这个方法】
     * 当@Trace标注在类级别上时，Spring AOP的@Around("@annotation(trace) || @within(trace)")
     * 会把trace参数绑定为null或类级别的注解。为了获得更精确的配置，
     * 需要手动获取方法或类上的注解实例。
     * </p>
     *
     * @param joinPoint  连接点
     * @param className  类名
     * @param methodName 方法名
     * @return @Trace注解实例，找不到则返回默认配置实例
     */
    private Trace getTraceFromTarget(ProceedingJoinPoint joinPoint, String className, String methodName) {
        try {
            // 先尝试从方法级别读取
            if (joinPoint.getSignature() instanceof MethodSignature) {
                MethodSignature methodSig = (MethodSignature) joinPoint.getSignature();
                Method method = methodSig.getMethod();
                Trace methodTrace = method.getAnnotation(Trace.class);
                if (methodTrace != null) {
                    return methodTrace;
                }
            }
            // 再尝试从类级别读取
            Class<?> targetClass = joinPoint.getTarget().getClass();
            Trace classTrace = targetClass.getAnnotation(Trace.class);
            if (classTrace != null) {
                return classTrace;
            }
        } catch (Exception ignored) {
            // 读取异常时忽略，使用默认匿名类返回
        }

        // 返回一个匿名的@Trace默认值实现
        // 这是一个巧妙的写法：创建一个匿名类，反射获取其注解
        // 实际更简单的做法是在调用方判断null时使用默认值，
        // 这里为了避免每个调用方都要判断，提供一个默认值的注解实例
        return new Trace() {
            @Override
            public long slowThreshold() { return 500L; }
            @Override
            public boolean logParams() { return true; }
            @Override
            public boolean logResult() { return true; }
            @Override
            public boolean logException() { return true; }
            @Override
            public String module() { return ""; }
            @Override
            public String description() { return ""; }
            @Override
            public Class<? extends java.lang.annotation.Annotation> annotationType() { return Trace.class; }
        };
    }

    /**
     * 格式化方法参数（用于日志）
     * <p>
     * 【安全考虑】
     * 只输出参数类型，不输出具体参数值，
     * 避免敏感信息（密码、身份证号等）泄露到日志文件。
     * 同时也避免大对象的toString()性能开销。
     * </p>
     *
     * @param args 方法参数数组
     * @return 格式化后的参数描述字符串
     */
    private String formatArgs(Object[] args) {
        if (args == null || args.length == 0) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < args.length; i++) {
            if (i > 0) sb.append(", ");
            Object arg = args[i];
            // 只输出类型和null判断，不输出具体值
            sb.append(arg == null ? "null" : arg.getClass().getSimpleName());
        }
        return sb.toString();
    }
}
