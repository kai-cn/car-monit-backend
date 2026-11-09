package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.redis.RedisCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * 字典版本号服务：字典写入后 INCR 版本号，缓存 key 带版本，实现主动失效。
 *
 * <p>读取路径：Redis {@code cm:{env}:dict:version:{domain}} → 本地 5 秒缓存 → 默认 0。
 * 写路径（add/edit/remove 字典或码表）调用 {@link #bump(String)}，版本 +1；
 * 各节点最多 5 秒后看到新版本，旧 key 自然过期，不需要逐 key 删除。</p>
 *
 * <p>降级：Redis 不可用时返回本地版本，缓存继续按 TTL 工作（退化为被动失效）。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class DictVersionService
{
    private static final Logger log = LoggerFactory.getLogger(DictVersionService.class);

    public static final String SECTION = "section";

    public static final String TOLL = "toll";

    public static final String GANTRY = "gantry";

    public static final String FWQ = "fwq";

    public static final String ORG = "org";

    public static final String SYS_DICT = "sysdict";

    public static final String PLATE_COLOR = "plate_color";

    private static final long LOCAL_TTL_MS = 5000L;

    @Value("${spring.profiles.active:dev}")
    private String env;

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    private final ConcurrentHashMap<String, VersionEntry> local =
            new ConcurrentHashMap<String, VersionEntry>();

    private final ConcurrentHashMap<String, Long> localBumps = new ConcurrentHashMap<String, Long>();

    public long current(String domain)
    {
        VersionEntry entry = local.get(domain);
        long now = System.currentTimeMillis();
        if (entry != null && entry.expiresAt > now)
        {
            return entry.value;
        }
        long value = readRemote(domain);
        local.put(domain, new VersionEntry(value, now + LOCAL_TTL_MS));
        return value;
    }

    /** 版本号写入：INCR Redis 并立即更新本地版本，保证当前节点后续读使用新 key。 */
    public long bump(String domain)
    {
        VersionEntry previous = local.get(domain);
        long floor = previous == null ? 0L : previous.value;
        long next;
        try
        {
            Long value = redisCache.increment(key(domain), 1L, 365L * 24L * 3600L);
            next = value == null ? floor + 1L : value;
        }
        catch (RuntimeException e)
        {
            next = localBumps.merge(domain, 1L, Long::sum);
            log.warn("[字典版本] Redis INCR 失败，退化为本地版本 domain={} version={} reason={}",
                    domain, next, e.getMessage());
        }
        // 版本必须单调：Redis key 被重置/过期或 Redis 不可用时，都不能回到小于
        // 本节点已知版本的数字，否则 segment() 会切回旧 key，字典变更“复活”旧数据。
        next = Math.max(next, floor + 1L);
        localBumps.put(domain, next);
        local.put(domain, new VersionEntry(next, System.currentTimeMillis() + LOCAL_TTL_MS));
        log.info("[字典版本] 主动失效 domain={} version={}", domain, next);
        return next;
    }

    /** 是否启用版本化 key（可运行期关闭，回退到纯 TTL）。 */
    public boolean enabled()
    {
        return featureSwitchService == null
                || featureSwitchService.isEnabled(FeatureSwitchService.DICT_VERSION);
    }

    /** 版本化缓存段：启用时返回 {@code v{version}:}，关闭时返回空串。 */
    public String segment(String domain)
    {
        return enabled() ? "v" + current(domain) + ":" : "";
    }

    private long readRemote(String domain)
    {
        try
        {
            Object raw = redisCache.getCacheObject(key(domain));
            if (raw != null)
            {
                long remote = Long.parseLong(String.valueOf(raw));
                Long localValue = localBumps.get(domain);
                return localValue == null ? remote : Math.max(remote, localValue);
            }
        }
        catch (NumberFormatException e)
        {
            log.warn("[字典版本] 值非法 domain={}", domain);
        }
        catch (RuntimeException e)
        {
            log.warn("[字典版本] 读取失败 domain={} reason={}", domain, e.getMessage());
        }
        Long localValue = localBumps.get(domain);
        return localValue == null ? 0L : localValue;
    }

    private String key(String domain)
    {
        return "cm:" + env + ":dict:version:" + domain;
    }

    private static class VersionEntry
    {
        private final long value;
        private final long expiresAt;

        VersionEntry(long value, long expiresAt)
        {
            this.value = value;
            this.expiresAt = expiresAt;
        }
    }
}
