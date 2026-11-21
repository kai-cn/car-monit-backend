package com.ruoyi.common.core.cache;

import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.common.core.redis.RedisCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.lang.reflect.Type;
import java.util.Collection;
import java.util.Collections;
import java.util.Date;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;

/**
 * 两级缓存：本地 L1（短 TTL）+ Redis L2（JSON 字符串），带 stale-while-revalidate 与单飞回源。
 *
 * <p>设计依据：docs/architecture-traffic-query-design.md §5.4.4「缓存与降级策略」。</p>
 * <ul>
 *   <li>L1 5-10s / L2 30-60s，超出后进入 stale 窗口，返回旧值并异步刷新；</li>
 *   <li>同一 key 进程内 single-flight，避免缓存击穿；</li>
 *   <li>TTL 加 10%-20% 随机抖动，避免群集同时失效；</li>
 *   <li>空结果按 30s 缓存，防穿透；</li>
 *   <li>单个 payload 超过 1MB 不写 L2，避免 Redis 大 key；</li>
 *   <li>Redis 不可用时自动只走 L1 / 回源，并标记降级原因。</li>
 * </ul>
 *
 * @author car-monit-backend-java-v3
 */
@Component
public class TwoLevelCache
{
    private static final Logger log = LoggerFactory.getLogger(TwoLevelCache.class);

    private static final long MAX_L2_BYTES = 1024L * 1024L;

    private static final long EMPTY_RESULT_TTL_SECONDS = 30L;

    @Autowired
    private RedisCache redisCache;

    @Value("${spring.profiles.active:dev}")
    private String env;

    private final LocalTtlCache local = new LocalTtlCache(2000);

    /**
     * 固定锁条带：同一 key 恒定映射到同一把锁。
     * 不能用「按 key 建锁 + finally remove」——等待中的线程仍持有旧锁对象，
     * remove 后新线程会创建新锁并同时回源，single-flight 失效。
     */
    private static final int LOCK_STRIPES = 256;

    private final Object[] locks = new Object[LOCK_STRIPES];

    private final Set<String> refreshing = Collections.newSetFromMap(new ConcurrentHashMap<String, Boolean>());

    private Object lockFor(String key)
    {
        int index = Math.floorMod(key.hashCode(), LOCK_STRIPES);
        Object lock = locks[index];
        if (lock == null)
        {
            synchronized (locks)
            {
                lock = locks[index];
                if (lock == null)
                {
                    lock = new Object();
                    locks[index] = lock;
                }
            }
        }
        return lock;
    }

    private final ExecutorService refreshPool = Executors.newFixedThreadPool(4, new ThreadFactory()
    {
        @Override
        public Thread newThread(Runnable runnable)
        {
            Thread thread = new Thread(runnable, "two-level-cache-refresh");
            thread.setDaemon(true);
            return thread;
        }
    });

    /**
     * 统一 key 规范：cm:{env}:{domain}:{id}，与设计文档 §4.4 保持一致。
     */
    public String key(String domain, String id)
    {
        return "cm:" + env + ":" + domain + ":" + id;
    }

    /**
     * 读缓存；未命中时回源并写入两级缓存。
     *
     * @param key             缓存 key
     * @param l1Seconds       L1 新鲜期（秒）
     * @param l2Seconds       L2 新鲜期（秒）
     * @param staleSeconds    stale 窗口（秒），L1/L2 的总 TTL = 新鲜期 + stale
     * @param type            反序列化类型（List/Map 请传 TypeReference）
     * @param loader          回源逻辑
     */
    public <T> T get(String key, long l1Seconds, long l2Seconds, long staleSeconds, Type type,
                     Supplier<T> loader)
    {
        long now = System.currentTimeMillis();
        LocalTtlCache.Entry localEntry = local.get(key);
        if (localEntry != null)
        {
            long ageSeconds = Math.max(0L, (now - localEntry.getCreatedAt()) / 1000L);
            if (ageSeconds <= effectiveFresh(l1Seconds, localEntry.isEmpty()))
            {
                markHit(key, "L1", ageSeconds, localEntry.getCreatedAt());
                return cast(localEntry.getValue());
            }
            // stale-while-revalidate：返回旧值，后台刷新
            triggerRefresh(key, l1Seconds, l2Seconds, staleSeconds, loader, localEntry);
            markHit(key, "STALE", ageSeconds, localEntry.getCreatedAt());
            return cast(localEntry.getValue());
        }

        CacheHit<T> l2Hit = readL2(key, type);
        if (l2Hit != null)
        {
            long ageSeconds = Math.max(0L, (now - l2Hit.createdAt) / 1000L);
            local.put(key, l2Hit.value, l2Hit.createdAt,
                    now + localTtlSeconds(l1Seconds, staleSeconds, l2Hit.empty) * 1000L, l2Hit.empty);
            if (ageSeconds <= effectiveFresh(l2Seconds, l2Hit.empty))
            {
                markHit(key, "L2", ageSeconds, l2Hit.createdAt);
                return l2Hit.value;
            }
            triggerRefresh(key, l1Seconds, l2Seconds, staleSeconds, loader, null);
            markHit(key, "STALE", ageSeconds, l2Hit.createdAt);
            return l2Hit.value;
        }

        // 两级都过期：把 grace 窗口内保留的旧值传给 load，回源失败时返回 stale
        LocalTtlCache.Entry retained = local.getRetained(key);
        return load(key, l1Seconds, l2Seconds, staleSeconds, type, loader,
                retained == null ? null : cast(retained.getValue()),
                retained == null ? null : retained.getCreatedAt());
    }

