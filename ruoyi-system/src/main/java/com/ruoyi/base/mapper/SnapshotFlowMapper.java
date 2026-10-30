package com.ruoyi.base.mapper;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Date;
import java.util.List;

/**
 * 卡口流水分区查询Mapper接口
 * <p>
 * 【设计说明】
 * 支持MySQL分区表的查询操作，包括：
 * 1. 单分区查询（使用分区提示）
 * 2. 跨分区查询
 * 3. 分页查询
 * 4. 计数查询
 * </p>
 * 
 * @author ruoyi
 */
@Mapper
public interface SnapshotFlowMapper {

    /**
     * 根据ID查询（使用分区提示）
     * 
     * <p>【使用场景】</p>
     * 单条记录查询时，已知分区名，使用分区提示直接查询目标分区，避免全表扫描
     * 
     * @param bigId 主键ID
     * @param snapshottime 抓拍时间
     * @param partition 分区名（如 p202508）
     * @return 记录
     */
    OdsRtSzdnSnapshotFlowAddcode selectByIdWithPartition(
            @Param("bigId") String bigId,
            @Param("snapshottime") Date snapshottime,
            @Param("partition") String partition);

    /**
     * 根据ID和时间范围查询（降级查询）
     * 
     * <p>【使用场景】</p>
     * 当无法确定分区时，使用时间范围查询缩小扫描范围
     * 
     * @param bigId 主键ID
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 记录
     */
    OdsRtSzdnSnapshotFlowAddcode selectByIdWithTimeRange(
            @Param("bigId") String bigId,
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime);

    /**
     * 根据ID查询（全表扫描，最坏情况）
     * 
     * <p>【使用场景】</p>
     * 无法确定分区且无法使用时间范围时的兜底查询
     * 
     * @param bigId 主键ID
     * @return 记录
     */
    OdsRtSzdnSnapshotFlowAddcode selectById(@Param("bigId") String bigId);

    /**
     * 查询指定分区的数据
     * 
     * <p>【使用场景】</p>
     * 跨月份查询时，并发查询每个分区的数据
     * 
     * @param partition 分区名
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> queryByPartition(
            @Param("partition") String partition,
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime);

    /**
     * 查询指定分区的数据（带偏移量）
     * 
     * <p>【使用场景】</p>
     * 跨分区分页查询时，从指定偏移量开始获取数据
     * 
     * @param partition 分区名
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @param offset 偏移量
     * @param limit 每页大小
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> queryByPartitionWithOffset(
            @Param("partition") String partition,
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime,
            @Param("offset") int offset,
            @Param("limit") int limit);

    /**
     * 统计指定分区的记录数
     * 
     * <p>【使用场景】</p>
     * 跨分区分页查询时，估算每个分区的记录数，定位起始分区
     * 
     * @param partition 分区名
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 记录数
     */
    long countByPartition(
            @Param("partition") String partition,
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime);

    /**
     * 根据时间范围查询（自动分区裁剪）
     * 
     * <p>【使用场景】</p>
     * 普通的时间范围查询，MySQL会自动进行分区裁剪
     * 
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByTimeRange(
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime);

    /**
     * 根据时间范围分页查询
     * 
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @param offset 偏移量
     * @param limit 每页大小
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByTimeRangeWithPage(
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime,
            @Param("offset") int offset,
            @Param("limit") int limit);

    /**
     * 统计时间范围内的记录数
     * 
     * @param startTime 开始时间
     * @param endTime 结束时间
     * @return 记录数
     */
    long countByTimeRange(
            @Param("startTime") Date startTime,
            @Param("endTime") Date endTime);
}
