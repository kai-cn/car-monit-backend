package com.ruoyi.base.service.cache;

import com.ruoyi.common.utils.SnowflakeIdUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Date;
import java.util.concurrent.TimeUnit;

/**
 * ID到分区的映射缓存服务
 * <p>
 * 【设计思路】
 * 使用Redis缓存ID与分区的映射关系，避免单条查询时扫描所有分区
 * 
 * <p>【工作原理】</p>
 * <pre>
 * 1. 数据写入时：将ID和对应的分区名缓存到Redis
 * 2. 数据查询时：先从缓存获取分区名，再使用分区提示查询
 * 3. 缓存失效时：降级到时间范围查询或全表扫描
 * </pre>
 * 
 * <p>【缓存策略】</p>
 * - 缓存时间：30天（数据写入后30天内查询频率较高）
 * - 缓存键：partition:mapping:{bigId}
 * - 缓存值：分区名，如 p202508
 * 
 * @author ruoyi
 */
@Slf4j
@Component
public class PartitionMappingCache {

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * 缓存键前缀
     */
    private static final String CACHE_KEY_PREFIX = "partition:mapping:";

    /**
     * 缓存过期时间（30天）
     */
    private static final long CACHE_EXPIRE_DAYS = 30;

    /**
     * 获取ID对应的分区名
     * 
     * <p>【查询流程】</p>
     * <pre>
     * 1. 尝试从Redis缓存获取分区名
     * 2. 如果缓存命中，直接返回分区名
     * 3. 如果缓存未命中，尝试从雪花ID解析分区名
     * 4. 如果解析成功，缓存并返回分区名
     * 5. 如果解析失败，返回null（调用方需要降级处理）
     * </pre>
     * 
     * @param bigId 主键ID
     * @return 分区名（如 p202508），如果无法确定返回null
     */
    public String getPartitionByBigId(String bigId) {
        if (bigId == null || bigId.isEmpty()) {
            return null;
        }

        // 步骤1：尝试从Redis缓存获取
        String cacheKey = buildCacheKey(bigId);
        String partition = redisTemplate.opsForValue().get(cacheKey);
        
        if (partition != null) {
            log.debug("[分区缓存命中] bigId={}, partition={}", bigId, partition);
            return partition;
        }

        // 步骤2：缓存未命中，尝试从雪花ID解析
        partition = SnowflakeIdUtil.parsePartitionFromId(bigId);
        
        if (partition != null) {
            log.debug("[ID解析成功] bigId={}, partition={}", bigId, partition);
            // 将解析结果缓存起来，供后续查询使用
            cachePartitionMapping(bigId, partition);
            return partition;
        }

        // 步骤3：无法确定分区，返回null
        log.debug("[无法确定分区] bigId={}", bigId);
        return null;
    }

    /**
     * 缓存ID与分区的映射关系
     * 
     * <p>【调用时机】</p>
     * - 数据写入成功后调用
     * - 从ID解析出分区后调用
     * 
     * @param bigId 主键ID
     * @param snapshottime 抓拍时间（用于确定分区）
     */
    public void cachePartitionMapping(String bigId, Date snapshottime) {
        if (bigId == null || bigId.isEmpty() || snapshottime == null) {
            return;
        }

        // 生成分区名
        String partition = "p" + new java.text.SimpleDateFormat("yyyyMM").format(snapshottime);
        
        // 缓存到Redis
        String cacheKey = buildCacheKey(bigId);
        redisTemplate.opsForValue().set(
            cacheKey, 
            partition, 
            CACHE_EXPIRE_DAYS, 
            TimeUnit.DAYS
        );
        
        log.debug("[缓存分区映射] bigId={}, partition={}", bigId, partition);
    }

    /**
     * 缓存ID与分区的映射关系（直接传入分区名）
     * 
     * @param bigId 主键ID
     * @param partition 分区名
     */
    public void cachePartitionMapping(String bigId, String partition) {
        if (bigId == null || bigId.isEmpty() || partition == null || partition.isEmpty()) {
            return;
        }

        String cacheKey = buildCacheKey(bigId);
        redisTemplate.opsForValue().set(
            cacheKey, 
            partition, 
            CACHE_EXPIRE_DAYS, 
            TimeUnit.DAYS
        );
        
        log.debug("[缓存分区映射] bigId={}, partition={}", bigId, partition);
    }

    /**
     * 删除ID的分区映射缓存
     * 
     * <p>【调用时机】</p>
     * - 数据删除时调用
     * - 数据更新导致分区变更时调用
     * 
     * @param bigId 主键ID
     */
    public void removePartitionMapping(String bigId) {
        if (bigId == null || bigId.isEmpty()) {
            return;
        }

        String cacheKey = buildCacheKey(bigId);
        Boolean deleted = redisTemplate.delete(cacheKey);
        
        if (deleted != null && deleted) {
            log.debug("[删除分区缓存] bigId={}", bigId);
        }
    }

    /**
     * 获取ID对应的时间范围（用于降级查询）
     * 
     * <p>【使用场景】</p>
     * 当无法确定分区时，使用时间范围查询缩小扫描范围
     * 
     * @param bigId 主键ID
     * @return 时间范围数组，[0]为开始时间，[1]为结束时间
     */
    public Date[] getTimeRangeForFallback(String bigId) {
        return SnowflakeIdUtil.estimateTimeRange(bigId);
    }

    /**
     * 构建缓存键
     */
    private String buildCacheKey(String bigId) {
        return CACHE_KEY_PREFIX + bigId;
    }

    /**
     * 检查缓存是否存在
     * 
     * @param bigId 主键ID
     * @return true=存在，false=不存在
     */
    public boolean hasCachedPartition(String bigId) {
        if (bigId == null || bigId.isEmpty()) {
            return false;
        }

        String cacheKey = buildCacheKey(bigId);
        return Boolean.TRUE.equals(redisTemplate.hasKey(cacheKey));
    }
}
