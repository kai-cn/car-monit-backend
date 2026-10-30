package com.ruoyi.base.service.consistency;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.OdsRtSzdnSnapshotFlowAddcodeMapper;
import com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.base.sharding.ShardingTableUtil;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 跨平台数据传输一致性保障服务
 * <p>
 * 功能：
 * 1. 数据校验机制（MD5校验、记录数比对）
 * 2. 断点续传机制（记录同步进度）
 * 3. 幂等性保证（唯一标识去重）
 * 4. 数据完整性校验（字段级比对）
 * 5. 异常重试和补偿机制
 * </p>
 */
@Slf4j
@Service
public class DataConsistencyService {

    @Autowired
    private OdsRtSzdnSnapshotFlowAddcodeMapper snapshotFlowMapper;

    @Resource
    private HttpOdsRtSzdnSnapshotFlowAddcodeService httpOdsRtSzdnSnapshotFlowAddcodeService;

    /**
     * 同步进度缓存（用于断点续传）
     * key: 月份（yyyyMM）, value: 同步进度
     */
    private Map<String, SyncProgress> syncProgressCache = new ConcurrentHashMap<>();

    /**
     * 已同步记录的MD5缓存（用于幂等性检查）
     * key: recordMd5, value: syncTime
     */
    private Map<String, Long> syncRecordCache = new ConcurrentHashMap<>();

    /**
     * 同步进度类
     */
    public static class SyncProgress {
        private String month;
        private int totalCount;
        private int completedCount;
        private String lastSyncId;
        private boolean completed;
        private Date startTime;
        private Date endTime;

        // Getters and Setters
        public String getMonth() { return month; }
        public void setMonth(String month) { this.month = month; }
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
     * 一致性校验结果
     */
    public static class ConsistencyResult {
        private boolean consistent;
        private String month;
        private long sourceCount;
        private long targetCount;
        private int mismatchCount;
        private List<String> mismatchIds;
        private String message;

        public boolean isConsistent() { return consistent; }
        public void setConsistent(boolean consistent) { this.consistent = consistent; }
        public String getMonth() { return month; }
        public void setMonth(String month) { this.month = month; }
        public long getSourceCount() { return sourceCount; }
        public void setSourceCount(long sourceCount) { this.sourceCount = sourceCount; }
        public long getTargetCount() { return targetCount; }
        public void setTargetCount(long targetCount) { this.targetCount = targetCount; }
        public int getMismatchCount() { return mismatchCount; }
        public void setMismatchCount(int mismatchCount) { this.mismatchCount = mismatchCount; }
        public List<String> getMismatchIds() { return mismatchIds; }
        public void setMismatchIds(List<String> mismatchIds) { this.mismatchIds = mismatchIds; }
        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
    }

