package com.ruoyi.base.mapper;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;

import java.util.List;
import java.util.Map;

/**
 * ============================================================
 * 文件说明：这是一个示例文件，不需要真正放到项目里
 * ------------------------------------------------------------
 * 你只需要把下面 4 个方法声明复制粘贴到你现有的
 *   ruoyi-system/src/main/java/com/ruoyi/base/mapper/OdsRtSzdnSnapshotFlowAddcodeMapper.java
 * 的 class 里即可（其他方法保持不变）
 * ============================================================
 */
public interface OdsRtSzdnSnapshotFlowAddcodeMapperExample {

    /**
     * 分区表跨月份 Keyset 游标分页查询
     *
     * @param params 查询参数：
     *                 platenumber      车牌（可选）
     *                 gantrycode   门架编号（可选）
     *                 sectioncode   路段编号（可选）
     *                 startTime     起始时间（必填，>=）
     *                 endTime       结束时间（必填，<）
     *                 lastSnapshottime  上一页最后一条的 snapshottime（首次查询传 null）
     *                 lastBigId     上一页最后一条的 big_id（首次查询传 null）
     *                 pageSize      每页条数
     * @return 当前页数据
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectSnapshotFlowByCursor(Map<String, Object> params);

    /**
     * 分区表跨月份游标分页 - 统计总数
     * 参数和上面一致（但不需要游标参数）
     */
    Long countSnapshotFlowByCursor(Map<String, Object> params);

    /**
     * 分区表双层 OFFSET 分页（当 UI 要求支持跳页时用）
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectSnapshotFlowByOffset(Map<String, Object> params);

    /**
     * 批量导出用的游标分页（一次查 1000 条，循环到最后）
     */
    List<OdsRtSzdnSnapshotFlowAddcode> selectSnapshotFlowForExport(Map<String, Object> params);
}
