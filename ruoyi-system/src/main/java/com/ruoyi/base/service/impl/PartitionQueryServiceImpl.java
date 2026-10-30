package com.ruoyi.base.service.impl;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.service.IPartitionQueryService;
import com.ruoyi.manager.domain.dto.CursorPageResult;
import com.ruoyi.manager.domain.dto.SnapshotCursorPageQuery;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.*;

/**
 * 分区表跨月份 Keyset 游标分页查询 Service 实现
 *
 * 核心思路（对比传统 OFFSET 分页）：
 *
 * 传统分页 SQL：
 *   SELECT ... FROM table WHERE ... ORDER BY snapshottime DESC
 *   LIMIT 20 OFFSET 20000;
 * 问题：OFFSET 需要先扫描并排序前面的 20000 条才能找到第 20001 条，
 *      翻到第 1000 页后性能骤降。
 *
 * Keyset 游标分页 SQL：
 *   SELECT ... FROM table WHERE ...
 *     AND (snapshottime, big_id) < ('2025-05-20 14:30', 98765)
 *   ORDER BY snapshottime DESC, big_id DESC LIMIT 20;
 * 优势：
 *   - 走组合索引 (snapshottime, big_id) 直接定位到起始位置
 *   - 不管翻到第几页，性能都是 O(logN)，不会衰减
 *   - 在分区表上天然支持分区剪枝
 *
 * openGauss 3.0 支持的语法特性：
 *   - 行比较 (col1, col2) < (val1, val2)  —— openGauss 原生支持
 *   - LIMIT N OFFSET M                      —— 标准语法
 *   - 分区表上的本地索引自动继承
 */
@Service
public class PartitionQueryServiceImpl implements IPartitionQueryService {

    private static final Logger log = LoggerFactory.getLogger(PartitionQueryServiceImpl.class);

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    /**
     * 抓拍流水表跨月份游标分页查询
     *
     * 实现要点：
     *   1. 先 validate() 校验参数
     *   2. 查 pageSize + 1 条（多一条用于判断 hasNextPage，
     *      避免额外的 COUNT(*)）
     *   3. 返回结果中填充 nextCursorTime / nextCursorId，
     *      调用方下一页直接用这两个值做游标
     */
    @Override
    public CursorPageResult<OdsRtSzdnSnapshotFlowAddcode> querySnapshotFlow(SnapshotCursorPageQuery query) {
        // 1. 参数校验
        query.validate();

        // 2. 组装查询参数（用 HashMap，避免引新的依赖）
        Map<String, Object> params = buildQueryParams(query);

        // 3. 多查 1 条，判断是否有下一页
        params.put("pageSize", query.getPageSize() + 1);

        log.info("[分区表游标分页] 查询: platenumber={}, gantrycode={}, " +
                        "timeRange=[{}, {}), isFirstPage={}, cursor=({}, {})",
                query.getPlatenumber(), query.getGantrycode(),
                query.getStartTime(), query.getEndTime(),
                query.isFirstPage(),
                query.getLastSnapshottime(), query.getLastBigId());

        // 4. 调用 Mapper 查询
        // 注意：selectSnapshotFlowByCursor 需要你把
        // 分区表分页查询Mapper示例.xml 中的对应 SQL 贴到现有 Mapper XML 里
        List<OdsRtSzdnSnapshotFlowAddcode> rawList =
                snapshotFlowMapper.selectSnapshotFlowByCursor(params);

        // 5. 构造分页结果
        CursorPageResult<OdsRtSzdnSnapshotFlowAddcode> result =
                new CursorPageResult<>(rawList, query.getPageSize());
        result.setIsFirstPage(query.isFirstPage());

        // 6. 填充下一页的游标（本页最后一条记录的 snapshottime + big_id）
        if (result.getList() != null && !result.getList().isEmpty()) {
            OdsRtSzdnSnapshotFlowAddcode last =
                    result.getList().get(result.getList().size() - 1);
            result.setNextCursorTime(last.getSnapshottime());
            // 注意：你的 big_id 是 String 类型，需要转 Long；如果全是数字可以直接 parse
            if (last.getBigId() != null) {
                try {
                    result.setNextCursorId(Long.parseLong(last.getBigId()));
                } catch (NumberFormatException e) {
                    // 若 big_id 不是纯数字，改用 hashcode 作为辅助排序键
                    result.setNextCursorId((long) last.getBigId().hashCode());
                }
            }
        }

        return result;
    }

    /**
     * 批量导出（循环调用游标分页，直到数据读完）
     * 适合报表导出、数据同步等场景
     */
    @Override
    public List<OdsRtSzdnSnapshotFlowAddcode> exportSnapshotFlow(SnapshotCursorPageQuery query) {
        query.validate();
        query.setLastSnapshottime(null);   // 导出从最旧的数据开始
        query.setLastBigId(null);
        query.setPageSize(1000);           // 导出用较大批次

        List<OdsRtSzdnSnapshotFlowAddcode> all = new ArrayList<>();
        int batchCount = 0;

        while (true) {
            CursorPageResult<OdsRtSzdnSnapshotFlowAddcode> page = querySnapshotFlow(query);
            if (page.getList() == null || page.getList().isEmpty()) {
                break;
            }

            all.addAll(page.getList());
            batchCount++;

            if (batchCount % 10 == 0) {
                log.info("[分区表导出] 已处理 {} 批次, 共 {} 条记录",
                        batchCount, all.size());
            }

            // 没有下一页，退出循环
            if (!page.getHasNextPage()) {
                break;
            }

            // 更新游标，准备下一批
            query.setLastSnapshottime(page.getNextCursorTime());
            query.setLastBigId(page.getNextCursorId());
        }

        log.info("[分区表导出] 完成: 共 {} 批次, {} 条记录", batchCount, all.size());
        return all;
    }

    /**
     * 统计总条数
     * 注意：千万级数据不建议每次分页都调用，建议首次查一次后缓存
     */
    @Override
    public Long countSnapshotFlow(SnapshotCursorPageQuery query) {
        query.validate();
        Map<String, Object> params = buildQueryParams(query);
        // count 查询不需要游标参数
        params.remove("lastSnapshottime");
        params.remove("lastBigId");
        return snapshotFlowMapper.countSnapshotFlowByCursor(params);
    }

    /**
     * 组装 MyBatis 查询参数（HashMap，避免引新的依赖）
     */
    private Map<String, Object> buildQueryParams(SnapshotCursorPageQuery query) {
        Map<String, Object> params = new HashMap<>();
        params.put("platenumber", query.getPlatenumber());
        params.put("gantrycode", query.getGantrycode());
        params.put("sectioncode", query.getSectioncode());
        params.put("startTime", query.getStartTime());
        params.put("endTime", query.getEndTime());
        params.put("pageSize", query.getPageSize());

        // 非首页才传游标
        if (!query.isFirstPage()) {
            params.put("lastSnapshottime", query.getLastSnapshottime());
            params.put("lastBigId", query.getLastBigId());
        }
        return params;
    }
}
