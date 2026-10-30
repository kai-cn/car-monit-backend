package com.ruoyi.quartz.task;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.base.sharding.ShardingTableUtil;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.PostConstruct;
import javax.annotation.Resource;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 门架抓拍流水分表同步定时任务
 * <p>
 * 功能：
 * 1. 全量同步：从GaussDB同步历史数据到MySQL分表，按snapshottime字段按月分表，并发执行
 * 2. 增量同步：定时同步当前月份的新增数据
 * </p>
 */
@Slf4j
@Component
public class SnapshotFlowSyncTask {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    @Resource
    private HttpOdsRtSzdnSnapshotFlowAddcodeService httpOdsRtSzdnSnapshotFlowAddcodeService;

    /**
     * 并发同步线程池
     * - 核心线程数：4（根据CPU核数和数据库连接池大小调整）
     * - 最大线程数：8
     * - 队列容量：100
     */
    private ExecutorService syncExecutor;

    /**
     * 线程池初始化
     */
    @PostConstruct
    public void init() {
        syncExecutor = new ThreadPoolExecutor(
                4,                                  // 核心线程数
                8,                                  // 最大线程数
                60L,                                // 空闲线程存活时间
                TimeUnit.SECONDS,                   // 时间单位
                new LinkedBlockingQueue<>(100),     // 任务队列
                r -> new Thread(r, "snapshot-sync-worker"), // 线程命名
                new ThreadPoolExecutor.CallerRunsPolicy()   // 拒绝策略
        );
        log.info("【分表同步任务】线程池初始化完成");
    }

    /**
     * 全量同步任务（首次同步或补全历史数据）
     * <p>
     * 执行策略：
     * 1. 查询GaussDB中最早的snapshottime
     * 2. 根据最早时间到现在进行月份分区
     * 3. 使用线程池并发同步每个月份的数据
     * </p>
     *
     * 注意：此任务应在系统首次部署时手动触发，或定期执行以补全遗漏的数据
     */
    public AjaxResult syncFullData() {
        log.info("【全量同步任务】开始执行全量同步");
        long startTime = System.currentTimeMillis();

        try {
            // 步骤1: 查询GaussDB中最早的snapshottime
            Date earliestDate = queryEarliestSnapshottime();
            if (earliestDate == null) {
                log.warn("【全量同步任务】未查询到最早的snapshottime，可能GaussDB中无数据");
                return AjaxResult.success("GaussDB中暂无数据");
            }

            // 步骤2: 获取当前时间
            Date now = new Date();

            // 步骤3: 根据时间范围获取月份分区列表
            List<String> monthPartitions = getMonthPartitions(earliestDate, now);
            log.info("【全量同步任务】时间范围: {} 至 {}, 月份分区数: {}, 分区列表: {}",
                    formatDate(earliestDate), formatDate(now), monthPartitions.size(), monthPartitions);

            // 步骤4: 并发同步每个月份的数据
            int totalCount = syncByMonthPartitions(monthPartitions);

            long endTime = System.currentTimeMillis();
            log.info("【全量同步任务】完成全量同步，同步记录数: {}, 耗时: {} ms",
                    totalCount, endTime - startTime);

            return AjaxResult.success("全量同步完成，共同步 " + totalCount + " 条数据");

        } catch (Exception e) {
            log.error("【全量同步任务】全量同步失败: {}", e.getMessage(), e);
            return AjaxResult.error("全量同步失败: " + e.getMessage());
        }
    }

