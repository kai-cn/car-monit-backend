package com.ruoyi.admin.config;

import com.ruoyi.base.sharding.SnapshotFlowMonthShardingAlgorithm;
import com.ruoyi.base.sharding.FeeRecordsDayShardingAlgorithm;
import org.apache.shardingsphere.driver.api.ShardingSphereDataSourceFactory;
import org.apache.shardingsphere.infra.algorithm.core.config.AlgorithmConfiguration;
import org.apache.shardingsphere.sharding.api.config.ShardingRuleConfiguration;
import org.apache.shardingsphere.sharding.api.config.rule.ShardingTableRuleConfiguration;
import org.apache.shardingsphere.sharding.api.config.strategy.sharding.StandardShardingStrategyConfiguration;
import org.apache.shardingsphere.sharding.api.config.strategy.keygen.KeyGenerateStrategyConfiguration;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import javax.sql.DataSource;
import java.sql.SQLException;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

/**
 * ShardingSphere分表配置类（Java 8兼容版）
 * <p>
 * 使用ShardingSphere 5.2.1版本API，确保Java 8语法兼容
 * <p>
 * 配置内容：
 * 1. 只对需要分表的表应用分表规则，其他表直接走默认数据源
 * 2. 卡口流水表：按月分表，分表字段：snapshottime
 * 3. 费用记录表：按日分表，分表字段：record_time
 * </p>
 */
@Configuration
@ConditionalOnProperty(prefix = "sharding", name = "enabled", havingValue = "true", matchIfMissing = false)
public class ShardingSphereConfig {

    @Value("${spring.datasource.druid.master.url}")
    private String masterUrl;

    @Value("${spring.datasource.druid.master.username}")
    private String masterUsername;

    @Value("${spring.datasource.druid.master.password}")
    private String masterPassword;

    @Value("${spring.datasource.driverClassName}")
    private String driverClassName;

    /**
     * 创建ShardingSphere数据源
     * <p>
     * 只对配置了分表规则的表应用分片逻辑，其他表直接路由到默认数据源
     * </p>
     *
     * @return ShardingSphere数据源
     * @throws SQLException SQL异常
     */
    @Bean
    @Primary
    public DataSource shardingDataSource() throws SQLException {
        // 1. 配置真实数据源
        Map<String, DataSource> dataSourceMap = createDataSourceMap();

        // 2. 配置分表规则
        ShardingRuleConfiguration shardingRuleConfig = createShardingRuleConfig();

        // 3. 创建ShardingSphere数据源
        Properties props = new Properties();
        props.setProperty("sql-show", "true");  // 显示SQL日志

        return ShardingSphereDataSourceFactory.createDataSource(dataSourceMap, Collections.singleton(shardingRuleConfig), props);
    }

    /**
     * 创建数据源映射
     * ds: 主数据源
     */
    private Map<String, DataSource> createDataSourceMap() {
        Map<String, DataSource> dataSourceMap = new HashMap<String, DataSource>();

        // 配置主库数据源（使用Druid连接池）
        com.alibaba.druid.pool.DruidDataSource dataSource = new com.alibaba.druid.pool.DruidDataSource();
        dataSource.setDriverClassName(driverClassName);
        // 移除p6spy包装，使用原始JDBC URL
        String jdbcUrl = masterUrl.replace("jdbc:p6spy:", "jdbc:");
        dataSource.setUrl(jdbcUrl);
        dataSource.setUsername(masterUsername);
        dataSource.setPassword(masterPassword);

        // 连接池配置
        dataSource.setInitialSize(5);
        dataSource.setMinIdle(10);
        dataSource.setMaxActive(200);
        dataSource.setMaxWait(60000);
        dataSource.setValidationQuery("SELECT 1");
        dataSource.setTestWhileIdle(true);

        dataSourceMap.put("ds", dataSource);

        return dataSourceMap;
    }

