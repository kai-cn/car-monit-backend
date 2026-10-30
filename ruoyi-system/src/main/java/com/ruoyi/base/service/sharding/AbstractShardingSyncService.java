package com.ruoyi.base.service.sharding;

import com.ruoyi.base.sharding.ShardingConfig;
import com.ruoyi.base.sharding.ShardingConfig.ShardingStrategy;
import com.ruoyi.base.sharding.ShardingTableUtil;
import lombok.extern.slf4j.Slf4j;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 通用分表同步服务抽象实现
 * <p>
 * 提供分表同步的通用逻辑，子类只需实现数据源相关的抽象方法即可
 * </p>
 *
 * @param <T> 实体类型
 */
@Slf4j
public abstract class AbstractShardingSyncService<T> implements ShardingSyncService<T> {

    /**
     * 并发同步线程池
     */
    private ExecutorService syncExecutor;

    /**
     * 同步进度缓存（用于断点续传）
     */
    private Map<String, SyncProgress> syncProgressCache = new ConcurrentHashMap<>();

    /**
     * 同步进度类
     */
    protected static class SyncProgress {
        private String period;
        private int totalCount;
        private int completedCount;
        private String lastSyncId;
        private boolean completed;
        private Date startTime;
        private Date endTime;

        // Getters and Setters
        public String getPeriod() { return period; }
        public void setPeriod(String period) { this.period = period; }
        public int getTotalCount() { return totalCount; }
        public void setTotalCount(int totalCount) { this.totalCount = totalCount; }
        public int getCompletedCount() { return completedCount; }
        public void setCompletedCount(int completedCount) { this.completedCount = completedCount; }
        public String getLastSyncId() { return lastSyncId; }
        public void setLastSyncId(String lastSyncId) { this.lastSyncId = lastSyncId; }
        public boolean isCompleted() { return completed; }
        public void setCompleted(boolean completed) { this.completed = completed; }
        public Date getStartTime() { return startTime; }
        public void setStartTime(Date startTime) { this.startTime = startTime; }
        public Date getEndTime() { return endTime; }
        public void setEndTime(Date endTime) { this.endTime = endTime; }
    }

    /**
     * 初始化线程池
     */
    protected AbstractShardingSyncService() {
        this.syncExecutor = Executors.newFixedThreadPool(4, r -> 
            new Thread(r, "sharding-sync-" + getTablePrefix())
        );
        log.info("【分表同步】初始化线程池，表前缀: {}", getTablePrefix());
    }

    @Override
    public int syncFullData() {
        log.info("【分表同步-全量】开始全量同步，表前缀: {}", getTablePrefix());
        long startTime = System.currentTimeMillis();

        try {
            // 获取最早日期和当前日期
            Date earliestDate = getEarliestDate();
            if (earliestDate == null) {
                log.warn("【分表同步-全量】未查询到最早数据，表前缀: {}", getTablePrefix());
                return 0;
            }

            Date now = new Date();
            ShardingStrategy strategy = getShardingConfig().getStrategy();

            // 获取周期列表
            List<String> periods = getPeriods(earliestDate, now, strategy);
            log.info("【分表同步-全量】时间范围: {} 至 {}, 周期数: {}, 周期列表: {}",
                    ShardingTableUtil.formatDate(earliestDate), 
                    ShardingTableUtil.formatDate(now),
                    periods.size(), periods);

            // 并发同步每个周期
            int totalCount = syncByPeriods(periods);

            long endTime = System.currentTimeMillis();
            log.info("【分表同步-全量】完成全量同步，表前缀: {}, 同步记录数: {}, 耗时: {} ms",
                    getTablePrefix(), totalCount, endTime - startTime);

            return totalCount;

        } catch (Exception e) {
            log.error("【分表同步-全量】全量同步失败，表前缀: {}, 错误: {}", getTablePrefix(), e.getMessage(), e);
            return 0;
        }
    }

    @Override
    public int syncIncrementalData() {
        log.info("【分表同步-增量】开始增量同步，表前缀: {}", getTablePrefix());
        long startTime = System.currentTimeMillis();

        try {
            ShardingStrategy strategy = getShardingConfig().getStrategy();
            String currentPeriodTable = ShardingTableUtil.getCurrentPeriodTable(getTablePrefix(), strategy);

            // 查询上次同步时间
            Date lastSyncTime = getMaxShardingFieldValue(currentPeriodTable);
            Date now = new Date();

            // 构建查询范围
            Date startDate;
            if (lastSyncTime == null) {
                startDate = ShardingTableUtil.getPeriodStart(now, strategy);
            } else {
                startDate = lastSyncTime;
            }

            log.info("【分表同步-增量】同步时间范围: {} 至 {}", 
                    ShardingTableUtil.formatDate(startDate), ShardingTableUtil.formatDate(now));

            // 执行同步
            int count = syncByDateRange(startDate, now);

            long endTime = System.currentTimeMillis();
            log.info("【分表同步-增量】完成增量同步，表前缀: {}, 同步记录数: {}, 耗时: {} ms",
                    getTablePrefix(), count, endTime - startTime);

            return count;

        } catch (Exception e) {
            log.error("【分表同步-增量】增量同步失败，表前缀: {}, 错误: {}", getTablePrefix(), e.getMessage(), e);
            return 0;
        }
    }

