package com.ruoyi.common.core.filter;

import com.ruoyi.common.core.context.TraceContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.*;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;

/**
 * Web请求链路追踪过滤器
 * <p>
 * 【设计目的】
 * 1. 在所有HTTP请求的入口处生成/接收TraceId，实现全链路统一标识
 * 2. 记录请求的基本信息（方法、路径、IP、耗时）
 * 3. 为后续的日志、告警、监控提供统一的TraceId基础
 * </p>
 *
 * <p>【执行时机】
 * <pre>
 * ┌────────────────────────────────────────────────────────────────────┐
 * │  请求进入Tomcat                                                       │
 * │       ↓                                                               │
 * │  Spring Security过滤器                                                 │
 * │       ↓                                                               │
 * │  ┌─ TraceIdFilter ─┐  ← 本过滤器在所有业务逻辑之前执行               │
 * │  │  1. 读取Header  │                                                    │
 * │  │  2. 初始化Trace │                                                    │
 * │  │  3. 记录请求日志 │                                                    │
 * │  │  4. 放行请求     │                                                    │
 * │  │  5. 记录响应日志 │                                                    │
 * │  │  6. 清理TraceId │                                                    │
 * │  └─────────────────┘                                                    │
 * │       ↓                                                               │
 * │  Controller / Service                                                  │
 * └────────────────────────────────────────────────────────────────────┘
 * </pre>
 * </p>
 *
 * <p>【TraceId传递规则】
 * <pre>
 * 1. 外部请求：优先从请求Header获取TraceId（如网关/上游系统传递）
 *    Header名称：X-Trace-Id（业界标准）
 * 2. 无TraceId：作为链路起点，生成新的TraceId
 * 3. 内部系统：统一从Header读取，避免重复生成导致链路断裂
 * </pre>
 * </p>
 *
 * @author ruoyi
 */
public class TraceIdFilter implements Filter {

    private static final Logger log = LoggerFactory.getLogger(TraceIdFilter.class);

    /**
     * 链路追踪Header名称（业界标准命名）
     * 【作用】支持上下游系统间的TraceId传递，形成跨服务调用链
     */
    private static final String TRACE_ID_HEADER = "X-Trace-Id";

    /**
     * 请求开始时间在request attribute中的key
     * 【用途】在doFilter前后分别记录和读取，计算总耗时
     */
    private static final String REQUEST_START_TIME_ATTR = "request_start_time_millis";

    // ===================== Filter核心方法 =====================

