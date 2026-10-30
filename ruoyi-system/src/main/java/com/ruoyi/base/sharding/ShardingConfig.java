package com.ruoyi.base.sharding;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

/**
 * 分表配置类
 * <p>
 * 支持配置多个需要分表的表，每个表可以独立配置分表策略
 * </p>
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "sharding")
public class ShardingConfig {

    /**
     * 分表策略类型
     */
    public enum ShardingStrategy {
        /**
         * 按月分表
         */
        MONTHLY,
        
        /**
         * 按日分表
         */
        DAILY,
        
        /**
         * 按季度分表
         */
        QUARTERLY,
        
        /**
         * 按年分表
         */
        YEARLY
    }

    /**
     * 分表配置映射
     * key: 表名前缀（如 ods_rt_szdn_snapshot_flow）
     * value: 该表的分表配置
     */
    private Map<String, TableShardingConfig> tables = new HashMap<>();

    /**
     * 单表分表配置
     */
    @Data
    public static class TableShardingConfig {
        /**
         * 分表策略
         */
        private ShardingStrategy strategy = ShardingStrategy.MONTHLY;

        /**
         * 分表字段名（用于确定数据所属分表）
         */
        private String shardingField = "snapshottime";

        /**
         * 分表字段类型（DATE, TIMESTAMP, STRING）
         */
        private String fieldType = "DATE";

        /**
         * 表名分隔符（默认下划线）
         */
        private String tableSeparator = "_";

        /**
         * 是否自动创建分表
         */
        private boolean autoCreateTable = true;

        /**
         * 是否启用同步
         */
        private boolean syncEnabled = true;

        /**
         * 同步批量大小
         */
        private int syncBatchSize = 1000;

        /**
         * 提前创建未来几个周期的分表
         */
        private int preCreatePeriods = 4;

        /**
         * 源数据服务Bean名称（用于从源数据库查询数据）
         */
        private String sourceServiceBean;

        /**
         * 目标Mapper Bean名称（用于写入目标分表）
         */
        private String targetMapperBean;
    }

    /**
     * 获取指定表的分表配置
     *
     * @param tablePrefix 表名前缀
     * @return 分表配置，如果未配置则返回默认配置
     */
    public TableShardingConfig getTableConfig(String tablePrefix) {
        return tables.getOrDefault(tablePrefix, createDefaultConfig());
    }

    /**
     * 创建默认分表配置
     */
    private TableShardingConfig createDefaultConfig() {
        TableShardingConfig config = new TableShardingConfig();
        config.setStrategy(ShardingStrategy.MONTHLY);
        config.setShardingField("snapshottime");
        config.setFieldType("DATE");
        config.setTableSeparator("_");
        config.setAutoCreateTable(true);
        config.setSyncEnabled(true);
        config.setSyncBatchSize(1000);
        config.setPreCreatePeriods(4);
        return config;
    }
}
