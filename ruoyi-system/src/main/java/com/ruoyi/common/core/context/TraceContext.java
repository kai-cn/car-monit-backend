package com.ruoyi.common.core.context;

import org.slf4j.MDC;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.Callable;

/**
 * 链路追踪上下文管理器
 * <p>
 * 【设计目的】
 * 1. 统一管理链路追踪核心标识（TraceId、SpanId）
 * 2. 实现跨线程的上下文传递（解决异步调用链路丢失问题）
 * 3. 为日志、监控、告警提供统一的标识基础
 * </p>
 *
 * <p>【核心概念说明】</p>
 * <pre>
 * ┌─────────────────────────────────────────────────────────────────────┐
 * │  TraceId（全链路唯一标识）                                           │
 * │  定义：一个完整请求从入口到出口的全生命周期ID                        │
 * │  作用：串联整个请求链上的所有日志、SQL、外部调用                      │
 * │  生成规则：32位UUID小写，格式：xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx      │
 * │  生命周期：请求入口生成 → 全链路传递 → 请求结束清理                 │
 * ├─────────────────────────────────────────────────────────────────────┤
 * │  SpanId（单次调用标识）                                             │
 * │  定义：链路中某一个节点/方法的唯一标识                               │
 * │  作用：标记链路中的具体调用节点，用于构建调用链树                    │
 * │  生成规则：进入新方法时生成，格式：00001，00002...                  │
 * ├─────────────────────────────────────────────────────────────────────┤
 * │  MDC（映射诊断上下文）                                              │
 * │  定义：SLF4J提供的线程本地存储，自动注入日志模版                     │
 * │  作用：日志输出时自动带上TraceId、用户ID、请求路径等信息            │
 * └─────────────────────────────────────────────────────────────────────┘
 * </pre>
 *
 * <p>【典型使用场景】</p>
 * <pre>
 * 1. Web请求入口：  Filter中调用 init()，初始化TraceId
 * 2. 异步任务：      调用 wrap() 包装Runnable/Callable，传递上下文
 * 3. 方法调用：      调用 newSpan() 生成子SpanId，用于区分调用层级
 * 4. 请求结束：      调用 clear()，避免线程池复用导致TraceId污染
 * </pre>
 *
 * @author ruoyi
 */
public class TraceContext {

    // ===================== 常量定义 =====================

    /**
     * TraceId在MDC中的key
     * 命名采用小写+下划线，与ELK/ELK兼容
     */
    public static final String TRACE_ID = "trace_id";

    /**
     * SpanId在MDC中的key
     */
    public static final String SPAN_ID = "span_id";

    /**
     * 用户ID在MDC中的key（用于用户行为追踪）
     */
    public static final String USER_ID = "user_id";

    /**
     * 请求路径在MDC中的key
     */
    public static final String REQUEST_PATH = "request_path";

    /**
     * 请求开始时间戳（用于计算耗时）
     */
    public static final String REQUEST_START_TIME = "request_start_time";

    /**
     * TraceId默认值（未初始化时使用，便于识别异常）
     */
    public static final String DEFAULT_TRACE_ID = "NO_TRACE_ID";

    /**
     * 生成的TraceId前缀（便于识别）
     */
    private static final String TRACE_ID_PREFIX = "";

    // ===================== TraceId生成方法 =====================

    /**
     * 生成一个新的TraceId
     * <p>
     * 【生成规则】
     * - 使用UUID生成32位唯一标识
     * - 去掉"-"分隔符，转为小写（便于日志存储和检索）
     * - 可通过添加前缀区分环境（如 dev_、prod_，此处不加）
     * </p>
     *
     * @return 生成的TraceId字符串
     */
    public static String generateTraceId() {
        return TRACE_ID_PREFIX + UUID.randomUUID().toString().replace("-", "");
    }

    /**
     * 生成一个新的SpanId
     * <p>
     * 【生成规则】
     * - 基于当前线程调用次数自增
     * - 格式：00001，00002...（5位补零，便于阅读）
     * </p>
     *
     * @return 生成的SpanId字符串
     */
    public static String generateSpanId() {
        // 使用线程本地变量存储Span计数器，避免并发问题
        Integer spanCount = SPAN_COUNTER.get();
        if (spanCount == null) {
            spanCount = 0;
        }
        spanCount = spanCount + 1;
        SPAN_COUNTER.set(spanCount);
        return String.format("%05d", spanCount);
    }