    /**
     * 过滤器初始化（容器启动时调用一次）
     * <p>
     * 【可做的事情】
     * - 读取过滤器配置参数
     * - 初始化缓存资源
     * </p>
     */
    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // 这里可以读取初始化参数，暂无需特殊处理
        log.info("[链路追踪过滤器] 初始化完成");
    }

    /**
     * 过滤请求（核心方法，每个请求都会调用）
     * <p>
     * 【执行流程】
     * <pre>
     * ┌─────────────────────────────────────────────────────────┐
     * │  1. 从请求Header中读取上游传递的TraceId（如果有）            │
     * │  2. 调用TraceContext.init()初始化链路上下文               │
     * │  3. 将请求路径设置到MDC                                    │
     * │  4. 记录请求日志（方法、路径、IP、参数）                    │
     * │  5. 将TraceId设置到响应Header（便于前端调试）               │
     * │  6. 放行请求，执行FilterChain.doFilter()                   │
     * │  7. 捕获并记录异常（防止异常导致TraceId未清理）             │
     * │  8. 在finally中调用TraceContext.clear()清理上下文          │
     * │  9. 记录响应日志（耗时、状态码）                            │
     * └─────────────────────────────────────────────────────────┘
     * </pre>
     * </p>
     *
     * @param request  Servlet请求对象
     * @param response Servlet响应对象
     * @param chain    过滤器链
     */
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {

        // 必须先做类型转换，才能读取HTTP相关信息
        if (!(request instanceof HttpServletRequest) || !(response instanceof HttpServletResponse)) {
            // 非HTTP请求，直接放行（避免异常）
            chain.doFilter(request, response);
            return;
        }

        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;

        // ========== 第1步：读取TraceId并初始化上下文 ==========
        // 优先从Header获取上游TraceId，否则生成新的（全链路一致原则）
        String traceId = httpRequest.getHeader(TRACE_ID_HEADER);

        // 初始化链路上下文（同时记录开始时间，用于后续耗时计算）
        TraceContext.init(traceId);

        // 将请求路径存入MDC（日志自动带上）
        TraceContext.setRequestPath(httpRequest.getRequestURI());

        // 记录开始时间戳（用于最终耗时统计）
        request.setAttribute(REQUEST_START_TIME_ATTR, System.currentTimeMillis());

        // ========== 第2步：在响应Header中添加TraceId（便于前端调试） ==========
        // 好处：前端开发者在浏览器DevTools中可以直接看到TraceId，便于问题定位
        httpResponse.setHeader(TRACE_ID_HEADER, TraceContext.getTraceId());

        // ========== 第3步：记录请求日志 ==========
        logRequest(httpRequest);

        // ========== 第4步：执行后续过滤器和业务逻辑 ==========
        try {
            chain.doFilter(request, response);

            // ========== 第5步：正常响应日志 ==========
            logResponse(httpRequest, httpResponse, null);

        } catch (IOException e) {
            // IO异常（通常与连接断开相关）
            logResponse(httpRequest, httpResponse, e);
            throw e;
        } catch (ServletException e) {
            // Servlet异常（业务异常通常会被全局处理器捕获）
            logResponse(httpRequest, httpResponse, e);
            throw e;
        } catch (RuntimeException e) {
            // 未捕获的运行时异常（应尽量避免走到这里）
            log.error("[未捕获异常] TraceId={}, Path={}, 异常信息: {}",
                    TraceContext.getTraceId(), httpRequest.getRequestURI(), e.getMessage(), e);
            throw e;
        } finally {
            // ========== 第6步：清理上下文（必须！） ==========
            // 不论请求成功/失败/异常，都必须清理
            // 否则Tomcat线程池复用会导致"日志串线"严重问题
            long startTime = 0;
            Object attr = request.getAttribute(REQUEST_START_TIME_ATTR);
            if (attr != null) {
                startTime = (Long) attr;
            }
            if (startTime > 0) {
                long cost = System.currentTimeMillis() - startTime;
                // 记录慢请求告警（阈值：3000ms）
                if (cost >= 3000) {
                    log.warn("[慢请求告警] Path={}, 耗时={}ms, Method={}, IP={}, TraceId={}",
                            httpRequest.getRequestURI(), cost, httpRequest.getMethod(),
                            getClientIp(httpRequest), TraceContext.getTraceId());
                }
            }
            TraceContext.clear();
        }
    }

    /**
     * 过滤器销毁（容器关闭时调用一次）
     * <p>
     * 【可做的事情】
     * - 释放过滤器占用的资源
     * </p>
     */
    @Override
    public void destroy() {
        log.info("[链路追踪过滤器] 已销毁");
    }

    // ===================== 辅助方法 =====================

    /**
     * 记录请求日志
     * <p>
     * 【记录内容】
     * 1. 请求方法（GET/POST/PUT/DELETE等）
     * 2. 请求路径
     * 3. 客户端IP（用于问题排查时溯源）
     * 4. 内容类型（便于识别是否上传文件请求）
     * 5. TraceId（用于全链路串联）
     * </p>
     *
     * @param request HTTP请求对象
     */
    private void logRequest(HttpServletRequest request) {
        // 使用log.isDebugEnabled()避免不必要的字符串拼接开销
        if (log.isDebugEnabled()) {
            log.debug("[请求进入] Method={}, Path={}, IP={}, ContentType={}, TraceId={}",
                    request.getMethod(),
                    request.getRequestURI(),
                    getClientIp(request),
                    request.getContentType(),
                    TraceContext.getTraceId());
        }
    }

    /**
     * 记录响应日志
     * <p>
     * 【记录内容】
     * 1. 请求路径
     * 2. HTTP状态码（便于识别4xx/5xx异常）
     * 3. 总耗时（毫秒）
     * 4. 如果有异常，记录异常信息
     * </p>
     *
     * @param request   HTTP请求对象
     * @param response  HTTP响应对象
     * @param exception 发生的异常（无异常则为null）
     */
    private void logResponse(HttpServletRequest request,
                             HttpServletResponse response,
                             Exception exception) {
        // 从request attribute中读取开始时间（doFilter开头设置的）
        Object startTime = request.getAttribute(REQUEST_START_TIME_ATTR);
        long cost = 0;
        if (startTime != null) {
            cost = System.currentTimeMillis() - (Long) startTime;
        }

        int status = response.getStatus();

        // 有异常时输出ERROR级日志
        if (exception != null) {
            log.error("[请求异常结束] Path={}, Status={}, 耗时={}ms, TraceId={}, IP={}, 异常={}",
                    request.getRequestURI(), status, cost,
                    TraceContext.getTraceId(), getClientIp(request),
                    exception.getMessage());
        } else {
            // 根据状态码分级记录
            if (status >= 500) {
                log.error("[服务器错误响应] Path={}, Status={}, 耗时={}ms, TraceId={}, IP={}",
                        request.getRequestURI(), status, cost,
                        TraceContext.getTraceId(), getClientIp(request));
            } else if (status >= 400) {
                log.warn("[客户端错误响应] Path={}, Status={}, 耗时={}ms, TraceId={}, IP={}",
                        request.getRequestURI(), status, cost,
                        TraceContext.getTraceId(), getClientIp(request));
            } else {
                // 正常响应，使用INFO级别
                log.info("[请求完成] Path={}, Status={}, 耗时={}ms, TraceId={}",
                        request.getRequestURI(), status, cost, TraceContext.getTraceId());
            }
        }
    }

    /**
     * 获取客户端真实IP地址
     * <p>
     * 【为什么需要这个方法】
     * 1. 请求经过Nginx等反向代理后，remoteAddr是代理服务器IP
     * 2. 代理服务器通常会在Header中添加真实IP
     * 3. 需要按优先级读取多个Header
     * </p>
     *
     * <p>【Header优先级】
     * <pre>
     * 1. X-Forwarded-For（标准，可能包含多个IP，逗号分隔，取第一个）
     * 2. X-Real-IP（Nginx常用）
     * 3. Proxy-Client-IP（部分代理使用）
     * 4. WL-Proxy-Client-IP（WebLogic）
     * 5. HTTP_CLIENT_IP
     * 6. HTTP_X_FORWARDED_FOR
     * 7. 最后使用 request.getRemoteAddr()
     * </pre>
     *
     * @param request HTTP请求对象
     * @return 客户端真实IP地址
     */
    private String getClientIp(HttpServletRequest request) {
        // 按优先级依次读取各个Header
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("Proxy-Client-IP");
        }
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("WL-Proxy-Client-IP");
        }
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("HTTP_CLIENT_IP");
        }
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("HTTP_X_FORWARDED_FOR");
        }
        if (ip == null || ip.length() == 0 || "unknown".equalsIgnoreCase(ip)) {
            // 兜底：使用Servlet API获取的IP
            ip = request.getRemoteAddr();
        }

        // X-Forwarded-For可能包含多个IP（经过多级代理），格式：clientIP, proxy1IP, proxy2IP...
        // 取第一个IP作为客户端真实IP
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }

        return ip;
    }
}
