package com.ruoyi.base.service;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.manager.domain.dto.CursorPageResult;
import com.ruoyi.manager.domain.dto.SnapshotCursorPageQuery;

import java.util.List;

/**
 * 分区表跨月份 Keyset 游标分页查询 Service
 */
public interface IPartitionQueryService {

    /**
     * 抓拍流水表跨月份游标分页查询
     *
     * @param query 分页请求（含游标）
     * @return 分页结果（含下一页的游标）
     */
    CursorPageResult<OdsRtSzdnSnapshotFlowAddcode> querySnapshotFlow(SnapshotCursorPageQuery query);

    /**
     * 批量导出（内部循环调用游标分页，直到数据读完）
     *
     * @param query 查询条件（只传 startTime / endTime / 筛选条件，不传游标）
     * @return 所有符合条件的记录
     */
    List<OdsRtSzdnSnapshotFlowAddcode> exportSnapshotFlow(SnapshotCursorPageQuery query);

    /**
     * 总条数（可选，用于 UI 显示"共多少条"）
     * 注意：千万级数据量不建议每次分页都查总数，首次查一次缓存即可
     */
    Long countSnapshotFlow(SnapshotCursorPageQuery query);
}
