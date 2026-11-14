package com.ruoyi.base.sharding;

import org.apache.shardingsphere.sharding.api.sharding.standard.PreciseShardingValue;
import org.apache.shardingsphere.sharding.api.sharding.standard.RangeShardingValue;
import org.apache.shardingsphere.sharding.api.sharding.standard.StandardShardingAlgorithm;

import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 卡口流水表按月分表算法
 * <p>
 * 实现ShardingSphere的StandardShardingAlgorithm接口
 * 支持精确查询(=)和范围查询(BETWEEN)两种模式
 * 分表字段：snapshottime（抓拍时间）
 * 分表规则：按月份分表，表名格式为 ods_rt_szdn_snapshot_flow_yyyyMM
 * </p>
 */
public class SnapshotFlowMonthShardingAlgorithm implements StandardShardingAlgorithm<Date> {

    /**
     * 日期格式化器（使用ThreadLocal保证线程安全）
     * 格式：yyyyMM（如 202508 表示2025年8月）
     */
    private static final ThreadLocal<SimpleDateFormat> DATE_FORMATTER =
            ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyyMM"));

    /**
     * 精确分片（用于等值查询，如 WHERE snapshottime = '2025-08-15'）
     *
     * @param availableTargetNames 配置中定义的所有可用分表名集合
     * @param shardingValue       分片值对象，包含分表字段名和具体值
     * @return 目标分表名
     */
    @Override
    public String doSharding(Collection<String> availableTargetNames,
                           PreciseShardingValue<Date> shardingValue) {
        // 获取分片字段的值（即抓拍时间）
        Date shardValue = shardingValue.getValue();

        // 将日期转换为表名后缀（格式：yyyyMM）
        String tableSuffix = DATE_FORMATTER.get().format(shardValue);

        // 遍历所有可用表名，找到匹配后缀的表
        for (String tableName : availableTargetNames) {
            if (tableName.endsWith(tableSuffix)) {
                return tableName;
            }
        }

        // 如果找不到匹配的表，返回第一个可用表作为兜底
        // 这种情况一般不会发生，除非分表配置有误
        return availableTargetNames.iterator().next();
    }

    /**
     * 范围分片（用于范围查询，如 WHERE snapshottime BETWEEN '2025-08-01' AND '2025-10-31'）
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

        // 计算时间范围内涉及的所有月份后缀
        Set<String> monthSuffixes = getMonthSuffixes(lowerDate, upperDate);

        // 从可用表名中筛选出匹配的表
        for (String tableName : availableTargetNames) {
            for (String suffix : monthSuffixes) {
                if (tableName.endsWith(suffix)) {
                    result.add(tableName);
                    break;
                }
            }
        }

        return result;
    }

    /**
     * 计算时间范围内所有月份的后缀
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @return 月份后缀集合（格式：yyyyMM）
     */
    private Set<String> getMonthSuffixes(Date startDate, Date endDate) {
        Set<String> suffixes = new LinkedHashSet<>();

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);
        // 重置到当月第一天，确保包含起始月份
        startCal.set(Calendar.DAY_OF_MONTH, 1);
        startCal.set(Calendar.HOUR_OF_DAY, 0);
        startCal.set(Calendar.MINUTE, 0);
        startCal.set(Calendar.SECOND, 0);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        // 循环遍历所有月份，直到超过结束日期
        while (!startCal.after(endCal)) {
            String suffix = DATE_FORMATTER.get().format(startCal.getTime());
            suffixes.add(suffix);
            startCal.add(Calendar.MONTH, 1);
        }

        return suffixes;
    }

    /**
     * 算法初始化方法（可用于加载配置等）
     */
    public void init() {
        // 可以在这里做一些初始化工作
        // 例如加载外部配置、初始化缓存等
    }

    /**
     * 算法初始化（ShardingSphere 5.5.x：TypedSPI.getType() 已由接口默认实现提供，
     * 不再由自定义算法覆盖，故此处只保留 init 回调）
     */
    @Override
    public void init(Properties properties) {

    }
}
