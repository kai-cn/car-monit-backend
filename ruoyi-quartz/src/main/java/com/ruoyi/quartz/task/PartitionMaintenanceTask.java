package com.ruoyi.quartz.task;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * GaussDB分区维护定时任务
 *
 * 功能：每月1号自动创建未来N个月的表分区
 * 场景：大表按时间分区后，需提前创建新分区避免数据插入失败
 */
@Slf4j
@Component
public class PartitionMaintenanceTask {

    @Autowired
    private JdbcTemplate jdbcTemplate;

    /**
     * 预创建分区的月数（建议6-12个月）
     */
    private static final int PRE_CREATE_MONTHS = 6;

    /**
     * 需要维护分区的表配置
     * 表名 + 分区键字段名
     */
    private static final String[][] PARTITION_TABLES = {
            {"ods_rt_szdn_snapshot_flow_addcode", "snapshottime"},
            {"ods_lwzxsfsj_fee_records_01", "transtime"},
            {"zdata_trail_fitting", "extime"}
    };

    /**
     * 每月1号凌晨1点执行，预创建未来月份的分区
     *
     * 执行逻辑：
     * 1. 获取当前月份
     * 2. 循环创建未来 N 个月的分区
     * 3. 如果分区已存在，SQL会报错但不影响其他分区
     */
    @Scheduled(cron = "0 0 1 1 * ?")
    public void createFuturePartitions() {
        log.info("[分区维护] 开始创建未来{}个月的分区", PRE_CREATE_MONTHS);

        LocalDate current = LocalDate.now().withDayOfMonth(1);

        for (int i = 1; i <= PRE_CREATE_MONTHS; i++) {
            LocalDate startMonth = current.plusMonths(i);
            LocalDate endMonth = startMonth.plusMonths(1);

            String startDate = startMonth.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
            String endDate = endMonth.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
            String monthSuffix = startMonth.format(DateTimeFormatter.ofPattern("yyyyMM"));

            for (String[] tableConfig : PARTITION_TABLES) {
                String tableName = tableConfig[0];
                String partitionName = tableName + "_p" + monthSuffix;

                String sql = String.format(
                    "CREATE TABLE IF NOT EXISTS %s PARTITION OF %s " +
                    "FOR VALUES FROM ('%s') TO ('%s')",
                    partitionName, tableName, startDate, endDate
                );

                try {
                    jdbcTemplate.execute(sql);
                    log.info("[分区维护] 创建分区成功: {} (范围: {} ~ {})",
                            partitionName, startDate, endDate);
                } catch (Exception e) {
                    // 分区已存在时会报错，忽略
                    log.warn("[分区维护] 分区可能已存在: {} - {}", partitionName, e.getMessage());
                }
            }
        }

        log.info("[分区维护] 分区创建任务完成");
    }

    /**
     * 每周一凌晨2点检查分区健康状态
     */
    @Scheduled(cron = "0 0 2 * * MON")
    public void checkPartitionHealth() {
        log.info("[分区维护] 开始检查分区健康状态");

        for (String[] tableConfig : PARTITION_TABLES) {
            String tableName = tableConfig[0];

            String checkSql = String.format(
                "SELECT inhrelid::regclass AS partition_name " +
                "FROM pg_inherits WHERE inhparent = '%s'::regclass " +
                "ORDER BY partition_name",
                tableName
            );

            try {
                jdbcTemplate.query(checkSql, rs -> {
                    log.info("[分区维护] {} 分区: {}", tableName, rs.getString("partition_name"));
                });
            } catch (Exception e) {
                log.error("[分区维护] 检查表分区失败: {}", tableName, e);
            }
        }

        log.info("[分区维护] 分区健康检查完成");
    }
}
