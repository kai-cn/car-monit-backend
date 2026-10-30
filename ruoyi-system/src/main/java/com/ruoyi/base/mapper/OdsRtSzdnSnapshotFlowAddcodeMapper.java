package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.manager.domain.vo.bigscreen.TopTenVO;
import org.apache.ibatis.annotations.MapKey;
import org.apache.ibatis.annotations.Param;
import org.springframework.stereotype.Repository;

import java.util.Date;
import java.util.List;
import java.util.Map;

/**
 * 门架抓拍流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@Repository
public interface OdsRtSzdnSnapshotFlowAddcodeMapper extends BaseMapper<OdsRtSzdnSnapshotFlowAddcode> {
    /**
     * 查询门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 门架抓拍流水
     */
    OdsRtSzdnSnapshotFlowAddcode selectOdsRtSzdnSnapshotFlowAddcodeById(String bigId);

    /**
     * 查询门架抓拍流水列表
     *
     * @param odsRtSzdnSnapshotFlowAddcode 门架抓拍流水
     * @return 门架抓拍流水集合
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectOdsRtSzdnSnapshotFlowAddcodeList(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 批量删除门架抓拍流水
     *
     * @param bigIds 需要删除的数据ID
     * @return 结果
     */
    int deleteOdsRtSzdnSnapshotFlowAddcodeByIds(String[] bigIds);

    /**
     * 删除门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 结果
     */
    int deleteOdsRtSzdnSnapshotFlowAddcodeById(String bigId);

    List<TopTenVO> getTopTen();

    /**
     * 根据分表名分页查询门架抓拍流水
     *
     * @param tableName                     分表名
     * @param odsRtSzdnSnapshotFlowAddcode 查询参数
     * @param offset                        偏移量
     * @return 门架抓拍流水集合
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectShardingList(@Param("tableName") String tableName,
                                                           @Param("odsRtSzdnSnapshotFlowAddcode") OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode,
                                                           @Param("offset") int offset);

    /**
     * 根据分表名统计记录总数
     *
     * @param tableName                     分表名
     * @param odsRtSzdnSnapshotFlowAddcode 查询参数
     * @return 记录总数
     */
    long selectShardingCount(@Param("tableName") String tableName,
                             @Param("odsRtSzdnSnapshotFlowAddcode") OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 检查表是否存在
     *
     * @param tableName 表名
     * @return 存在返回1，不存在返回0
     */
    int checkTableExists(@Param("tableName") String tableName);

    /**
     * 创建分表（复制结构）
     *
     * @param tableName 新表名
     */
    void createShardingTable(@Param("tableName") String tableName);

    /**
     * 获取表的近似行数（从INFORMATION_SCHEMA获取）
     * <p>
     * 用于优化大数据量表的COUNT查询性能
     *
     * @param tableName 表名
     * @return 近似行数
     */
    Long getTableApproximateCount(@Param("tableName") String tableName);

    /**
     * 从指定表查询数据
     *
     * @param tableName                     表名
     * @param odsRtSzdnSnapshotFlowAddcode 查询参数
     * @return 门架抓拍流水集合
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectFromTable(@Param("tableName") String tableName,
                                                        @Param("query") OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 从联合视图查询数据（跨月份查询优化）
     *
     * @param odsRtSzdnSnapshotFlowAddcode 查询参数
     * @return 门架抓拍流水集合
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectFromView(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 统计指定表的数据
     *
     * @param tableName                     表名
     * @param odsRtSzdnSnapshotFlowAddcode 查询参数
     * @return 统计结果（totalCount, sectionCount）
     */
    @MapKey("totalCount")
    Map<String, Object> statisticsTable(@Param("tableName") String tableName,
                                        @Param("query") OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    /**
     * 查询所有分表名（从information_schema获取）
     *
     * @param tablePrefix 表名前缀
     * @return 分表名列表
     */
    List<String> listShardingTables(@Param("tablePrefix") String tablePrefix);

    /**
     * 查询指定表中的最大snapshottime
     * <p>
     * 用于增量同步任务确定上次同步时间
     *
     * @param tableName 表名
     * @return 最大抓拍时间
     */
    Date getMaxSnapshottime(@Param("tableName") String tableName);

    /**
     * 批量插入数据到指定分表
     *
     * @param tableName                     分表名
     * @param list                          数据列表
     */
    void insertBatchToTable(@Param("tableName") String tableName,
                           @Param("list") List<OdsRtSzdnSnapshotFlowAddcode> list);

    void insertToTable(@Param("tableName")String tableName, @Param("item") OdsRtSzdnSnapshotFlowAddcode data);

    /**
     * 根据ID从指定表查询单条数据
     *
     * @param tableName 表名
     * @param bigId     ID
     * @return 查询结果
     */
    OdsRtSzdnSnapshotFlowAddcode selectFromTableById(@Param("tableName") String tableName,
                                                      @Param("bigId") String bigId);

    List<OdsRtSzdnSnapshotFlowAddcode> selectSnapshotFlowByCursor(Map<String, Object> params);

    Long countSnapshotFlowByCursor(Map<String, Object> params);
}
