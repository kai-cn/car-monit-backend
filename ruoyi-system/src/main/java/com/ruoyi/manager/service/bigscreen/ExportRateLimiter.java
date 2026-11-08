package com.ruoyi.manager.service.bigscreen;

import com.ruoyi.common.core.cache.CacheContext;
import com.ruoyi.common.core.redis.RedisCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * 导出提交/下载限流。固定窗口 + Redis 原子自增；Redis 不可用时 fail-open（不阻断业务），并标记降级。
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class ExportRateLimiter
{
    private static final Logger log = LoggerFactory.getLogger(ExportRateLimiter.class);

    @Autowired
    private RedisCache redisCache;

    @Value("${spring.profiles.active:dev}")
    private String env;

    public boolean tryAcquire(String scope, Long userId, int limit, int windowSeconds)
    {
        long bucket = System.currentTimeMillis() / (windowSeconds * 1000L);
        String key = "cm:" + env + ":export:rate:" + scope + ":" + userId + ":" + bucket;
        try
        {
            Long count = redisCache.increment(key, 1L, windowSeconds + 5L);
            return count == null || count <= limit;
        }
        catch (RuntimeException e)
        {
            log.warn("[导出限流] Redis 不可用，放行 scope={} user={} reason={}",
                    scope, userId, e.getMessage());
            CacheContext.markDegrade("REDIS_UNAVAILABLE");
            return true;
        }
    }
}