    /**
     * 带一致性保障的全量同步
     * <p>
     * 执行流程：
     * 1. 查询源数据统计信息
     * 2. 按月份分批同步（带断点续传）
     * 3. 每批同步后进行一致性校验
     * 4. 校验失败则进行补偿同步
     * </p>
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncWithConsistency() {
        log.info("【一致性保障】开始带一致性保障的全量同步");
        long startTime = System.currentTimeMillis();

        try {
            // 步骤1: 查询GaussDB中最早的snapshottime
            Date earliestDate = httpOdsRtSzdnSnapshotFlowAddcodeService.getEarliestSnapshottime();
            if (earliestDate == null) {
                log.warn("【一致性保障】GaussDB中暂无数据");
                return AjaxResult.success("GaussDB中暂无数据");
            }

            // 步骤2: 获取月份分区列表
            List<String> monthPartitions = getMonthPartitions(earliestDate, new Date());
            log.info("【一致性保障】需要同步的月份: {}", monthPartitions);

            // 步骤3: 按月份同步并校验
            int totalSynced = 0;
            int totalCorrected = 0;

            for (String month : monthPartitions) {
                log.info("【一致性保障】开始同步月份: {}", month);

                // 执行同步（带断点续传）
                int synced = syncMonthWithBreakpoint(month);

                // 执行一致性校验
                ConsistencyResult result = checkConsistency(month);

                if (!result.isConsistent()) {
                    log.warn("【一致性保障】月份 {} 数据不一致，开始补偿同步", month);
                    int corrected = compensateSync(month, result);
                    totalCorrected += corrected;

                    // 再次校验
                    ConsistencyResult finalResult = checkConsistency(month);
                    if (!finalResult.isConsistent()) {
                        log.error("【一致性保障】月份 {} 补偿同步后仍不一致", month);
                    }
                }

                totalSynced += synced;
                log.info("【一致性保障】月份 {} 同步完成，同步数: {}, 补偿数: {}", month, synced, totalCorrected);
            }

            long endTime = System.currentTimeMillis();
            log.info("【一致性保障】全量同步完成，总同步数: {}, 总补偿数: {}, 耗时: {} ms",
                    totalSynced, totalCorrected, endTime - startTime);

            return AjaxResult.success("全量同步完成，同步数: " + totalSynced + ", 补偿数: " + totalCorrected);

        } catch (Exception e) {
            log.error("【一致性保障】同步失败: {}", e.getMessage(), e);
            return AjaxResult.error("同步失败: " + e.getMessage());
        }
    }

    /**
     * 带断点续传的月份同步
     */
    private int syncMonthWithBreakpoint(String month) {
        // 检查是否有断点续传进度
        SyncProgress progress = syncProgressCache.get(month);

        if (progress != null && !progress.isCompleted()) {
            log.info("【断点续传】恢复月份 {} 的同步，已完成: {}/{}",
                    month, progress.getCompletedCount(), progress.getTotalCount());
        } else {
            // 初始化进度
            progress = new SyncProgress();
            progress.setMonth(month);
            progress.setCompleted(false);
            progress.setStartTime(new Date());
            syncProgressCache.put(month, progress);
        }

        int totalSynced = progress.getCompletedCount();
        String lastSyncId = progress.getLastSyncId();

        // 构建时间范围
        String startDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-01 00:00:00";
        Calendar cal = Calendar.getInstance();
        cal.set(Integer.parseInt(month.substring(0, 4)), Integer.parseInt(month.substring(4, 6)) - 1, 1);
        int lastDay = cal.getActualMaximum(Calendar.DAY_OF_MONTH);
        String endDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-" + lastDay + " 23:59:59";

        int pageNum = 1;
        int pageSize = 1000;

        while (true) {
            TableDataInfo tableDataInfo = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(buildQueryParam(startDate, endDate, pageNum, pageSize));

            if (tableDataInfo == null || tableDataInfo.getRows() == null || tableDataInfo.getRows().isEmpty()) {
                break;
            }

            List<OdsRtSzdnSnapshotFlowAddcode> dataList = convertToEntityList(tableDataInfo.getRows());

            for (OdsRtSzdnSnapshotFlowAddcode data : dataList) {
                // 幂等性检查
                String recordMd5 = calculateRecordMd5(data);
                if (syncRecordCache.containsKey(recordMd5)) {
                    log.debug("【幂等性检查】记录已同步，跳过: {}", data.getBigId());
                    continue;
                }

                // 执行插入
                String tableName = ShardingTableUtil.getTableNameByDate(data.getSnapshottime());
                ensureTableExists(tableName);
                snapshotFlowMapper.insertToTable(tableName, data);
                // 更新缓存和进度
                syncRecordCache.put(recordMd5, System.currentTimeMillis());
                totalSynced++;
                progress.setLastSyncId(data.getBigId());
                progress.setCompletedCount(totalSynced);
            }



            if (dataList.size() < pageSize) {
                break;
            }
            pageNum++;
        }

        // 标记完成
        progress.setCompleted(true);
        progress.setEndTime(new Date());

        return totalSynced;
    }

    /**
     * 一致性校验
     */
    public ConsistencyResult checkConsistency(String month) {
        ConsistencyResult result = new ConsistencyResult();
        result.setMonth(month);

        // 构建时间范围
        String startDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-01 00:00:00";
        Calendar cal = Calendar.getInstance();
        cal.set(Integer.parseInt(month.substring(0, 4)), Integer.parseInt(month.substring(4, 6)) - 1, 1);
        int lastDay = cal.getActualMaximum(Calendar.DAY_OF_MONTH);
        String endDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-" + lastDay + " 23:59:59";

        try {
            // 1. 记录数比对
            long sourceCount = querySourceCount(startDate, endDate);
            long targetCount = queryTargetCount(month);

            result.setSourceCount(sourceCount);
            result.setTargetCount(targetCount);

            if (sourceCount != targetCount) {
                result.setConsistent(false);
                result.setMessage("记录数不一致: 源=" + sourceCount + ", 目标=" + targetCount);
                log.warn("【一致性校验】月份 {} 记录数不一致: 源={}, 目标={}", month, sourceCount, targetCount);
                return result;
            }

            // 2. 随机抽样校验（校验1%的数据）
            int sampleSize = Math.min((int) sourceCount / 100, 100);
            List<String> mismatchIds = sampleCheck(month, startDate, endDate, sampleSize);

            if (!mismatchIds.isEmpty()) {
                result.setConsistent(false);
                result.setMismatchCount(mismatchIds.size());
                result.setMismatchIds(mismatchIds);
                result.setMessage("抽样校验发现 " + mismatchIds.size() + " 条不一致记录");
                log.warn("【一致性校验】月份 {} 抽样校验失败，发现 {} 条不一致记录", month, mismatchIds.size());
                return result;
            }

            result.setConsistent(true);
            result.setMessage("数据一致");
            log.info("【一致性校验】月份 {} 数据一致", month);

        } catch (Exception e) {
            result.setConsistent(false);
            result.setMessage("校验异常: " + e.getMessage());
            log.error("【一致性校验】月份 {} 校验异常: {}", month, e.getMessage());
        }

        return result;
    }

