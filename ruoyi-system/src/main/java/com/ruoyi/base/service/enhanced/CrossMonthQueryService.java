package com.ruoyi.base.service.enhanced;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.sharding.ShardingTableUtil;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 门架抓拍流水跨月份查询优化服务
 * <p>
 * 非分布式场景下的性能优化方案：
 * 1. 基于数据库视图的跨表查询
 * 2. 动态分表查询（根据时间范围自动路由）
 * 3. 缓存优化（减少重复查询）
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Service
public class CrossMonthQueryService {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    /**
     * 分表缓存（避免重复计算表名）
     */
    private static final Map<String, List<String>> tableNameCache = new HashMap<>();
    private static final SimpleDateFormat TABLE_NAME_FORMAT = new SimpleDateFormat("yyyyMM");

    /**
     * 跨月份分页查询（优化版）
     * <p>
     * 查询策略：
     * 1. 如果时间范围在同一个月，直接查询对应分表
     * 2. 如果跨多个月份，使用 UNION ALL 查询多个分表
     * 3. 支持视图查询（如果已创建联合视图）
     *
     * @param queryParam 查询参数
     * @return 分页结果
     */
    public TableDataInfo queryCrossMonthPage(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        TableDataInfo result = new TableDataInfo();
        List<OdsRtSzdnSnapshotFlowAddcode> dataList = new ArrayList<>();
        long total = 0L;

        Date startTime = queryParam.getSnapshottime();
        Date endTime = queryParam.getApplyTime2() != null ? 
            parseDate(queryParam.getApplyTime2()) : new Date();

        // 根据时间范围决定查询策略
        List<String> tableNames = getTableNamesByDateRange(startTime, endTime);

        log.info("[跨月份查询] 时间范围={}~{}, 涉及表数量={}", 
            formatDate(startTime), formatDate(endTime), tableNames.size());

        // 如果只有一个表，直接查询
        if (tableNames.size() == 1) {
            String tableName = tableNames.get(0);
            dataList = snapshotFlowMapper.selectFromTable(tableName, queryParam);
            total = dataList.size();
        } 
        // 跨多个表，使用联合查询或视图
        else if (tableNames.size() <= 3) {
            // 少量表：使用 UNION ALL
            dataList = unionQuery(tableNames, queryParam);
            total = dataList.size();
        } 
        else {
            // 大量表：优先使用视图或物化视图
            try {
                dataList = snapshotFlowMapper.selectFromView(queryParam);
                total = dataList.size();
                log.info("[跨月份查询] 使用视图查询");
            } catch (Exception e) {
                log.warn("[跨月份查询] 视图查询失败，回退到UNION ALL: {}", e.getMessage());
                dataList = unionQuery(tableNames, queryParam);
                total = dataList.size();
            }
        }

        // 排序（如果需要）
        if (!dataList.isEmpty()) {
            dataList.sort((a, b) -> {
                Date aTime = a.getSnapshottime();
                Date bTime = b.getSnapshottime();
                return bTime.compareTo(aTime); // 按时间降序
            });
        }

        // 分页处理
        int pageNum = queryParam.getPageNum() != null ? queryParam.getPageNum() : 1;
        int pageSize = queryParam.getPageSize() != null ? queryParam.getPageSize() : 10;
        int startIndex = (pageNum - 1) * pageSize;
        int endIndex = Math.min(startIndex + pageSize, dataList.size());

        if (startIndex < dataList.size()) {
            result.setRows(dataList.subList(startIndex, endIndex));
        } else {
            result.setRows(new ArrayList<>());
        }
        result.setTotal(total);
        result.setCode(200);
        result.setMsg("查询成功");

        return result;
    }