    /**
     * 查询GaussDB中最早的snapshottime
     */
    private Date queryEarliestSnapshottime() {
        try {
            return httpOdsRtSzdnSnapshotFlowAddcodeService.getEarliestSnapshottime();
        } catch (Exception e) {
            log.error("【全量同步任务】查询最早snapshottime失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 根据时间范围获取月份分区列表
     *
     * @param startDate 开始日期
     * @param endDate   结束日期
     * @return 月份分区列表（格式：yyyyMM）
     */
    private List<String> getMonthPartitions(Date startDate, Date endDate) {
        List<String> partitions = new ArrayList<>();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMM");

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        while (!startCal.after(endCal)) {
            partitions.add(sdf.format(startCal.getTime()));
            startCal.add(Calendar.MONTH, 1);
        }

        return partitions;
    }

    /**
     * 并发同步所有月份分区的数据
     *
     * @param monthPartitions 月份分区列表
     * @return 总同步记录数
     */
    private int syncByMonthPartitions(List<String> monthPartitions) {
        // 用于统计总同步数
        AtomicInteger totalCount = new AtomicInteger(0);
        // 用于收集异常
        List<Exception> exceptions = Collections.synchronizedList(new ArrayList<>());
        // 用于等待所有任务完成
        List<Future<Integer>> futures = new ArrayList<>();

        // 提交每个月份的同步任务
        for (String month : monthPartitions) {
            Future<Integer> future = syncExecutor.submit(() -> {
                try {
                    return syncSingleMonth(month, totalCount);
                } catch (Exception e) {
                    log.error("【全量同步任务】月份 {} 同步失败: {}", month, e.getMessage());
                    exceptions.add(e);
                    return 0;
                }
            });
            futures.add(future);
        }

        // 等待所有任务完成
        for (Future<Integer> future : futures) {
            try {
                future.get(); // 等待任务完成
            } catch (InterruptedException | ExecutionException e) {
                log.error("【全量同步任务】等待任务完成时发生异常: {}", e.getMessage());
                exceptions.add(e);
            }
        }

        // 如果有异常，记录警告日志
        if (!exceptions.isEmpty()) {
            log.warn("【全量同步任务】有 {} 个月份同步失败", exceptions.size());
        }

        return totalCount.get();
    }

    /**
     * 同步单个月份的数据
     *
     * @param month       月份（格式：yyyyMM）
     * @param totalCount  总计数
     * @return 该月份同步的记录数
     */
    @Transactional(rollbackFor = Exception.class)
    public int syncSingleMonth(String month, AtomicInteger totalCount) {
        log.info("【全量同步任务】开始同步月份: {}", month);
        long startTime = System.currentTimeMillis();

        // 构建该月份的时间范围
        String startDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-01 00:00:00";

        // 获取该月份的最后一天
        Calendar cal = Calendar.getInstance();
        cal.set(Integer.parseInt(month.substring(0, 4)),
                Integer.parseInt(month.substring(4, 6)) - 1, 1);
        int lastDay = cal.getActualMaximum(Calendar.DAY_OF_MONTH);
        String endDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-" + lastDay + " 23:59:59";

        int count = syncSnapshotFlowByDateRange(startDate, endDate);
        totalCount.addAndGet(count);

        long endTime = System.currentTimeMillis();
        log.info("【全量同步任务】月份 {} 同步完成，记录数: {}, 耗时: {} ms",
                month, count, endTime - startTime);

        return count;
    }

    /**
     * 根据日期范围同步数据（单线程版本）
     */
    private int syncSnapshotFlowByDateRange(String startDate, String endDate) {
        int totalCount = 0;
        int pageNum = 1;
        int pageSize = 1000;

        while (true) {
            TableDataInfo tableDataInfo = fetchFromGaussDB(startDate, endDate, pageNum, pageSize);

            if (tableDataInfo == null || tableDataInfo.getRows() == null || tableDataInfo.getRows().isEmpty()) {
                break;
            }

            List<OdsRtSzdnSnapshotFlowAddcode> dataList = convertToEntityList(tableDataInfo.getRows());

            if (dataList.isEmpty()) {
                break;
            }

            Map<String, List<OdsRtSzdnSnapshotFlowAddcode>> groupedByMonth = groupByMonth(dataList);

            for (Map.Entry<String, List<OdsRtSzdnSnapshotFlowAddcode>> entry : groupedByMonth.entrySet()) {
                String tableName = entry.getKey();
                List<OdsRtSzdnSnapshotFlowAddcode> list = entry.getValue();

                ensureTableExists(tableName);
                insertBatchToTable(tableName, list);
                totalCount += list.size();

                log.debug("【全量同步任务】表 {} 插入 {} 条数据", tableName, list.size());
            }

            if (dataList.size() < pageSize) {
                break;
            }

            pageNum++;
        }

        return totalCount;
    }

    // ==================== 增量同步任务 ====================

    /**
     * 增量同步任务（每小时执行一次）
     * <p>
     * 执行策略：
     * 1. 查询MySQL当前月份表中最新的snapshottime
     * 2. 从GaussDB同步该时间之后的新增数据
     * 3. 写入MySQL当前月份表
     * </p>
     */
    @Scheduled(cron = "0 0 * * * ?")
    @Transactional(rollbackFor = Exception.class)
    public void syncIncrementalData() {
        log.info("【增量同步任务】开始执行增量同步");
        long startTime = System.currentTimeMillis();

        try {
            // 步骤1: 获取当前月份表名
            String currentMonthTable = ShardingTableUtil.getTableNameByDate(new Date());

            // 步骤2: 查询MySQL中当前月份表的最新snapshottime
            Date lastSyncTime = queryLastSyncTime(currentMonthTable);

            // 步骤3: 构建查询范围（从上次同步时间到当前时间）
            String startDate;
            if (lastSyncTime == null) {
                // 如果是首次同步，从本月1号开始
                Calendar cal = Calendar.getInstance();
                cal.set(Calendar.DAY_OF_MONTH, 1);
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                startDate = formatDateTime(cal.getTime());
            } else {
                startDate = formatDateTime(lastSyncTime);
            }

            String endDate = formatDateTime(new Date());

            log.info("【增量同步任务】同步时间范围: {} 至 {}", startDate, endDate);

            // 步骤4: 执行同步
            int syncCount = syncSnapshotFlowByDateRange(startDate, endDate);

            long endTime = System.currentTimeMillis();
            log.info("【增量同步任务】完成增量同步，同步记录数: {}, 耗时: {} ms",
                    syncCount, endTime - startTime);

        } catch (Exception e) {
            log.error("【增量同步任务】增量同步失败: {}", e.getMessage(), e);
        }
    }

    /**
     * 查询MySQL中当前月份表的最新snapshottime
     */
    private Date queryLastSyncTime(String tableName) {
        try {
            // 检查表是否存在
            int exists = snapshotFlowMapper.checkTableExists(tableName);
            if (exists == 0) {
                log.warn("【增量同步任务】表 {} 不存在，将从本月初开始同步", tableName);
                return null;
            }

            // 查询最新的snapshottime
            return snapshotFlowMapper.getMaxSnapshottime(tableName);
        } catch (Exception e) {
            log.error("【增量同步任务】查询最新snapshottime失败: {}", e.getMessage());
            return null;
        }
    }

    // ==================== 辅助方法 ====================

    private TableDataInfo fetchFromGaussDB(String startDate, String endDate, int pageNum, int pageSize) {
        try {
            OdsRtSzdnSnapshotFlowAddcode queryParam = new OdsRtSzdnSnapshotFlowAddcode();
            queryParam.setApplyTime1(startDate);
            queryParam.setApplyTime2(endDate);
            queryParam.setPageNum(pageNum);
            queryParam.setPageSize(pageSize);

            return httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(queryParam);
        } catch (Exception e) {
            log.error("【分表同步任务】从GaussDB拉取数据失败: {}", e.getMessage());
            return null;
        }
    }

    private List<OdsRtSzdnSnapshotFlowAddcode> convertToEntityList(List<?> rows) {
        List<OdsRtSzdnSnapshotFlowAddcode> list = new ArrayList<>();
        for (Object row : rows) {
            if (row instanceof OdsRtSzdnSnapshotFlowAddcode) {
                list.add((OdsRtSzdnSnapshotFlowAddcode) row);
            }
        }
        return list;
    }

    private Map<String, List<OdsRtSzdnSnapshotFlowAddcode>> groupByMonth(List<OdsRtSzdnSnapshotFlowAddcode> dataList) {
        Map<String, List<OdsRtSzdnSnapshotFlowAddcode>> grouped = new LinkedHashMap<>();

        for (OdsRtSzdnSnapshotFlowAddcode data : dataList) {
            if (data.getSnapshottime() != null) {
                String tableName = ShardingTableUtil.getTableNameByDate(data.getSnapshottime());
                grouped.computeIfAbsent(tableName, k -> new ArrayList<>()).add(data);
            }
        }

        return grouped;
    }

    private void ensureTableExists(String tableName) {
        try {
            int exists = snapshotFlowMapper.checkTableExists(tableName);
            if (exists == 0) {
                snapshotFlowMapper.createShardingTable(tableName);
                log.info("【分表同步任务】创建分表: {}", tableName);
            }
        } catch (Exception e) {
            log.error("【分表同步任务】创建分表失败: {}", e.getMessage());
        }
    }

    private void insertBatchToTable(String tableName, List<OdsRtSzdnSnapshotFlowAddcode> list) {
        try {
            snapshotFlowMapper.insertBatchToTable(tableName, list);
        } catch (Exception e) {
            log.error("【分表同步任务】批量插入失败: {}", e.getMessage());
            throw e;
        }
    }

    private String formatDate(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd").format(date);
    }

    private String formatDateTime(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    /**
     * 手动触发全量同步
     */
    @Scheduled(cron = "0 */5 * * * *")
    public AjaxResult manualFullSync() {
        return syncFullData();
    }

    /**
     * 手动触发增量同步
     */
    public AjaxResult manualIncrementalSync() {
        syncIncrementalData();
        return AjaxResult.success("增量同步任务已触发");
    }

    /**
     * 提前创建未来N个月的分表
     */
    public void preCreateTables(int months) {
        List<String> futureTableNames = ShardingTableUtil.getFutureTableNames(months);
        for (String tableName : futureTableNames) {
            ensureTableExists(tableName);
        }
        log.info("【分表同步任务】已提前创建 {} 个未来分表", futureTableNames.size());
    }
}