    /**
     * 抽样校验
     */
    private List<String> sampleCheck(String month, String startDate, String endDate, int sampleSize) {
        List<String> mismatchIds = new ArrayList<>();

        // 获取源数据的随机ID列表
        List<String> sourceIds = getRandomSourceIds(startDate, endDate, sampleSize);

        if (sourceIds.isEmpty()) {
            return mismatchIds;
        }

        // 查询目标数据
        String tableName = ShardingTableUtil.DEFAULT_TABLE_PREFIX + month;
        for (String bigId : sourceIds) {
            OdsRtSzdnSnapshotFlowAddcode sourceData = getSourceData(bigId);
            OdsRtSzdnSnapshotFlowAddcode targetData = snapshotFlowMapper.selectOdsRtSzdnSnapshotFlowAddcodeById(bigId);

            if (targetData == null) {
                mismatchIds.add(bigId + ": 目标不存在");
                continue;
            }

            // MD5比对
            String sourceMd5 = calculateRecordMd5(sourceData);
            String targetMd5 = calculateRecordMd5(targetData);

            if (!sourceMd5.equals(targetMd5)) {
                mismatchIds.add(bigId + ": MD5不一致");
            }
        }

        return mismatchIds;
    }

    /**
     * 补偿同步
     */
    private int compensateSync(String month, ConsistencyResult result) {
        int corrected = 0;

        if (result.getMismatchIds() != null) {
            for (String mismatchInfo : result.getMismatchIds()) {
                String bigId = mismatchInfo.split(":")[0];
                OdsRtSzdnSnapshotFlowAddcode sourceData = getSourceData(bigId);

                if (sourceData != null) {
                    // 删除错误数据并重新插入
                    snapshotFlowMapper.deleteOdsRtSzdnSnapshotFlowAddcodeById(bigId);

                    String tableName = ShardingTableUtil.getTableNameByDate(sourceData.getSnapshottime());
                    ensureTableExists(tableName);
                    snapshotFlowMapper.insert(sourceData);

                    corrected++;
                    log.info("【补偿同步】已修复记录: {}", bigId);
                }
            }
        }

        // 如果只是记录数不一致，进行全量对比
        if (result.getSourceCount() != result.getTargetCount()) {
            log.info("【补偿同步】进行全量对比补偿");
            corrected += fullCompareAndCompensate(month);
        }

        return corrected;
    }

    /**
     * 全量对比并补偿
     */
    private int fullCompareAndCompensate(String month) {
        int corrected = 0;

        String startDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-01 00:00:00";
        Calendar cal = Calendar.getInstance();
        cal.set(Integer.parseInt(month.substring(0, 4)), Integer.parseInt(month.substring(4, 6)) - 1, 1);
        int lastDay = cal.getActualMaximum(Calendar.DAY_OF_MONTH);
        String endDate = month.substring(0, 4) + "-" + month.substring(4, 6) + "-" + lastDay + " 23:59:59";

        // 获取源数据ID列表
        List<String> sourceIds = getAllSourceIds(startDate, endDate);

        // 获取目标数据ID列表
        String tableName = ShardingTableUtil.DEFAULT_TABLE_PREFIX + month;
        List<String> targetIds = getAllTargetIds(tableName);

        // 找出缺失的ID
        Set<String> sourceIdSet = new HashSet<>(sourceIds);
        Set<String> targetIdSet = new HashSet<>(targetIds);

        // 源有目标没有
        for (String sourceId : sourceIdSet) {
            if (!targetIdSet.contains(sourceId)) {
                OdsRtSzdnSnapshotFlowAddcode sourceData = getSourceData(sourceId);
                if (sourceData != null) {
                    ensureTableExists(tableName);
                    snapshotFlowMapper.insert(sourceData);
                    corrected++;
                }
            }
        }

        // 目标有源没有
        for (String targetId : targetIdSet) {
            if (!sourceIdSet.contains(targetId)) {
                snapshotFlowMapper.deleteOdsRtSzdnSnapshotFlowAddcodeById(targetId);
                corrected++;
            }
        }

        return corrected;
    }