    @Override
    public int syncByDateRange(Date startDate, Date endDate) {
        if (startDate == null || endDate == null) {
            return 0;
        }

        ShardingStrategy strategy = getShardingConfig().getStrategy();
        List<String> periods = getPeriods(startDate, endDate, strategy);

        int totalCount = 0;
        for (String period : periods) {
            totalCount += syncByPeriod(period);
        }

        return totalCount;
    }

    @Override
    public int syncByPeriod(String period) {
        log.info("【分表同步-周期】开始同步周期: {}, 表前缀: {}", period, getTablePrefix());

        ShardingStrategy strategy = getShardingConfig().getStrategy();
        String tableName = getTablePrefix() + "_" + period;

        // 确保分表存在
        ensureTableExists(tableName);

        // 获取该周期的时间范围
        Date periodStart = parsePeriodStart(period, strategy);
        Date periodEnd = parsePeriodEnd(period, strategy);

        if (periodStart == null || periodEnd == null) {
            log.warn("【分表同步-周期】无法解析周期: {}", period);
            return 0;
        }

        int totalCount = 0;
        int pageNum = 1;
        int pageSize = getShardingConfig().getSyncBatchSize();

        while (true) {
            List<T> dataList = fetchFromSource(periodStart, periodEnd, pageNum, pageSize);

            if (dataList == null || dataList.isEmpty()) {
                break;
            }

            // 按分表字段分组（处理边界情况）
            Map<String, List<T>> grouped = groupByShardingField(dataList, strategy);

            for (Map.Entry<String, List<T>> entry : grouped.entrySet()) {
                String targetTable = entry.getKey();
                List<T> list = entry.getValue();

                ensureTableExists(targetTable);
                batchInsertToTable(targetTable, list);
                totalCount += list.size();
            }

            if (dataList.size() < pageSize) {
                break;
            }

            pageNum++;
        }

        log.info("【分表同步-周期】周期 {} 同步完成，表前缀: {}, 记录数: {}", 
                period, getTablePrefix(), totalCount);

        return totalCount;
    }

    /**
     * 并发同步多个周期
     */
    private int syncByPeriods(List<String> periods) {
        AtomicInteger totalCount = new AtomicInteger(0);
        List<Future<Integer>> futures = new ArrayList<>();

        for (String period : periods) {
            Future<Integer> future = syncExecutor.submit(() -> {
                return syncByPeriod(period);
            });
            futures.add(future);
        }

        for (Future<Integer> future : futures) {
            try {
                totalCount.addAndGet(future.get());
            } catch (InterruptedException | ExecutionException e) {
                log.error("【分表同步-并发】等待任务完成失败: {}", e.getMessage());
            }
        }

        return totalCount.get();
    }

    /**
     * 获取周期列表
     */
    private List<String> getPeriods(Date startDate, Date endDate, ShardingStrategy strategy) {
        List<String> periods = new ArrayList<>();

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        while (!startCal.after(endCal)) {
            String period = getPeriodString(startCal.getTime(), strategy);
            if (!periods.contains(period)) {
                periods.add(period);
            }
            advanceCalendar(startCal, strategy);
        }

        return periods;
    }

    /**
     * 获取周期字符串
     */
    private String getPeriodString(Date date, ShardingStrategy strategy) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(date);
        int year = cal.get(Calendar.YEAR);
        int month = cal.get(Calendar.MONTH) + 1;
        int day = cal.get(Calendar.DAY_OF_MONTH);
        int quarter = (month - 1) / 3 + 1;

