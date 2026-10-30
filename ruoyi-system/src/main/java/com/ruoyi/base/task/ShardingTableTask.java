package com.ruoyi.base.task;

import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.sharding.ShardingTableUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 分表定时任务
 * <p>
 * 功能：提前创建未来月份的空分表，避免查询时表不存在的问题
 * 执行策略：每月1日凌晨1点执行，提前创建未来4个月的分表
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Component
public class ShardingTableTask {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    /**
     * 提前创建分表
     * <p>
     * 定时规则：每月1日凌晨1:00执行
     * 创建策略：提前创建当前月份之后4个月的分表
     * </p>
     */
    @Scheduled(cron = "0 0 1 1 * ?")
    public void createShardingTables() {
        log.info("【分表定时任务】开始执行提前创建分表任务");

        try {
            // 获取未来4个月的分表名列表
            List<String> futureTableNames = ShardingTableUtil.getFutureTableNames(4);
            log.info("【分表定时任务】需要创建的分表数量: {}, 表名列表: {}", futureTableNames.size(), futureTableNames);

            int createdCount = 0;
            int existedCount = 0;

            for (String tableName : futureTableNames) {
                // 检查表是否已存在
                int exists = snapshotFlowMapper.checkTableExists(tableName);

                if (exists > 0) {
                    log.info("【分表定时任务】表 {} 已存在，跳过创建", tableName);
                    existedCount++;
                    continue;
                }

                // 创建分表
                snapshotFlowMapper.createShardingTable(tableName);
                log.info("【分表定时任务】成功创建分表: {}", tableName);
                createdCount++;
            }

            log.info("【分表定时任务】执行完成，已存在表: {}, 新创建表: {}", existedCount, createdCount);

        } catch (Exception e) {
            log.error("【分表定时任务】执行失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 手动触发创建分表（用于测试或初始化）
     *
     * @param months 提前创建的月份数
     * @return 创建结果信息
     */
    public String manualCreateTables(int months) {
        log.info("【分表手动任务】手动触发创建未来 {} 个月的分表", months);

        try {
            List<String> futureTableNames = ShardingTableUtil.getFutureTableNames(months);
            int createdCount = 0;
            int existedCount = 0;

            for (String tableName : futureTableNames) {
                int exists = snapshotFlowMapper.checkTableExists(tableName);

                if (exists > 0) {
                    existedCount++;
                    continue;
                }

                snapshotFlowMapper.createShardingTable(tableName);
                createdCount++;
            }

            return String.format("创建完成，已存在表: %d, 新创建表: %d", existedCount, createdCount);

        } catch (Exception e) {
            log.error("【分表手动任务】执行失败: {}", e.getMessage(), e);
            return "创建失败: " + e.getMessage();
        }
    }
}
