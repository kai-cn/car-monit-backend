package com.ruoyi.common.core.cache;

import com.fasterxml.jackson.core.type.TypeReference;
import com.ruoyi.common.core.redis.RedisCache;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * 两级缓存单测：空结果 30s 上限（不再叠加 stale）、回源失败返回 stale、L1 命中不重复回源。
 */
class TwoLevelCacheTest
{
    private static final Type LIST_TYPE = new TypeReference<List<String>>()
    {
    }.getType();

    @Test
    void emptyResultTtlIsCappedAtThirtySecondsInsteadOfThirtyPlusStale()
    {
        StubRedisCache redis = new StubRedisCache();
        TwoLevelCache cache = newCache(redis);

        List<String> result = cache.get("empty", 60L, 120L, 120L, LIST_TYPE,
                ArrayList::new);
        assertTrue(result.isEmpty());

        LocalTtlCache.Entry entry = local(cache).get("empty");
        long ttlMs = entry.getExpireAt() - System.currentTimeMillis();
        // 期望约 30s；若叠加 stale 会变成 150s
        assertTrue(ttlMs <= 31_000L, "空结果 TTL 不应超过 30s，实际 " + ttlMs + "ms");
        assertTrue(ttlMs > 20_000L, "空结果 TTL 不应过短，实际 " + ttlMs + "ms");
    }

    @Test
    void loaderFailureReturnsRetainedStaleValue()
    {
        StubRedisCache redis = new StubRedisCache();
        redis.unavailable = true;
        TwoLevelCache cache = newCache(redis);

        long now = System.currentTimeMillis();
        // 已过期 1s，但仍在 grace 保留窗口内
        local(cache).put("stale", "last-known", now - 10_000L, now - 1_000L, false);

        String value = cache.get("stale", 5L, 30L, 60L, String.class, () -> {
            throw new IllegalStateException("api down");
        });
        assertEquals("last-known", value);
    }

    @Test
    void freshL1HitDoesNotCallLoaderAgain()
    {
        StubRedisCache redis = new StubRedisCache();
        TwoLevelCache cache = newCache(redis);
        AtomicInteger calls = new AtomicInteger();

        List<String> first = cache.get("hit", 60L, 120L, 60L, LIST_TYPE, () -> {
            calls.incrementAndGet();
            return Collections.singletonList("v");
        });
        List<String> second = cache.get("hit", 60L, 120L, 60L, LIST_TYPE, () -> {
            calls.incrementAndGet();
            return Collections.singletonList("v");
        });

        assertEquals(Collections.singletonList("v"), first);
        assertEquals(Collections.singletonList("v"), second);
        assertEquals(1, calls.get());
    }

    private TwoLevelCache newCache(StubRedisCache redis)
    {
        TwoLevelCache cache = new TwoLevelCache();
        inject(cache, "redisCache", redis);
        inject(cache, "env", "test");
        return cache;
    }

    private LocalTtlCache local(TwoLevelCache cache)
    {
        try
        {
            Field field = TwoLevelCache.class.getDeclaredField("local");
            field.setAccessible(true);
            return (LocalTtlCache) field.get(cache);
        }
        catch (ReflectiveOperationException e)
        {
            throw new IllegalStateException("无法读取 local 缓存", e);
        }
    }

    private void inject(Object target, String fieldName, Object value)
    {
        try
        {
            Field field = target.getClass().getDeclaredField(fieldName);
            field.setAccessible(true);
            field.set(target, value);
        }
        catch (ReflectiveOperationException e)
        {
            throw new IllegalStateException("无法注入字段 " + fieldName, e);
        }
    }

    /**
     * 用内存 Map 替代 Redis；{@code unavailable=true} 时模拟 Redis 不可用。
     */
    static class StubRedisCache extends RedisCache
    {
        private final Map<String, Object> store = new ConcurrentHashMap<String, Object>();

        private boolean unavailable;

        @Override
        public <T> void setCacheObject(String key, T value)
        {
            store.put(key, value);
        }

        @Override
        public <T> void setCacheObject(String key, T value, Integer timeout, TimeUnit timeUnit)
        {
            store.put(key, value);
        }

        @SuppressWarnings("unchecked")
        @Override
        public <T> T getCacheObject(String key)
        {
            if (unavailable)
            {
                throw new IllegalStateException("redis down");
            }
            return (T) store.get(key);
        }

        @Override
        public boolean deleteObject(String key)
        {
            store.remove(key);
            return true;
        }
    }
}
