package com.ruoyi.common.core.cache;

import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 进程内 L1 缓存（按访问顺序淘汰），仅用于大屏高频轮询的短 TTL 结果。
 *
 * <p>不引入额外依赖，避免与 Java 8 / Spring Boot 2.5 运行时产生版本冲突；语义等价于 Caffeine 的
 * maximumSize + expireAfterWrite 子集。</p>
 */
public class LocalTtlCache
{
    public static class Entry
    {
        private final Object value;
        private final long createdAt;
        private final long expireAt;
        private final boolean empty;

        Entry(Object value, long createdAt, long expireAt, boolean empty)
        {
            this.value = value;
            this.createdAt = createdAt;
            this.expireAt = expireAt;
            this.empty = empty;
        }

        public Object getValue()
        {
            return value;
        }

        public long getCreatedAt()
        {
            return createdAt;
        }

        public long getExpireAt()
        {
            return expireAt;
        }

        public boolean isEmpty()
        {
            return empty;
        }
    }

    private final int maxEntries;
    private final LinkedHashMap<String, Entry> store;

    public LocalTtlCache(int maxEntries)
    {
        this.maxEntries = maxEntries;
        this.store = new LinkedHashMap<String, Entry>(64, 0.75f, true);
    }

    public synchronized Entry get(String key)
    {
        Entry entry = store.get(key);
        if (entry == null)
        {
            return null;
        }
        if (System.currentTimeMillis() > entry.getExpireAt())
        {
            store.remove(key);
            return null;
        }
        return entry;
    }

    public synchronized void put(String key, Object value, long createdAt, long expireAt, boolean empty)
    {
        store.put(key, new Entry(value, createdAt, expireAt, empty));
        evictIfNeeded();
    }

    public synchronized void remove(String key)
    {
        store.remove(key);
    }

    public synchronized void invalidatePrefix(String prefix)
    {
        Iterator<Map.Entry<String, Entry>> it = store.entrySet().iterator();
        while (it.hasNext())
        {
            if (it.next().getKey().startsWith(prefix))
            {
                it.remove();
            }
        }
    }

    public synchronized int size()
    {
        return store.size();
    }

    private void evictIfNeeded()
    {
        if (store.size() <= maxEntries)
        {
            return;
        }
        Iterator<Map.Entry<String, Entry>> it = store.entrySet().iterator();
        while (store.size() > maxEntries && it.hasNext())
        {
            it.next();
            it.remove();
        }
    }
}
