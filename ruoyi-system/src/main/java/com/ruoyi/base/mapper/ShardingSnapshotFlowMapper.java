package com.ruoyi.base.mapper;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.Date;
import java.util.List;

/**
 * 卡口流水ShardingSphere分表Mapper接口
 * <p>
 * 使用ShardingSphere后，Mapper直接操作逻辑表名，分表路由由ShardingSphere自动处理
 * 逻辑表名：ods_rt_szdn_snapshot_flow
 * 分表规则：按snapshottime字段按月分表
 * </p>
 */
@Mapper
public interface ShardingSnapshotFlowMapper {

    /**
     * 插入数据（ShardingSphere自动路由到对应分表）
     * 
     * @param record 卡口流水记录
     * @return 影响行数
     */
    int insert(OdsRtSzdnSnapshotFlowAddcode record);

    /**
     * 批量插入数据（ShardingSphere自动路由）
     * 
     * @param list 记录列表
     * @return 影响行数
     */
    int batchInsert(@Param("list") List<OdsRtSzdnSnapshotFlowAddcode> list);

    /**
     * 根据ID查询（ShardingSphere自动路由）
     * 
     * @param bigId 主键ID
     * @return 记录
     */
    OdsRtSzdnSnapshotFlowAddcode selectById(@Param("bigId") String bigId);

    /**
     * 根据时间范围查询（跨分表查询，自动合并结果）
     * <p>
     * 当时间范围跨多个月份时，ShardingSphere会：
     * 1. 识别涉及的分表
     * 2. 并行查询所有分表
     * 3. 合并结果并排序
     * </p>
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByTimeRange(
            @Param("startTime") Date startTime, 
            @Param("endTime") Date endTime);

    /**
     * 分页查询（支持跨分表分页）
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @param offset    偏移量
     * @param limit     每页大小
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByTimeRangeWithPage(
            @Param("startTime") Date startTime, 
            @Param("endTime") Date endTime,
            @Param("offset") int offset,
            @Param("limit") int limit);

    /**
     * 统计时间范围内记录数（跨分表统计）
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 记录总数
     */
    long countByTimeRange(@Param("startTime") Date startTime, @Param("endTime") Date endTime);

    /**
     * 更新数据（ShardingSphere自动路由）
     * 
     * @param record 更新记录
     * @return 影响行数
     */
    int updateById(OdsRtSzdnSnapshotFlowAddcode record);

    /**
     * 删除数据（ShardingSphere自动路由）
     * 
     * @param bigId 主键ID
     * @return 影响行数
     */
    int deleteById(@Param("bigId") String bigId);

    /**
     * 多条件查询（支持跨分表）
     * 
     * @param record 查询条件
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByCondition(OdsRtSzdnSnapshotFlowAddcode record);

    /**
     * 多条件分页查询
     * 
     * @param record 查询条件
     * @param offset 偏移量
     * @param limit  每页大小
     * @return 记录列表
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectByConditionWithPage(
            @Param("record") OdsRtSzdnSnapshotFlowAddcode record,
            @Param("offset") int offset,
            @Param("limit") int limit);

    /**
     * 多条件统计
     * 
     * @param record 查询条件
     * @return 记录总数
     */
    long countByCondition(OdsRtSzdnSnapshotFlowAddcode record);
}