    /**
     * Span计数器线程本地变量
     * 【注意】ThreadLocal必须配合remove()使用，避免内存泄漏
     */
    private static final ThreadLocal<Integer> SPAN_COUNTER = new ThreadLocal<Integer>();

    // ===================== 初始化和清理方法 =====================

    /**
     * 初始化链路追踪上下文
     * <p>
     * 【调用时机】
     * - Web请求过滤器的doFilter()方法开头
     * - 定时任务的run()方法开头
     * - 消息消费者的onMessage()方法开头
     * </p>
     *
     * <p>【执行逻辑】</p>
     * <pre>
     * 1. 检查传入的TraceId：
     *    - 如果传入了TraceId（来自上游请求），使用传入值（全链路一致）
     *    - 如果没有传入（系统入口请求），生成新的TraceId
     * 2. 将TraceId、SpanId存入MDC
     * 3. 记录请求开始时间戳（用于后续计算耗时）
     * </pre>
     *
     * @param traceId 传入的TraceId，可为null（表示新请求）
     */
    public static void init(String traceId) {
        // 优先使用传入的TraceId（支持链路传递），否则生成新的
        String effectiveTraceId = (traceId != null && !traceId.trim().isEmpty())
                ? traceId
                : generateTraceId();

        // 存入MDC，日志输出时会自动带上这些值
        MDC.put(TRACE_ID, effectiveTraceId);
        MDC.put(SPAN_ID, generateSpanId());
        MDC.put(REQUEST_START_TIME, String.valueOf(System.currentTimeMillis()));
    }

    /**
     * 初始化链路追踪上下文（指定TraceId和用户ID）
     * <p>
     * 【重载方法】
     * 用于需要同时设置用户ID的场景（如登录后的请求）
     * </p>
     *
     * @param traceId 传入的TraceId
     * @param userId  用户ID（可为null）
     */
    public static void init(String traceId, String userId) {
        init(traceId);
        if (userId != null && !userId.trim().isEmpty()) {
            MDC.put(USER_ID, userId);
        }
    }

    /**
     * 清空链路追踪上下文
     * <p>
     * 【调用时机】
     * - Web请求过滤器的doFilter()方法结束后（finally块中）
     * - 定时任务结束后
     * - 异步任务结束后
     * - 任何手动调用init()的地方，在结束时必须调用本方法
     * </p>
     *
     * <p>【重要说明】</p>
     * <pre>
     * 必须调用！原因：
     * 1. Tomcat使用线程池，线程复用
     * 2. 如果不清理，下一个请求会沿用前一个请求的TraceId
     * 3. 严重后果：日志串线、监控异常、内存泄漏
     * </pre>
     */
    public static void clear() {
        // 清理MDC中所有由本类设置的值
        MDC.remove(TRACE_ID);
        MDC.remove(SPAN_ID);
        MDC.remove(USER_ID);
        MDC.remove(REQUEST_PATH);
        MDC.remove(REQUEST_START_TIME);
        // 重置Span计数器
        SPAN_COUNTER.remove();
    }

    // ===================== 读取方法 =====================

    /**
     * 获取当前线程的TraceId
     * <p>
     * 【使用场景】
     * - 向外部系统发起调用时，通过Header传递TraceId
     * - 记录日志时手动获取
     * </p>
     *
     * @return TraceId字符串，如果未初始化返回默认值
     */
    public static String getTraceId() {
        String traceId = MDC.get(TRACE_ID);
        return traceId != null ? traceId : DEFAULT_TRACE_ID;
    }

    /**
     * 获取当前线程的SpanId
     *
     * @return SpanId字符串
     */
    public static String getSpanId() {
        String spanId = MDC.get(SPAN_ID);
        return spanId != null ? spanId : "0";
    }

