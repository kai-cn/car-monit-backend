package com.ruoyi.base.service.sharding;

import com.ruoyi.base.sharding.ShardingConfig;

import java.util.Date;
import java.util.List;

/**
 * 通用分表同步服务接口
 * <p>
 * 定义分表同步的标准接口，所有需要分表同步的表都应实现此接口
 * </p>
 *
 * @param <T> 实体类型
 */
public interface ShardingSyncService<T> {

    /**
     * 获取表名前缀
     *
     * @return 表名前缀
     */
    String getTablePrefix();

    /**
     * 获取分表配置
     *
     * @return 分表配置
     */
    ShardingConfig.TableShardingConfig getShardingConfig();

    /**
     * 从源数据库查询数据
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @param pageNum   页码
     * @param pageSize  每页大小
     * @return 数据列表
     */
    List<T> fetchFromSource(Date startDate, Date endDate, int pageNum, int pageSize);

    /**
     * 获取源数据总数
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @return 数据总数
     */
    long getSourceCount(Date startDate, Date endDate);

    /**
     * 获取分表字段值
     *
     * @param entity 实体对象
     * @return 分表字段值（通常是日期类型）
     */
    Date getShardingFieldValue(T entity);

    /**
     * 批量插入到分表
     *
     * @param tableName 分表名
     * @param list      数据列表
     */
    void batchInsertToTable(String tableName, List<T> list);

    /**
     * 检查分表是否存在
     *
     * @param tableName 分表名
     * @return 是否存在
     */
    boolean checkTableExists(String tableName);

    /**
     * 创建分表
     *
     * @param tableName 分表名
     */
    void createShardingTable(String tableName);

    /**
     * 获取目标表中指定时间范围的数据总数
     *
     * @param tableName 分表名
     * @return 数据总数
     */
    long getTargetCount(String tableName);

    /**
     * 获取目标表中最新的分表字段值
     *
     * @param tableName 分表名
     * @return 最新的分表字段值
     */
    Date getMaxShardingFieldValue(String tableName);

    /**
     * 执行全量同步
     * <p>
     * 从源数据库同步所有历史数据到目标分表
     * </p>
     *
     * @return 同步记录数
     */
    int syncFullData();

    /**
     * 执行增量同步
     * <p>
     * 同步当前周期的新增数据
     * </p>
     *
     * @return 同步记录数
     */
    int syncIncrementalData();

    /**
     * 同步指定时间范围的数据
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @return 同步记录数
     */
    int syncByDateRange(Date startDate, Date endDate);

    /**
     * 同步指定周期的数据
     *
     * @param period 周期标识（如 202508 表示2025年8月）
     * @return 同步记录数
     */
    int syncByPeriod(String period);

    /**
     * 提前创建未来N个周期的分表
     *
     * @param periods 周期数
     */
    void preCreateTables(int periods);
}