    /**
     * 主动失效（字典/配置变更时调用）。
     */
    public void evict(String key)
    {
        local.remove(key);
        try
        {
            redisCache.deleteObject(key);
        }
        catch (RuntimeException e)
        {
            log.warn("[缓存] 删除 Redis key 失败 key={} reason={}", key, e.getMessage());
        }
    }

    private <T> T load(String key, long l1Seconds, long l2Seconds, long staleSeconds, Type type,
                       Supplier<T> loader, T staleValue, Long staleCreatedAt)
    {
        Object lock = lockFor(key);
        synchronized (lock)
        {
            // double check：并发线程已完成回源
            LocalTtlCache.Entry current = local.get(key);
            if (current != null)
            {
                long ageSeconds = Math.max(0L,
                        (System.currentTimeMillis() - current.getCreatedAt()) / 1000L);
                if (ageSeconds <= effectiveFresh(l1Seconds, current.isEmpty()))
                {
                    markHit(key, "L1", ageSeconds, current.getCreatedAt());
                    return cast(current.getValue());
                }
            }
            CacheHit<T> l2Current = readL2(key, type);
            if (l2Current != null)
            {
                long ageSeconds = Math.max(0L, (System.currentTimeMillis() - l2Current.createdAt) / 1000L);
                local.put(key, l2Current.value, l2Current.createdAt,
                        System.currentTimeMillis()
                                + localTtlSeconds(l1Seconds, staleSeconds, l2Current.empty) * 1000L,
                        l2Current.empty);
                if (ageSeconds <= effectiveFresh(l2Seconds, l2Current.empty))
                {
                    markHit(key, "L2", ageSeconds, l2Current.createdAt);
                    return l2Current.value;
                }
            }

            T value;
            try
            {
                value = loader.get();
            }
            catch (RuntimeException e)
            {
                log.error("[缓存] 回源失败 key={} reason={}", key, e.getMessage(), e);
                // L1 已淘汰但 L2 仍保留旧值时同样作为 stale 兜底，避免 api 故障直接 500
                T fallback = staleValue != null ? staleValue
                        : (l2Current == null ? null : (T) l2Current.value);
                Long fallbackAt = staleValue != null ? staleCreatedAt
                        : (l2Current == null ? null : Long.valueOf(l2Current.createdAt));
                if (fallback != null)
                {
                    CacheContext.get().setLevel("DEGRADED");
                    CacheContext.markDegrade("LOAD_FAILED");
                    markAsOf(fallbackAt);
                    return fallback;
                }
                throw e;
            }
            store(key, value, l1Seconds, l2Seconds, staleSeconds);
            markHit(key, "MISS", 0L, System.currentTimeMillis());
            return value;
        }
    }

    private void triggerRefresh(final String key, final long l1Seconds, final long l2Seconds,
                                final long staleSeconds, final Supplier<?> loader, final Object staleValueHint)
    {
        if (!refreshing.add(key))
        {
            return;
        }
        try
        {
            refreshPool.submit(new Runnable()
            {
                @Override
                public void run()
                {
                Object lock = lockFor(key);
                try
                {
                    synchronized (lock)
                    {
                        LocalTtlCache.Entry current = local.get(key);
                        if (current != null)
                        {
                            long ageSeconds = Math.max(0L,
                                    (System.currentTimeMillis() - current.getCreatedAt()) / 1000L);
                            if (ageSeconds <= effectiveFresh(l1Seconds, current.isEmpty()))
                            {
                                return;
                            }
                        }
                        Object value = loader.get();
                        store(key, value, l1Seconds, l2Seconds, staleSeconds);
                    }
                }
                catch (RuntimeException e)
                {
                    log.warn("[缓存] 异步刷新失败 key={} reason={}", key, e.getMessage());
                }
                finally
                {
                    refreshing.remove(key);
                    CacheContext.clear();
                }
            }
            });
        }
        catch (RuntimeException e)
        {
            // 线程池拒绝/关闭时释放 refreshing 标记，否则该 key 永远不会再异步刷新
            refreshing.remove(key);
            log.warn("[缓存] 异步刷新任务提交失败 key={} reason={}", key, e.getMessage());
        }
    }