    /**
     * 获取请求已执行时长（毫秒）
     * <p>
     * 【使用场景】
     * - 告警模块根据耗时判断是否需要告警
     * - 性能监控模块记录接口耗时
     * </p>
     *
     * @return 执行时长（毫秒），如果未初始化返回0
     */
    public static long getElapsedTime() {
        String startTimeStr = MDC.get(REQUEST_START_TIME);
        if (startTimeStr == null || startTimeStr.trim().isEmpty()) {
            return 0;
        }
        try {
            long startTime = Long.parseLong(startTimeStr);
            return System.currentTimeMillis() - startTime;
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    // ===================== MDC扩展方法 =====================

    /**
     * 向MDC中添加请求路径信息
     *
     * @param path 请求路径（如：/api/snapshot/list）
     */
    public static void setRequestPath(String path) {
        if (path != null && !path.trim().isEmpty()) {
            MDC.put(REQUEST_PATH, path);
        }
    }

    /**
     * 向MDC中添加自定义键值对
     * <p>
     * 【使用场景】
     * 需要在日志中记录额外的上下文信息（如设备ID、订单号等）
     * </p>
     *
     * @param key   自定义key
     * @param value 自定义值（对象会转为toString()）
     */
    public static void put(String key, Object value) {
        if (key != null && !key.trim().isEmpty() && value != null) {
            MDC.put(key, String.valueOf(value));
        }
    }

    /**
     * 从MDC中获取指定key的值
     *
     * @param key 存储的key
     * @return 对应的值，不存在返回null
     */
    public static String get(String key) {
        return MDC.get(key);
    }

    // ===================== 跨线程传递方法（核心） =====================

    /**
     * 包装Runnable，传递链路追踪上下文到新线程
     * <p>
     * 【解决的问题】
     * MDC是基于ThreadLocal的，直接new Runnable()会丢失TraceId，
     * 导致异步任务的日志没有TraceId，无法与主链路关联。
     * </p>
     *
     * <p>【使用示例】</p>
     * <pre>
     * // 错误写法（TraceId丢失）
     * executorService.submit(() -> {
     *     // 异步任务
     * });
     *
     * // 正确写法（使用包装方法）
     * executorService.submit(TraceContext.wrap(() -> {
     *     // 异步任务，日志中自动携带TraceId
     * }));
     * </pre>
     *
     * @param runnable 需要包装的任务
     * @return 包装后的Runnable（已注入上下文）
     */
    public static Runnable wrap(final Runnable runnable) {
        // 先捕获当前线程的MDC快照（必须在调用线程中捕获）
        final Map<String, String> contextSnapshot = MDC.getCopyOfContextMap();

        return new Runnable() {
            @Override
            public void run() {
                // 进入新线程后：先判断原快照是否存在
                if (contextSnapshot != null) {
                    // 将快照设置到新线程的MDC中
                    MDC.setContextMap(contextSnapshot);
                } else {
                    // 如果原线程没有MDC，初始化一个新的（避免空MDC）
                    init(null);
                }
                try {
                    // 执行实际任务
                    runnable.run();
                } finally {
                    // 清理新线程的MDC（避免线程池复用污染）
                    MDC.clear();
                }
            }
        };
    }

    /**
     * 包装Callable，传递链路追踪上下文到新线程
     * <p>
     * 【与wrap(Runnable)的区别】
     * - Runnable：无返回值
     * - Callable：有返回值，支持抛出异常
     * </p>
     *
     * @param callable 需要包装的任务
     * @param <T>      返回值类型
     * @return 包装后的Callable
     */
    public static <T> Callable<T> wrap(final Callable<T> callable) {
        // 先捕获当前线程的MDC快照（必须在调用线程中捕获）
        final Map<String, String> contextSnapshot = MDC.getCopyOfContextMap();

        return new Callable<T>() {
            @Override
            public T call() throws Exception {
                if (contextSnapshot != null) {
                    MDC.setContextMap(contextSnapshot);
                } else {
                    init(null);
                }
                try {
                    return callable.call();
                } finally {
                    MDC.clear();
                }
            }
        };
    }

    // ===================== 快照方法（用于复杂场景） =====================

    /**
     * 捕获当前MDC上下文的快照
     * <p>
     * 【使用场景】
     * 复杂的异步场景（如跨线程池、多级嵌套），需要手动保存和恢复上下文
     * </p>
     *
     * @return MDC上下文快照Map
     */
    public static Map<String, String> captureSnapshot() {
        Map<String, String> snapshot = MDC.getCopyOfContextMap();
        if (snapshot == null || snapshot.isEmpty()) {
            // 如果MDC为空，至少确保有TraceId
            java.util.HashMap<String, String> map = new java.util.HashMap<String, String>();
            map.put(TRACE_ID, generateTraceId());
            return map;
        }
        return snapshot;
    }

    /**
     * 从快照恢复MDC上下文
     * <p>
     * 【调用时机】
     * 在新的执行线程/上下文中，使用captureSnapshot()获取的快照恢复上下文
     * </p>
     *
     * @param snapshot 通过captureSnapshot()获取的快照
     */
    public static void restoreFromSnapshot(Map<String, String> snapshot) {
        if (snapshot != null && !snapshot.isEmpty()) {
            MDC.setContextMap(snapshot);
        }
    }

    public static void setTraceIdHeaderName(String traceIdHeader) {
    }
}
