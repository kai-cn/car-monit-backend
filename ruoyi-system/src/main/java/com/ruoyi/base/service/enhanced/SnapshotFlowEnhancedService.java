package com.ruoyi.base.service.enhanced;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.sharding.ShardingTableUtil;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Date;
import java.util.List;

/**
 * 门架抓拍流水增强查询服务
 * <p>
 * 用途：跨月份分表查询，直接从MySQL分表中查询并合并数据
 *
 * 数据存储策略：
 * - MySQL：按月分表存储，表名格式 ods_rt_szdn_snapshot_flow_yyyyMM
 * - 数据通过定时任务从GaussDB同步到MySQL分表
 *
 * 查询策略：
 * 1. 时间参数校验（超过当前时间直接返回空数据）
 * 2. 根据时间范围确定涉及的分表列表
 * 3. 跨多个分表查询数据并合并
 * 4. 按抓拍时间倒序排序后返回分页结果
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Service
public class SnapshotFlowEnhancedService {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    /**
     * 分页查询门架流水（跨月份分表查询）
     * <p>
     * 查询策略：
     * 1. 时间参数校验（超过当前时间直接返回空数据）
     * 2. 根据时间范围确定涉及的分表列表
     * 3. 跨多个分表查询数据并合并
     * 4. 按抓拍时间倒序排序后返回分页结果
     *
     * @param queryParam 查询参数
     * @return 分页查询结果
     */
    public TableDataInfo queryPage(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        TableDataInfo result = new TableDataInfo();
        result.setCode(200);
        result.setMsg("查询成功");

        // 步骤1: 时间参数校验
        if (!validateTimeRange(queryParam)) {
            log.warn("【时间校验】查询时间范围无效或超过当前时间，返回空数据");
            result.setRows(new ArrayList<>());
            result.setTotal(0L);
            return result;
        }

        // 步骤2: 执行MySQL分表查询
        log.info("【分表查询】开始查询，时间范围: {} 至 {}",
                queryParam.getApplyTime1(), queryParam.getApplyTime2());

        try {
            result = queryFromShardingTables(queryParam);
        } catch (Exception e) {
            log.error("【分表查询】查询失败: {}", e.getMessage(), e);
            result.setRows(new ArrayList<>());
            result.setTotal(0L);
        }

        return result;
    }

    /**
     * 校验查询时间范围
     * <p>
     * 校验规则：
     * 1. 开始时间不能超过当前时间
     * 2. 结束时间不能超过当前时间
     * 3. 开始时间不能大于结束时间
     *
     * @param queryParam 查询参数
     * @return 校验是否通过
     */
    private boolean validateTimeRange(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        String applyTime1 = queryParam.getApplyTime1();
        String applyTime2 = queryParam.getApplyTime2();

        // 如果时间参数为空，返回true（由上层判断）
        if (CommonUtil.isBlank(applyTime1) && CommonUtil.isBlank(applyTime2)) {
            return true;
        }

        Date now = new Date();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

        try {
            // 确保日期格式完整（添加时分秒）
            if (applyTime1 != null && applyTime1.length() == 10) {
                applyTime1 += " 00:00:00";
            }
            if (applyTime2 != null && applyTime2.length() == 10) {
                applyTime2 += " 23:59:59";
            }

            // 校验开始时间
            if (CommonUtil.isNotBlank(applyTime1)) {
                Date startTime = sdf.parse(applyTime1);
                if (startTime.after(now)) {
                    log.warn("【时间校验】开始时间 {} 超过当前时间", applyTime1);
                    return false;
                }
            }

            // 校验结束时间
            if (CommonUtil.isNotBlank(applyTime2)) {
                Date endTime = sdf.parse(applyTime2);
                if (endTime.after(now)) {
                    log.warn("【时间校验】结束时间 {} 超过当前时间", applyTime2);
                    return false;
                }
            }

            // 校验时间范围逻辑
            if (CommonUtil.isNotBlank(applyTime1) && CommonUtil.isNotBlank(applyTime2)) {
                Date startTime = sdf.parse(applyTime1);
                Date endTime = sdf.parse(applyTime2);
                if (startTime.after(endTime)) {
                    log.warn("【时间校验】开始时间 {} 大于结束时间 {}", applyTime1, applyTime2);
                    return false;
                }
            }

        } catch (ParseException e) {
            log.error("【时间校验】日期解析失败: {}", e.getMessage());
            return false;
        }

        return true;
    }

    /**
     * 从分表中查询数据（跨月份查询核心方法）
     * <p>
     * 核心算法逻辑：
     * 1. 根据时间范围获取所有涉及的分表列表
     * 2. 遍历所有分表统计总记录数（优化：历史表使用近似计数）
     * 3. 根据分页偏移量计算从哪个分表开始获取数据
     * 4. 跨分表获取数据并合并
     * 5. 按抓拍时间倒序排序后返回
     * </p>
     *
     * 分页算法说明：
     * - 假设每页10条，查询第3页（offset=20）
     * - 分表A有15条，分表B有20条，分表C有30条
     * - offset=20 > 15，跳过A表，offset=20-15=5
     * - offset=5 < 20，从B表的第5条开始取10条
     * - 如果B表不够，继续从C表取剩余数据
     *
     * COUNT优化策略：
     * - 对于大数据量表（如2000W+记录），使用INFORMATION_SCHEMA.TABLES获取近似行数
     * - 当前月份表（可能还在写入）使用精确COUNT
     * - 历史月份表（数据稳定）使用近似计数
     *
     * @param queryParam 查询参数（包含时间范围 applyTime1/applyTime2）
     * @return 分页查询结果（包含数据列表和总记录数）
     */
    private TableDataInfo queryFromShardingTables(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        // 初始化返回结果
        TableDataInfo result = new TableDataInfo();
        List<OdsRtSzdnSnapshotFlowAddcode> allList = new ArrayList<>();
        long total = 0L;

        // 步骤1: 根据时间范围获取所有涉及的分表名列表
        // 例如：时间范围 2025-08-01 至 2025-10-31，会获取表：
        // ods_rt_szdn_snapshot_flow_202508, ods_rt_szdn_snapshot_flow_202509, ods_rt_szdn_snapshot_flow_202510
        List<String> tableNames = ShardingTableUtil.getTableNamesByDateRange(
                queryParam.getApplyTime1(), queryParam.getApplyTime2());

        log.info("【分表查询】需要查询的分表数量: {}, 表名列表: {}", tableNames.size(), tableNames);

        // 步骤2: 获取当前月份表名（用于判断是否需要精确计数）
        String currentMonthTable = ShardingTableUtil.getTableNameByDate(new Date());

        // 步骤3: 遍历所有分表，统计总记录数（优化版）
        for (String tableName : tableNames) {
            try {
                long count;

                // 判断是否为当前月份的表
                boolean isCurrentMonthTable = tableName.equals(currentMonthTable);

                if (isCurrentMonthTable) {
                    // 当前月份表：数据可能还在写入，使用精确COUNT
                    count = snapshotFlowMapper.selectShardingCount(tableName, queryParam);
                    log.info("【分表统计】表 {} (当前月) 精确记录数: {}", tableName, count);
                } else {
                    // 历史月份表：数据稳定，使用近似计数（通过INFORMATION_SCHEMA获取）
                    count = getApproximateCount(tableName, queryParam);
                    log.info("【分表统计】表 {} (历史月) 近似记录数: {}", tableName, count);
                }

                total += count;
            } catch (Exception e) {
                // 表不存在时跳过，记录警告日志
                log.warn("【分表统计】表 {} 不存在或查询失败: {}", tableName, e.getMessage());
            }
        }

        // 步骤4: 计算分页参数
        int pageNum = queryParam.getPageNum() != null ? queryParam.getPageNum() : 1;
        int pageSize = queryParam.getPageSize() != null ? queryParam.getPageSize() : 10;
        int offset = (pageNum - 1) * pageSize;  // 全局偏移量

        log.info("【分页参数】页码: {}, 每页大小: {}, 全局偏移量: {}", pageNum, pageSize, offset);

        // 如果总记录数小于偏移量，直接返回空数据
        if (total <= offset) {
            log.info("【分表查询】总记录数 {} <= 偏移量 {}，返回空数据", total, offset);
            result.setRows(allList);
            result.setTotal(total);
            return result;
        }

        // 步骤5: 跨分表分页查询
        int remaining = pageSize;  // 还需要获取的记录数
        int currentOffset = offset;  // 当前表内的偏移量

        for (String tableName : tableNames) {
            // 如果已经获取足够的数据，提前退出循环
            if (remaining <= 0) {
                break;
            }

            try {
                // 获取当前表的记录数（使用精确计数，因为分页需要准确判断）
                long tableCount = snapshotFlowMapper.selectShardingCount(tableName, queryParam);

                // 如果全局偏移量超过当前表的记录数，跳过当前表
                if (currentOffset >= tableCount) {
                    currentOffset -= tableCount;
                    log.debug("【分页查询】跳过表 {} (offset={} >= 表记录数={})",
                            tableName, currentOffset + tableCount, tableCount);
                    continue;
                }

                // 从当前表获取数据
                log.debug("【分页查询】从表 {} 获取数据，偏移量: {}, 需要数量: {}",
                        tableName, currentOffset, remaining);
                List<OdsRtSzdnSnapshotFlowAddcode> tableList =
                        snapshotFlowMapper.selectShardingList(tableName, queryParam, currentOffset);

                // 计算实际获取的数量
                int take = Math.min(tableList.size(), remaining);
                allList.addAll(tableList.subList(0, take));
                remaining -= take;
                currentOffset = 0;  // 下一个表从0开始

                log.info("【分页查询】表 {} 获取了 {} 条数据，剩余需要获取: {}", tableName, take, remaining);
            } catch (Exception e) {
                log.warn("【分页查询】表 {} 查询失败: {}", tableName, e.getMessage());
            }
        }

        // 步骤6: 按抓拍时间倒序排序（确保跨分表数据的时间顺序正确）
        allList.sort(Comparator.comparing(OdsRtSzdnSnapshotFlowAddcode::getSnapshottime).reversed());

        // 设置返回结果
        result.setRows(allList);
        result.setTotal(total);

        log.info("【分表查询完成】总记录数: {}, 当前页数据量: {}", total, allList.size());

        return result;
    }

    /**
     * 获取表的近似记录数（优化大数据量COUNT查询）
     * <p>
     * 优化原理：
     * 1. 对于历史月份表，数据已经稳定，不需要精确计数
     * 2. 使用INFORMATION_SCHEMA.TABLES.TABLE_ROWS获取近似行数
     * 3. TABLE_ROWS是MySQL统计信息，可能有一定误差（通常在10%以内）
     * 4. 避免对2000W+记录的表执行全表扫描COUNT(*)
     *
     * @param tableName    表名
     * @param queryParam   查询参数（用于判断是否需要应用过滤条件）
     * @return 近似记录数
     */
    private long getApproximateCount(String tableName, OdsRtSzdnSnapshotFlowAddcode queryParam) {
        // 检查是否有额外的过滤条件（除了时间范围）
        boolean hasExtraFilters = hasExtraFilters(queryParam);

        if (hasExtraFilters) {
            // 如果有额外过滤条件，需要执行精确COUNT
            log.debug("【近似计数】存在额外过滤条件，使用精确COUNT");
            return snapshotFlowMapper.selectShardingCount(tableName, queryParam);
        }

        // 使用INFORMATION_SCHEMA获取近似行数
        try {
            Long approxCount = snapshotFlowMapper.getTableApproximateCount(tableName);
            if (approxCount != null && approxCount > 0) {
                log.debug("【近似计数】表 {} 的近似行数: {}", tableName, approxCount);
                return approxCount;
            }
        } catch (Exception e) {
            log.warn("【近似计数】获取表 {} 近似行数失败: {}", tableName, e.getMessage());
        }

        // 降级到精确COUNT
        return snapshotFlowMapper.selectShardingCount(tableName, queryParam);
    }

    /**
     * 判断查询参数是否包含除时间范围外的额外过滤条件
     * <p>
     * 如果有额外过滤条件（如车牌号、设备ID等），则无法使用近似计数
     *
     * @param queryParam 查询参数
     * @return 是否有额外过滤条件
     */
    private boolean hasExtraFilters(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        return CommonUtil.isNotBlank(queryParam.getPlatenumber())
                || CommonUtil.isNotBlank(queryParam.getDeviceid())
                || CommonUtil.isNotBlank(queryParam.getGantrycode())
                || CommonUtil.isNotBlank(queryParam.getSectionCodeStr())
                || queryParam.getDirection() != null
                || CommonUtil.isNotBlank(queryParam.getPlatecolor())
                || CommonUtil.isNotBlank(queryParam.getCartype())
                || CommonUtil.isNotBlank(queryParam.getDatasource());
    }

    /**
     * 查询门架流水列表（用于导出）
     * <p>
     * 查询策略同分页查询，但不做分页限制
     *
     * @param queryParam 查询参数
     * @return 门架流水列表
     */
    public List<OdsRtSzdnSnapshotFlowAddcode> queryListForExport(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        List<OdsRtSzdnSnapshotFlowAddcode> allList = new ArrayList<>();

        // 获取分表列表
        List<String> tableNames = ShardingTableUtil.getTableNamesByDateRange(
                queryParam.getApplyTime1(), queryParam.getApplyTime2());

        // 遍历分表查询
        for (String tableName : tableNames) {
            try {
                List<OdsRtSzdnSnapshotFlowAddcode> tableList =
                        snapshotFlowMapper.selectShardingList(tableName, queryParam, 0);
                allList.addAll(tableList);
            } catch (Exception e) {
                log.warn("【导出查询】表 {} 查询失败: {}", tableName, e.getMessage());
            }
        }

        // 按时间倒序排序
        allList.sort(Comparator.comparing(OdsRtSzdnSnapshotFlowAddcode::getSnapshottime).reversed());

        return allList;
    }
}
