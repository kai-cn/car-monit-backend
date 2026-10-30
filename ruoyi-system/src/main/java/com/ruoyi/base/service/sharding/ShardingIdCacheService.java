package com.ruoyi.base.service.sharding;

import com.ruoyi.common.core.redis.RedisCache;
import org.apache.commons.lang3.time.DateUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Optional;

/**
 * ID-分表映射缓存服务
 * <p>
 * 解决问题：根据ID查询时，ShardingSphere会遍历所有分表，导致性能下降
 * <p>
 * 解决方案：
 * 1. 雪花算法ID包含时间戳，可以从ID中解析出分表信息
 * 2. 对于无法从ID解析时间的情况，使用Redis缓存ID与分表的映射关系
 * 3. 提供高效的查询方法
 * </p>
 */
@Service
public class ShardingIdCacheService {

    private static final Logger log = LoggerFactory.getLogger(ShardingIdCacheService.class);

    @Autowired
    private RedisCache redisCache;

    /**
     * Redis Key前缀
     */
    private static final String SHARDING_ID_CACHE_PREFIX = "sharding:id:cache:";

    /**
     * 缓存过期时间：7天
     */
    private static final long CACHE_EXPIRE_DAYS = 7;

    /**
     * 雪花算法参数
     */
    private static final long SNOWFLAKE_EPOCH = 1672531200000L;  // 2023-01-01
    private static final long TIME_SHIFT = 22;  // 时间戳左移位数

    /**
     * 从雪花算法ID中解析出时间戳
     *
     * @param id 雪花算法ID（Long类型）
     * @return 时间戳（毫秒）
     */
    public Optional<Long> extractTimestampFromId(Long id) {
        if (id == null) {
            return Optional.empty();
        }
        try {
            long timestamp = (id >> TIME_SHIFT) + SNOWFLAKE_EPOCH;
            return Optional.of(timestamp);
        } catch (Exception e) {
            log.warn("无法从ID {} 中解析时间戳: {}", id, e.getMessage());
            return Optional.empty();
        }
    }

    /**
     * 从雪花算法ID中解析出时间戳（String类型）
     *
     * @param idStr 雪花算法ID（String类型）
     * @return 时间戳（毫秒）
     */
    public Optional<Long> extractTimestampFromId(String idStr) {
        try {
            Long id = Long.parseLong(idStr);
            return extractTimestampFromId(id);
        } catch (NumberFormatException e) {
            log.warn("ID {} 不是有效的数字", idStr);
            return Optional.empty();
        }
    }

    /**
     * 根据ID获取卡口流水表的分表名称
     * <p>
     * 优先尝试从ID中解析时间戳，如果失败则从缓存中获取
     * </p>
     *
     * @param bigId 卡口流水表ID
     * @return 分表名称（如 ods_rt_szdn_snapshot_flow_202508）
     */
    public Optional<String> getSnapshotFlowTableName(String bigId) {
        // 1. 尝试从ID中解析时间戳
        Optional<Long> timestampOpt = extractTimestampFromId(bigId);
        if (timestampOpt.isPresent()) {
            Date date = new Date(timestampOpt.get());
            String suffix = new SimpleDateFormat("yyyyMM").format(date);
            return Optional.of("ods_rt_szdn_snapshot_flow_" + suffix);
        }

        // 2. 尝试从缓存中获取
        String cacheKey = SHARDING_ID_CACHE_PREFIX + "snapshot:" + bigId;
        String tableName = redisCache.getCacheObject(cacheKey);
        if (tableName != null) {
            return Optional.of(tableName);
        }

        return Optional.empty();
    }

