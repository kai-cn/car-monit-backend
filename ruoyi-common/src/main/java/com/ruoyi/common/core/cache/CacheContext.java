package com.ruoyi.common.core.cache;

import com.ruoyi.common.core.metrics.MetricsRegistry;

/**
 * 请求级缓存元数据上下文。
 *
 * <p>大屏接口在读取缓存/回源/降级时写入元数据，由响应过滤器统一输出响应头并在请求结束时清理。</p>
 */
public final class CacheContext
{
    private static final ThreadLocal<CacheMeta> HOLDER = new ThreadLocal<CacheMeta>();

    private CacheContext()
    {
    }

    public static CacheMeta get()
    {
        CacheMeta meta = HOLDER.get();
        if (meta == null)
        {
            meta = new CacheMeta();
            HOLDER.set(meta);
        }
        return meta;
    }

    /**
     * 不创建新对象，只读取已存在的元数据，避免过滤器为无关请求创建 ThreadLocal。
     */
    public static CacheMeta peek()
    {
        return HOLDER.get();
    }

    public static void clear()
    {
        HOLDER.remove();
    }

    public static void markSource(String source)
    {
        get().setSource(source);
    }

    public static void markDegrade(String reason)
    {
        get().setDegradeReason(reason);
        if (reason != null)
        {
            MetricsRegistry.increment("degrade");
            MetricsRegistry.increment("degrade." + reason);
        }
    }
}