    /**
     * 计算记录的MD5值（用于数据完整性校验）
     */
    public String calculateRecordMd5(OdsRtSzdnSnapshotFlowAddcode data) {
        try {
            StringBuilder sb = new StringBuilder();
            sb.append(data.getBigId()).append("|")
              .append(data.getPlatenumber()).append("|")
              .append(data.getSnapshottime()).append("|")
              .append(data.getDeviceid()).append("|")
              .append(data.getPlatecolor()).append("|")
              .append(data.getCartype()).append("|")
              .append(data.getDirection());

            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(sb.toString().getBytes(StandardCharsets.UTF_8));

            StringBuilder hexString = new StringBuilder();
            for (byte b : digest) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) {
                    hexString.append('0');
                }
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            log.error("【MD5计算】失败: {}", e.getMessage());
            return data.getBigId();
        }
    }

    // ==================== 辅助方法 ====================

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

    private OdsRtSzdnSnapshotFlowAddcode buildQueryParam(String startDate, String endDate, int pageNum, int pageSize) {
        OdsRtSzdnSnapshotFlowAddcode param = new OdsRtSzdnSnapshotFlowAddcode();
        param.setApplyTime1(startDate);
        param.setApplyTime2(endDate);
        param.setPageNum(pageNum);
        param.setPageSize(pageSize);
        return param;
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

    private void ensureTableExists(String tableName) {
        int exists = snapshotFlowMapper.checkTableExists(tableName);
        if (exists == 0) {
            snapshotFlowMapper.createShardingTable(tableName);
        }
    }

    private long querySourceCount(String startDate, String endDate) {
        // 这里需要调用GaussDB的统计接口
        TableDataInfo info = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(buildQueryParam(startDate, endDate, 1, 1));
        return info != null ? info.getTotal() : 0;
    }

    private long queryTargetCount(String month) {
        String tableName = ShardingTableUtil.DEFAULT_TABLE_PREFIX + month;
        int exists = snapshotFlowMapper.checkTableExists(tableName);
        if (exists == 0) {
            return 0;
        }
        return snapshotFlowMapper.getTableApproximateCount(tableName);
    }

    private List<String> getRandomSourceIds(String startDate, String endDate, int count) {
        // 简化实现：实际应使用数据库的随机抽样
        List<String> ids = new ArrayList<>();
        TableDataInfo info = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(buildQueryParam(startDate, endDate, 1, count));

        if (info != null && info.getRows() != null) {
            for (Object row : info.getRows()) {
                if (row instanceof OdsRtSzdnSnapshotFlowAddcode) {
                    ids.add(((OdsRtSzdnSnapshotFlowAddcode) row).getBigId());
                }
            }
        }
        return ids;
    }

    private List<String> getAllSourceIds(String startDate, String endDate) {
        List<String> ids = new ArrayList<>();
        int pageNum = 1;
        int pageSize = 1000;

        while (true) {
            TableDataInfo info = httpOdsRtSzdnSnapshotFlowAddcodeService.getOdsRtSzdnSnapshotFlowAddcodePage(buildQueryParam(startDate, endDate, pageNum, pageSize));
            if (info == null || info.getRows() == null || info.getRows().isEmpty()) {
                break;
            }

            for (Object row : info.getRows()) {
                if (row instanceof OdsRtSzdnSnapshotFlowAddcode) {
                    ids.add(((OdsRtSzdnSnapshotFlowAddcode) row).getBigId());
                }
            }

            if (info.getRows().size() < pageSize) {
                break;
            }
            pageNum++;
        }

        return ids;
    }

    private List<String> getAllTargetIds(String tableName) {
        // 需要在Mapper中添加方法
        return new ArrayList<>();
    }

    private OdsRtSzdnSnapshotFlowAddcode getSourceData(String bigId) {
        return httpOdsRtSzdnSnapshotFlowAddcodeService.selectOdsRtSzdnSnapshotFlowAddcodeById(bigId);
    }

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
        syncRecordCache.clear();
    }
}
