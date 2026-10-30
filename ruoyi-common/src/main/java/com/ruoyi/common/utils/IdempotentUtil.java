package com.ruoyi.common.utils;

import com.ruoyi.common.core.redis.RedisCache;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.concurrent.TimeUnit;

/**
 * 幂等性工具类
 * <p>
 * 用途：基于Redis实现分布式幂等性控制，防止重复消费Kafka消息
 * 核心原理：
 * 1. 使用Redis的SETNX命令（原子操作）标记消息已处理
 * 2. 设置过期时间，避免Redis内存无限增长
 * 3. 处理失败时移除标记，允许重试
 * </p>
 *
 * @author ruoyi
 */
@Component
public class IdempotentUtil {

    @Autowired
    private RedisCache redisCache;

    /** Redis键前缀，用于隔离不同业务的幂等性控制 */
    @Value("${idempotent.redis.prefix}")
    private String idempotentPrefix;

    /** 幂等性标记过期时间（秒），默认86400秒=24小时 */
    @Value("${idempotent.redis.expire-time:86400}")
    private long expireTime;

    /**
     * 检查并设置幂等性标记
     * <p>
     * 用途：原子性地检查消息是否已处理，如果未处理则设置标记
     * 实现原理：使用Redis的SETNX命令，如果key不存在则设置并返回true
     *
     * @param key 幂等性键，通常使用消息的唯一ID（如bigId）
     * @return true=消息未处理，可以继续处理；false=消息已处理，跳过
     */
    public boolean checkAndSet(String key) {
        String redisKey = idempotentPrefix + key;
        Boolean result = redisCache.setCacheObjectIfAbsent(redisKey, "1", expireTime, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(result);
    }

    /**
     * 检查消息是否已处理
     * <p>
     * 用途：仅查询消息处理状态，不做任何修改
     *
     * @param key 幂等性键
     * @return true=已处理；false=未处理
     */
    public boolean isProcessed(String key) {
        String redisKey = idempotentPrefix + key;
        return redisCache.getCacheObject(redisKey) != null;
    }

    /**
     * 移除幂等性标记
     * <p>
     * 用途：消息处理失败时调用，允许后续重试
     * 场景：Kafka消息处理失败，需要回滚幂等性状态
     *
     * @param key 幂等性键
     */
    public void remove(String key) {
        String redisKey = idempotentPrefix + key;
        redisCache.deleteObject(redisKey);
    }
}