    /**
     * 根据ID获取费用记录表的分表名称
     * <p>
     * 优先尝试从ID中解析时间戳，如果失败则从缓存中获取
     * </p>
     *
     * @param id 费用记录表ID
     * @return 分表名称（如 ods_lwzxsfsj_fee_records_20250801）
     */
    public Optional<String> getFeeRecordsTableName(String id) {
        // 1. 尝试从ID中解析时间戳
        Optional<Long> timestampOpt = extractTimestampFromId(id);
        if (timestampOpt.isPresent()) {
            Date date = new Date(timestampOpt.get());
            String suffix = new SimpleDateFormat("yyyyMMdd").format(date);
            return Optional.of("ods_lwzxsfsj_fee_records_" + suffix);
        }

        // 2. 尝试从缓存中获取
        String cacheKey = SHARDING_ID_CACHE_PREFIX + "fee:" + id;
        String tableName = redisCache.getCacheObject(cacheKey);
        if (tableName != null) {
            return Optional.of(tableName);
        }

        return Optional.empty();
    }

    /**
     * 缓存卡口流水表ID与分表的映射关系
     *
     * @param bigId     卡口流水表ID
     * @param tableName 分表名称
     */
    public void cacheSnapshotFlowTableName(String bigId, String tableName) {
        String cacheKey = SHARDING_ID_CACHE_PREFIX + "snapshot:" + bigId;
        redisCache.setCacheObject(cacheKey, tableName, (int) CACHE_EXPIRE_DAYS, java.util.concurrent.TimeUnit.DAYS);
        log.debug("缓存卡口流水表ID映射: {} -> {}", bigId, tableName);
    }

    /**
     * 缓存费用记录表ID与分表的映射关系
     *
     * @param id        费用记录表ID
     * @param tableName 分表名称
     */
    public void cacheFeeRecordsTableName(String id, String tableName) {
        String cacheKey = SHARDING_ID_CACHE_PREFIX + "fee:" + id;
        redisCache.setCacheObject(cacheKey, tableName, (int) CACHE_EXPIRE_DAYS, java.util.concurrent.TimeUnit.DAYS);
        log.debug("缓存费用记录表ID映射: {} -> {}", id, tableName);
    }

    /**
     * 从雪花算法ID中解析出卡口流水表分表的时间范围
     * <p>
     * 用于需要通过时间范围查询代替直接ID查询的场景
     * </p>
     *
     * @param id 雪花算法ID
     * @return 分表对应的时间范围（包含开始和结束时间）
     */
    public Optional<TimeRange> getSnapshotFlowTimeRange(String id) {
        Optional<Long> timestampOpt = extractTimestampFromId(id);
        if (timestampOpt.isPresent()) {
            Date date = new Date(timestampOpt.get());
            Date startDate = DateUtils.setDays(DateUtils.setHours(DateUtils.setMinutes(DateUtils.setSeconds(date, 0), 0), 0), 1);
            Date endDate = DateUtils.addMonths(startDate, 1);
            return Optional.of(new TimeRange(startDate, endDate));
        }
        return Optional.empty();
    }

    /**
     * 从雪花算法ID中解析出费用记录表分表的时间范围
     *
     * @param id 雪花算法ID
     * @return 分表对应的时间范围（包含开始和结束时间）
     */
    public Optional<TimeRange> getFeeRecordsTimeRange(String id) {
        Optional<Long> timestampOpt = extractTimestampFromId(id);
        if (timestampOpt.isPresent()) {
            Date date = new Date(timestampOpt.get());
            Date startDate = DateUtils.setHours(DateUtils.setMinutes(DateUtils.setSeconds(date, 0), 0), 0);
            Date endDate = DateUtils.addDays(startDate, 1);
            return Optional.of(new TimeRange(startDate, endDate));
        }
        return Optional.empty();
    }

    /**
     * 时间范围封装类
     */
    public static class TimeRange {
        private final Date startTime;
        private final Date endTime;

        public TimeRange(Date startTime, Date endTime) {
            this.startTime = startTime;
            this.endTime = endTime;
        }

        public Date getStartTime() {
            return startTime;
        }

        public Date getEndTime() {
            return endTime;
        }
    }
}
