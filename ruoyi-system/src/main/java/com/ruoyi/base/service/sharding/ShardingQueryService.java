package com.ruoyi.base.service.sharding;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.mapper.ShardingSnapshotFlowMapper;
import com.ruoyi.base.service.sharding.ShardingIdCacheService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;

/**
 * 分表查询服务（优化版）
 * <p>
 * 主要功能：
 * 1. 根据ID查询时，优先从ID中解析时间信息，避免遍历所有分表
 * 2. 提供高效的查询方法
 * 3. 支持降级策略
 * </p>
 */
@Service
public class ShardingQueryService {

    private static final Logger log = LoggerFactory.getLogger(ShardingQueryService.class);

    @Autowired
    private ShardingIdCacheService shardingIdCacheService;

    @Autowired
    private ShardingSnapshotFlowMapper shardingSnapshotFlowMapper;

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper odsRtSzdnSnapshotFlowAddcodeMapper;

    /**
     * 根据ID查询卡口流水（优化版）
     * <p>
     * 优化方案：
     * 1. 从雪花算法ID中解析出时间戳
     * 2. 根据时间戳确定需要查询的分表
     * 3. 直接查询该分表，避免遍历所有分表
     * 4. 如果解析失败，降级到ShardingSphere的标准查询
     * </p>
     *
     * @param bigId ID
     * @return 查询结果
     */
    public OdsRtSzdnSnapshotFlowAddcode selectByIdOptimized(String bigId) {
        // 1. 尝试从ID中解析出分表名称
        Optional<String> tableNameOpt = shardingIdCacheService.getSnapshotFlowTableName(bigId);

        if (tableNameOpt.isPresent()) {
            String tableName = tableNameOpt.get();
            log.debug("根据ID解析出分表: {}, 直接查询", tableName);

            // 2. 使用原Mapper直接查询指定分表
            try {
                OdsRtSzdnSnapshotFlowAddcode result = odsRtSzdnSnapshotFlowAddcodeMapper.selectFromTableById(tableName, bigId);
                if (result != null) {
                    return result;
                }
            } catch (Exception e) {
                log.warn("直接查询分表失败，降级到ShardingSphere标准查询: {}", e.getMessage());
            }
        }

        // 3. 降级到ShardingSphere的标准查询
        log.debug("无法从ID解析分表，使用ShardingSphere标准查询");
        return shardingSnapshotFlowMapper.selectById(bigId);
    }

    /**
     * 根据ID查询卡口流水（时间范围查询优化版）
     * <p>
     * 另一种优化方案：
     * 1. 从ID中解析出时间范围
     * 2. 在该时间范围内进行查询
     * 3. ShardingSphere会根据时间范围确定需要查询的分表
     * </p>
     *
     * @param bigId ID
     * @return 查询结果
     */
    public OdsRtSzdnSnapshotFlowAddcode selectByIdByTimeRange(String bigId) {
        // 1. 尝试从ID中解析出时间范围
        Optional<ShardingIdCacheService.TimeRange> timeRangeOpt = shardingIdCacheService.getSnapshotFlowTimeRange(bigId);

        if (timeRangeOpt.isPresent()) {
            ShardingIdCacheService.TimeRange timeRange = timeRangeOpt.get();
            log.debug("根据ID解析出时间范围: {} - {}", timeRange.getStartTime(), timeRange.getEndTime());

            // 2. 构建查询条件，使用时间范围 + ID查询
            // ShardingSphere会根据时间范围自动路由到对应的分表
            OdsRtSzdnSnapshotFlowAddcode queryParam = new OdsRtSzdnSnapshotFlowAddcode();
            queryParam.setBigId(bigId);
            queryParam.setSnapshottime(timeRange.getStartTime());
            queryParam.setApplyTime2(String.valueOf(timeRange.getEndTime()));

            // 3. 执行查询
            try {
                return shardingSnapshotFlowMapper.selectByCondition(queryParam)
                        .stream()
                        .findFirst()
                        .orElse(null);
            } catch (Exception e) {
                log.warn("时间范围查询失败，降级到标准查询: {}", e.getMessage());
            }
        }

        // 4. 降级到标准查询
        return shardingSnapshotFlowMapper.selectById(bigId);
    }

    /**
     * 插入数据并缓存ID映射关系
     *
     * @param record 记录
     * @return 影响行数
     */
    public int insertWithCache(OdsRtSzdnSnapshotFlowAddcode record) {
        // 1. 先获取当前分表名称
        String tableName = "";
        if (record.getSnapshottime() != null) {
            tableName = "ods_rt_szdn_snapshot_flow_" +
                new java.text.SimpleDateFormat("yyyyMM").format(record.getSnapshottime());
        }

        // 2. 插入数据（ShardingSphere自动路由）
        int result = shardingSnapshotFlowMapper.insert(record);

        // 3. 缓存ID与分表的映射关系
        if (result > 0 && record.getBigId() != null && !tableName.isEmpty()) {
            shardingIdCacheService.cacheSnapshotFlowTableName(record.getBigId(), tableName);
        }

        return result;
    }

    /**
     * 批量插入数据并缓存ID映射关系
     *
     * @param list 记录列表
     * @return 影响行数
     */
    public int batchInsertWithCache(java.util.List<OdsRtSzdnSnapshotFlowAddcode> list) {
        if (list == null || list.isEmpty()) {
            return 0;
        }

        // 1. 批量插入数据
        int result = shardingSnapshotFlowMapper.batchInsert(list);

        // 2. 缓存ID与分表的映射关系
        for (OdsRtSzdnSnapshotFlowAddcode record : list) {
            if (record.getBigId() != null && record.getSnapshottime() != null) {
                String tableName = "ods_rt_szdn_snapshot_flow_" +
                    new java.text.SimpleDateFormat("yyyyMM").format(record.getSnapshottime());
                shardingIdCacheService.cacheSnapshotFlowTableName(record.getBigId(), tableName);
            }
        }

        return result;
    }
}