        if (strategy == ShardingStrategy.DAILY) {
            return String.format("%04d%02d%02d", year, month, day);
        } else if (strategy == ShardingStrategy.MONTHLY) {
            return String.format("%04d%02d", year, month);
        } else if (strategy == ShardingStrategy.QUARTERLY) {
            return String.format("%04dQ%d", year, quarter);
        } else if (strategy == ShardingStrategy.YEARLY) {
            return String.format("%04d", year);
        } else {
            return String.format("%04d%02d", year, month); // 默认按月分表
        }
    }

    /**
     * 推进日历
     */
    private void advanceCalendar(Calendar calendar, ShardingStrategy strategy) {
        if (strategy == ShardingStrategy.DAILY) {
            calendar.add(Calendar.DAY_OF_MONTH, 1);
        } else if (strategy == ShardingStrategy.MONTHLY) {
            calendar.add(Calendar.MONTH, 1);
        } else if (strategy == ShardingStrategy.QUARTERLY) {
            calendar.add(Calendar.MONTH, 3);
        } else if (strategy == ShardingStrategy.YEARLY) {
            calendar.add(Calendar.YEAR, 1);
        }
    }

    /**
     * 解析周期起始日期
     */
    private Date parsePeriodStart(String period, ShardingStrategy strategy) {
        try {
            Calendar cal = Calendar.getInstance();
            
            switch (strategy) {
                case DAILY:
                    cal.set(Integer.parseInt(period.substring(0, 4)),
                            Integer.parseInt(period.substring(4, 6)) - 1,
                            Integer.parseInt(period.substring(6, 8)),
                            0, 0, 0);
                    break;
                case MONTHLY:
                    cal.set(Integer.parseInt(period.substring(0, 4)),
                            Integer.parseInt(period.substring(4, 6)) - 1,
                            1, 0, 0, 0);
                    break;
                case QUARTERLY:
                    int year = Integer.parseInt(period.substring(0, 4));
                    int quarter = Integer.parseInt(period.substring(5));
                    cal.set(year, (quarter - 1) * 3, 1, 0, 0, 0);
                    break;
                case YEARLY:
                    cal.set(Integer.parseInt(period), 0, 1, 0, 0, 0);
                    break;
            }
            
            cal.set(Calendar.MILLISECOND, 0);
            return cal.getTime();
        } catch (Exception e) {
            log.error("【分表同步】解析周期起始日期失败: {}", period);
            return null;
        }
    }

    /**
     * 解析周期结束日期
     */
    private Date parsePeriodEnd(String period, ShardingStrategy strategy) {
        Date start = parsePeriodStart(period, strategy);
        if (start == null) {
            return null;
        }

        Calendar cal = Calendar.getInstance();
        cal.setTime(start);

        if (strategy == ShardingStrategy.DAILY) {
            cal.add(Calendar.DAY_OF_MONTH, 1);
        } else if (strategy == ShardingStrategy.MONTHLY) {
            cal.add(Calendar.MONTH, 1);
        } else if (strategy == ShardingStrategy.QUARTERLY) {
            cal.add(Calendar.MONTH, 3);
        } else if (strategy == ShardingStrategy.YEARLY) {
            cal.add(Calendar.YEAR, 1);
        }

        cal.add(Calendar.MILLISECOND, -1);
        return cal.getTime();
    }

    /**
     * 按分表字段分组
     */
    private Map<String, List<T>> groupByShardingField(List<T> dataList, ShardingStrategy strategy) {
        Map<String, List<T>> grouped = new LinkedHashMap<>();

        for (T data : dataList) {
            Date shardingValue = getShardingFieldValue(data);
            if (shardingValue != null) {
                String tableName = ShardingTableUtil.getTableNameByDate(getTablePrefix(), shardingValue, strategy);
                grouped.computeIfAbsent(tableName, k -> new ArrayList<>()).add(data);
            }
        }

        return grouped;
    }

    /**
     * 确保分表存在
     */
    protected void ensureTableExists(String tableName) {
        if (getShardingConfig().isAutoCreateTable() && !checkTableExists(tableName)) {
            createShardingTable(tableName);
            log.info("【分表同步】创建分表: {}", tableName);
        }
    }

    @Override
    public void preCreateTables(int periods) {
        ShardingStrategy strategy = getShardingConfig().getStrategy();
        List<String> futureTableNames = ShardingTableUtil.getFutureTableNames(getTablePrefix(), periods, strategy);
        
        for (String tableName : futureTableNames) {
            ensureTableExists(tableName);
        }
        
        log.info("【分表同步】已提前创建 {} 个未来分表，表前缀: {}", futureTableNames.size(), getTablePrefix());
    }

    /**
     * 获取最早日期（需要子类实现）
     */
    protected abstract Date getEarliestDate();

    /**
     * 获取同步进度
     */
    public Map<String, SyncProgress> getSyncProgress() {
        return syncProgressCache;
    }

    /**
     * 重置同步进度
     */
    public void resetSyncProgress() {
        syncProgressCache.clear();
    }
}