    /**
     * 根据日期范围获取涉及的分表名列表
     *
     * @param startDate 开始日期
     * @param endDate 结束日期
     * @return 分表名列表
     */
    public List<String> getTableNamesByDateRange(Date startDate, Date endDate) {
        if (startDate == null) {
            startDate = new Date();
        }
        if (endDate == null) {
            endDate = new Date();
        }

        // 构建缓存键
        String cacheKey = formatDate(startDate) + "~" + formatDate(endDate);
        
        // 检查缓存
        if (tableNameCache.containsKey(cacheKey)) {
            return tableNameCache.get(cacheKey);
        }

        List<String> tableNames = new ArrayList<>();
        
        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);
        startCal.set(Calendar.DAY_OF_MONTH, 1);
        startCal.set(Calendar.HOUR_OF_DAY, 0);
        startCal.set(Calendar.MINUTE, 0);
        startCal.set(Calendar.SECOND, 0);
        startCal.set(Calendar.MILLISECOND, 0);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        while (!startCal.after(endCal)) {
            String tableName = ShardingTableUtil.getTableNameByDate(startCal.getTime());
            tableNames.add(tableName);
            
            // 下一个月
            startCal.add(Calendar.MONTH, 1);
        }

        // 添加当前活跃表（最新数据可能写入该表）
        String currentTable = "ods_rt_szdn_snapshot_flow_addcode";
        if (!tableNames.contains(currentTable)) {
            tableNames.add(currentTable);
        }

        // 缓存结果（有效期较短，避免表结构变化导致问题）
        tableNameCache.put(cacheKey, tableNames);

        // 清理过期缓存（简单实现）
        if (tableNameCache.size() > 100) {
            tableNameCache.clear();
        }

        return tableNames;
    }

    /**
     * UNION ALL 联合查询多个表
     *
     * @param tableNames 表名列表
     * @param queryParam 查询参数
     * @return 查询结果
     */
    private List<OdsRtSzdnSnapshotFlowAddcode> unionQuery(List<String> tableNames, 
                                                           OdsRtSzdnSnapshotFlowAddcode queryParam) {
        List<OdsRtSzdnSnapshotFlowAddcode> allResults = new ArrayList<>();

        for (String tableName : tableNames) {
            try {
                List<OdsRtSzdnSnapshotFlowAddcode> results = 
                    snapshotFlowMapper.selectFromTable(tableName, queryParam);
                allResults.addAll(results);
            } catch (Exception e) {
                log.warn("[跨月份查询] 查询表{}失败: {}", tableName, e.getMessage());
            }
        }

        return allResults;
    }

    /**
     * 解析日期字符串
     */
    private Date parseDate(String dateStr) {
        if (CommonUtil.isBlank(dateStr)) {
            return null;
        }
        try {
            if (dateStr.contains("-")) {
                if (dateStr.contains(" ")) {
                    return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").parse(dateStr);
                } else {
                    return new SimpleDateFormat("yyyy-MM-dd").parse(dateStr);
                }
            }
        } catch (Exception e) {
            log.warn("[日期解析失败] {}", dateStr);
        }
        return null;
    }

    /**
     * 格式化日期
     */
    private String formatDate(Date date) {
        if (date == null) {
            return "null";
        }
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    /**
     * 统计查询（跨月份）
     *
     * @param queryParam 查询参数
     * @return 统计结果
     */
    public Map<String, Object> statisticsCrossMonth(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        Map<String, Object> result = new HashMap<>();
        
        Date startTime = queryParam.getSnapshottime();
        Date endTime = queryParam.getApplyTime2() != null ? 
            parseDate(queryParam.getApplyTime2()) : new Date();

        List<String> tableNames = getTableNamesByDateRange(startTime, endTime);
        long totalCount = 0;
        Map<String, Long> sectionCountMap = new HashMap<>();

        for (String tableName : tableNames) {
            try {
                Map<String, Object> stats = snapshotFlowMapper.statisticsTable(tableName, queryParam);
                totalCount += stats.get("totalCount") != null ? (Long) stats.get("totalCount") : 0;
                
                @SuppressWarnings("unchecked")
                Map<String, Long> sectionMap = (Map<String, Long>) stats.get("sectionCount");
                if (sectionMap != null) {
                    sectionMap.forEach((k, v) -> 
                        sectionCountMap.merge(k, v, Long::sum));
                }
            } catch (Exception e) {
                log.warn("[统计查询] 查询表{}失败: {}", tableName, e.getMessage());
            }
        }

        result.put("totalCount", totalCount);
        result.put("sectionCount", sectionCountMap);
        result.put("tableCount", tableNames.size());

        return result;
    }

    /**
     * 刷新分表缓存
     */
    public void refreshTableCache() {
        tableNameCache.clear();
        log.info("[跨月份查询] 分表缓存已刷新");
    }
}
