package com.ruoyi.base.sharding;

import org.apache.shardingsphere.sharding.api.sharding.standard.PreciseShardingValue;
import org.apache.shardingsphere.sharding.api.sharding.standard.RangeShardingValue;
import org.apache.shardingsphere.sharding.api.sharding.standard.StandardShardingAlgorithm;

import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 费用记录表按日分表算法
 * <p>
 * 实现ShardingSphere的StandardShardingAlgorithm接口
 * 支持精确查询(=)和范围查询(BETWEEN)两种模式
 * 分表字段：record_time（记录时间）
 * 分表规则：按日分表，表名格式为 ods_lwzxsfsj_fee_records_yyyyMMdd
 * </p>
 */
public class FeeRecordsDayShardingAlgorithm implements StandardShardingAlgorithm<Date> {

    /**
     * 日期格式化器（使用ThreadLocal保证线程安全）
     * 格式：yyyyMMdd（如 20250801 表示2025年8月1日）
     */
    private static final ThreadLocal<SimpleDateFormat> DATE_FORMATTER =
            ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyyMMdd"));

    /**
     * 精确分片（用于等值查询，如 WHERE record_time = '2025-08-01'）
     *
     * @param availableTargetNames 配置中定义的所有可用分表名集合
     * @param shardingValue       分片值对象，包含分表字段名和具体值
     * @return 目标分表名
     */
    @Override
    public String doSharding(Collection<String> availableTargetNames,
                           PreciseShardingValue<Date> shardingValue) {
        // 获取分片字段的值（即记录时间）
        Date shardValue = shardingValue.getValue();

        // 将日期转换为表名后缀（格式：yyyyMMdd）
        String tableSuffix = DATE_FORMATTER.get().format(shardValue);

        // 遍历所有可用表名，找到匹配后缀的表
        for (String tableName : availableTargetNames) {
            if (tableName.endsWith(tableSuffix)) {
                return tableName;
            }
        }

        // 如果找不到匹配的表，返回第一个可用表作为兜底
        return availableTargetNames.iterator().next();
    }

    /**
     * 范围分片（用于范围查询，如 WHERE record_time BETWEEN '2025-08-01' AND '2025-08-10'）
     *
     * @param availableTargetNames 可用的目标表名集合
     * @param shardingValue       范围分片值，包含起始值和结束值
     * @return 需要查询的所有分表名集合
     */
    @Override
    public Collection<String> doSharding(Collection<String> availableTargetNames,
                                       RangeShardingValue<Date> shardingValue) {
        // 使用LinkedHashSet保持插入顺序
        Set<String> result = new LinkedHashSet<>();

        // 获取范围边界
        Date lowerDate = shardingValue.getValueRange().lowerEndpoint();
        Date upperDate = shardingValue.getValueRange().upperEndpoint();

        // 边界检查
        if (lowerDate == null || upperDate == null) {
            return result;
        }

        // 计算时间范围内涉及的所有日期后缀
        Set<String> daySuffixes = getDaySuffixes(lowerDate, upperDate);

        // 从可用表名中筛选出匹配的表
        for (String tableName : availableTargetNames) {
            for (String suffix : daySuffixes) {
                if (tableName.endsWith(suffix)) {
                    result.add(tableName);
                    break;
                }
            }
        }

        return result;
    }

    /**
     * 计算时间范围内所有日期的后缀
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @return 日期后缀集合（格式：yyyyMMdd）
     */
    private Set<String> getDaySuffixes(Date startDate, Date endDate) {
        Set<String> suffixes = new LinkedHashSet<>();

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);
        // 重置到当天开始，确保包含起始日期
        startCal.set(Calendar.HOUR_OF_DAY, 0);
        startCal.set(Calendar.MINUTE, 0);
        startCal.set(Calendar.SECOND, 0);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        // 循环遍历所有日期，直到超过结束日期
        while (!startCal.after(endCal)) {
            String suffix = DATE_FORMATTER.get().format(startCal.getTime());
            suffixes.add(suffix);
            startCal.add(Calendar.DAY_OF_MONTH, 1);
        }

        return suffixes;
    }

    /**
     * 算法初始化方法（可用于加载配置等）
     */
    public void init() {
        // 可以在这里做一些初始化工作
    }

    /**
     * 算法初始化（ShardingSphere 5.5.x：TypedSPI.getType() 已由接口默认实现提供，
     * 不再由自定义算法覆盖，故此处只保留 init 回调）
     */
    @Override
    public void init(Properties properties) {

    }
}