    private <T> void store(String key, T value, long l1Seconds, long l2Seconds, long staleSeconds)
    {
        boolean empty = isEmptyValue(value);
        long now = System.currentTimeMillis();
        long l1Fresh = jitteredSeconds(effectiveFresh(l1Seconds, empty));
        long l2Fresh = jitteredSeconds(effectiveFresh(l2Seconds, empty));
        // 空结果只缓存 30s：不再叠加 stale，否则配置的 30s 实际会变成 30s + stale 窗口
        long l1Ttl = empty ? EMPTY_RESULT_TTL_SECONDS : l1Fresh + staleSeconds;
        long l2Ttl = empty ? EMPTY_RESULT_TTL_SECONDS : l2Fresh + staleSeconds;
        local.put(key, value, now, now + l1Ttl * 1000L, empty);
        writeL2(key, value, l2Ttl);
    }

    /**
     * L1 总 TTL：空结果固定 30s；正常结果 = 新鲜期 + stale 窗口。
     */
    private long localTtlSeconds(long freshSeconds, long staleSeconds, boolean empty)
    {
        if (empty)
        {
            return EMPTY_RESULT_TTL_SECONDS;
        }
        return effectiveFresh(freshSeconds, false) + staleSeconds;
    }

    private void writeL2(String key, Object value, long ttlSeconds)
    {
        try
        {
            JSONObject wrapper = new JSONObject();
            wrapper.put("ts", System.currentTimeMillis());
            wrapper.put("empty", isEmptyValue(value));
            wrapper.put("v", value);
            String text = wrapper.toJSONString();
            if (text.length() > MAX_L2_BYTES)
            {
                log.warn("[缓存] payload 超过 1MB，跳过 L2 key={} size={}", key, text.length());
                return;
            }
            redisCache.setCacheObject(key, text, (int) Math.max(1L, ttlSeconds), TimeUnit.SECONDS);
        }
        catch (RuntimeException e)
        {
            log.warn("[缓存] 写 Redis 失败 key={} reason={}", key, e.getMessage());
            MetricsRegistry.increment("cache.l2.write_failed");
            CacheContext.markDegrade("REDIS_UNAVAILABLE");
        }
    }

    private <T> CacheHit<T> readL2(String key, Type type)
    {
        try
        {
            Object raw = redisCache.getCacheObject(key);
            if (raw == null)
            {
                return null;
            }
            JSONObject wrapper = JSONObject.parseObject(String.valueOf(raw));
            if (wrapper == null)
            {
                return null;
            }
            long ts = wrapper.getLongValue("ts", 0L);
            boolean empty = wrapper.getBooleanValue("empty", false);
            T value = wrapper.getObject("v", type);
            if (value == null)
            {
                return null;
            }
            return new CacheHit<T>(value, ts, empty);
        }
        catch (RuntimeException e)
        {
            log.warn("[缓存] 读 Redis 失败 key={} reason={}", key, e.getMessage());
            MetricsRegistry.increment("cache.l2.read_failed");
            CacheContext.markDegrade("REDIS_UNAVAILABLE");
            return null;
        }
    }

    private boolean isEmptyValue(Object value)
    {
        if (value == null)
        {
            return true;
        }
        if (value instanceof Collection)
        {
            return ((Collection<?>) value).isEmpty();
        }
        if (value instanceof Map)
        {
            return ((Map<?, ?>) value).isEmpty();
        }
        return false;
    }

    private long effectiveFresh(long freshSeconds, boolean empty)
    {
        if (empty && freshSeconds > EMPTY_RESULT_TTL_SECONDS)
        {
            return EMPTY_RESULT_TTL_SECONDS;
        }
        return freshSeconds;
    }

    private void markHit(String key, String level, long ageSeconds, long createdAt)
    {
        CacheMeta meta = CacheContext.get();
        meta.setLevel(level);
        meta.setDataAgeSeconds(ageSeconds);
        if (!"MISS".equals(level) && meta.getSource() == null)
        {
            // 缓存命中时原回源来源不可知，统一标记 CACHE，避免 X-Data-Source 缺失
            meta.setSource("CACHE");
        }
        markAsOf(createdAt);
        MetricsRegistry.increment("cache.hit");
        MetricsRegistry.increment("cache.hit." + level);
        log.debug("[缓存] key={} level={} age={}s", key, level, ageSeconds);
    }

    private void markAsOf(Long createdAt)
    {
        if (createdAt != null)
        {
            CacheContext.get().setDataAsOf(new Date(createdAt));
        }
    }

    private long jitteredSeconds(long seconds)
    {
        if (seconds <= 0L)
        {
            return seconds;
        }
        double factor = 1.0d + ThreadLocalRandom.current().nextDouble(0.1d, 0.2d);
        return Math.max(1L, (long) Math.ceil(seconds * factor));
    }

    @SuppressWarnings("unchecked")
    private <T> T cast(Object value)
    {
        return (T) value;
    }

    private static class CacheHit<T>
    {
        private final T value;
        private final long createdAt;
        private final boolean empty;

        CacheHit(T value, long createdAt, boolean empty)
        {
            this.value = value;
            this.createdAt = createdAt;
            this.empty = empty;
        }
    }
}