    /**
     * 创建分表规则配置
     * <p>
     * 只对需要分表的表配置分片规则，其他表直接走默认数据源
     * </p>
     */
    private ShardingRuleConfiguration createShardingRuleConfig() {
        ShardingRuleConfiguration shardingRuleConfig = new ShardingRuleConfiguration();

        // ========== 1. 配置分表算法 ==========
        Map<String, AlgorithmConfiguration> shardingAlgorithms = new HashMap<>();

        // 1.1 卡口流水表 - 按月分表算法
        Properties snapshotFlowProps = new Properties();
        snapshotFlowProps.put("strategy", "standard");
        snapshotFlowProps.put("algorithm-class-name", SnapshotFlowMonthShardingAlgorithm.class.getName());
        AlgorithmConfiguration snapshotFlowAlgorithmConfig = new AlgorithmConfiguration("CLASS_BASED", snapshotFlowProps);
        shardingAlgorithms.put("snapshot-flow-month-algorithm", snapshotFlowAlgorithmConfig);

        // 1.2 费用记录表 - 按日分表算法
        Properties feeRecordsProps = new Properties();
        feeRecordsProps.put("strategy", "standard");
        feeRecordsProps.put("algorithm-class-name", FeeRecordsDayShardingAlgorithm.class.getName());
        AlgorithmConfiguration feeRecordsAlgorithmConfig = new AlgorithmConfiguration("CLASS_BASED", feeRecordsProps);
        shardingAlgorithms.put("fee-records-day-algorithm", feeRecordsAlgorithmConfig);

        shardingRuleConfig.setShardingAlgorithms(shardingAlgorithms);

        // ========== 2. 配置主键生成策略 ==========
        Map<String, AlgorithmConfiguration> keyGenerators = new HashMap<>();
        Properties snowflakeProps = new Properties();
        snowflakeProps.put("worker-id", "1");
        AlgorithmConfiguration snowflakeKeyGeneratorConfig = new AlgorithmConfiguration("SNOWFLAKE", snowflakeProps);
        keyGenerators.put("snowflake", snowflakeKeyGeneratorConfig);
        shardingRuleConfig.setKeyGenerators(keyGenerators);

        // ========== 3. 配置卡口流水表分表规则 ==========
        ShardingTableRuleConfiguration snapshotFlowTableRuleConfig = createSnapshotFlowTableRule();
        shardingRuleConfig.getTables().add(snapshotFlowTableRuleConfig);

        // ========== 4. 配置费用记录表分表规则 ==========
        ShardingTableRuleConfiguration feeRecordsTableRuleConfig = createFeeRecordsTableRule();
        shardingRuleConfig.getTables().add(feeRecordsTableRuleConfig);

        // ========== 5. 配置默认数据源（重要！！！ ==========
        // 未配置分表规则的表，默认使用ds数据源，直接访问原表，不做分表处理
//        shardingRuleConfig.setDefaultDataSourceName("ds");

        return shardingRuleConfig;
    }

    /**
     * 创建卡口流水表分表规则
     */
    private ShardingTableRuleConfiguration createSnapshotFlowTableRule() {

        // 实际数据节点（定义分表范围）
        // 格式：数据源.表名_年份月份
        // 配置2025-2099年的分表
        StringBuilder dataNodes = new StringBuilder();
        // 生成1-9月的表名模式
        for (int year = 2025; year <= 2099; year++) {
            for (int month = 1; month <= 9; month++) {
                if (dataNodes.length() > 0) {
                    dataNodes.append(",");
                }
                dataNodes.append("ds.ods_rt_szdn_snapshot_flow_").append(year).append("0").append(month);
            }
            for (int month = 10; month <= 12; month++) {
                if (dataNodes.length() > 0) {
                    dataNodes.append(",");
                }
                dataNodes.append("ds.ods_rt_szdn_snapshot_flow_").append(year).append(month);
            }
        }

        ShardingTableRuleConfiguration tableRuleConfig = new ShardingTableRuleConfiguration("ods_rt_szdn_snapshot_flow",dataNodes.toString());



        // 分表策略：使用snapshottime字段进行分片
        StandardShardingStrategyConfiguration tableShardingStrategy =
                new StandardShardingStrategyConfiguration("snapshottime", "snapshot-flow-month-algorithm");
        tableRuleConfig.setTableShardingStrategy(tableShardingStrategy);

        // 主键生成策略
        KeyGenerateStrategyConfiguration keyGenerateStrategy =
                new KeyGenerateStrategyConfiguration("big_id", "snowflake");
        tableRuleConfig.setKeyGenerateStrategy(keyGenerateStrategy);

        return tableRuleConfig;
    }

    /**
     * 创建费用记录表分表规则
     */
    private ShardingTableRuleConfiguration createFeeRecordsTableRule() {
        // 实际数据节点（定义分表范围）
        // 配置2025-2099年的分表，按日分表
        StringBuilder dataNodes = new StringBuilder();
        for (int year = 2025; year <= 2099; year++) {
            for (int month = 1; month <= 12; month++) {
                int daysInMonth = getDaysInMonth(year, month);
                for (int day = 1; day <= daysInMonth; day++) {
                    if (dataNodes.length() > 0) {
                        dataNodes.append(",");
                    }
                    String monthStr = month < 10 ? "0" + month : String.valueOf(month);
                    String dayStr = day < 10 ? "0" + day : String.valueOf(day);
                    dataNodes.append("ds.ods_lwzxsfsj_fee_records_").append(year).append(monthStr).append(dayStr);
                }
            }
        }

        ShardingTableRuleConfiguration tableRuleConfig = new ShardingTableRuleConfiguration("ods_lwzxsfsj_fee_records", dataNodes.toString());

        // 分表策略：使用record_time字段进行分片
        StandardShardingStrategyConfiguration tableShardingStrategy =
                new StandardShardingStrategyConfiguration("record_time", "fee-records-day-algorithm");
        tableRuleConfig.setTableShardingStrategy(tableShardingStrategy);

        // 主键生成策略
        KeyGenerateStrategyConfiguration keyGenerateStrategy =
                new KeyGenerateStrategyConfiguration("id", "snowflake");
        tableRuleConfig.setKeyGenerateStrategy(keyGenerateStrategy);

        return tableRuleConfig;
    }

    /**
     * 获取指定年月的天数
     */
    private int getDaysInMonth(int year, int month) {
        switch (month) {
            case 1:
            case 3:
            case 5:
            case 7:
            case 8:
            case 10:
            case 12:
                return 31;
            case 4:
            case 6:
            case 9:
            case 11:
                return 30;
            case 2:
                // 判断闰年
                if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0) {
                    return 29;
                } else {
                    return 28;
                }
            default:
                return 30;
        }
    }
}
