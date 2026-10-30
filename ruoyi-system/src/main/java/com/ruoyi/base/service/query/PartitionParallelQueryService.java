package com.ruoyi.base.service.query;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.mapper.SnapshotFlowMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

/**
 * 分区并行查询服务
 * <p>
 * 【设计思路】
 * 跨月份查询时，使用CompletableFuture并发查询多个分区，提升查询性能
 * 
 * <p>【性能提升原理】</p>
 * <pre>
 * 传统方式：串行扫描所有涉及的分区，总耗时 = 分区1耗时 + 分区2耗时 + ... + 分区N耗时
 * 并行方式：并发查询所有分区，总耗时 ≈ max(分区1耗时, 分区2耗时, ..., 分区N耗时)
 * 
 * 例如：跨3个月查询，每个分区查询耗时100ms
 * - 串行：300ms
 * - 并行：≈100ms（提升3倍）
 * </pre>
 * 
 * @author ruoyi
 */
@Slf4j
@Service
public class PartitionParallelQueryService {

    @Autowired
    private SnapshotFlowMapper snapshotFlowMapper;

    /**
     * 自定义线程池
     * <p>
     * 配置说明：
     * - 核心线程数：4（CPU核心数的1/2）
     * - 最大线程数：8（避免过多线程导致CPU竞争）
     * - 队列容量：100（缓冲任务）
     * - 拒绝策略：CallerRunsPolicy（队列满时由调用线程执行）
     */
    private final ExecutorService executorService = new ThreadPoolExecutor(
            4,                              // 核心线程数
            8,                              // 最大线程数
            60L,                            // 空闲线程存活时间
            TimeUnit.SECONDS,               // 时间单位
            new ArrayBlockingQueue<>(100),  // 任务队列
            Executors.defaultThreadFactory(),// 线程工厂
            new ThreadPoolExecutor.CallerRunsPolicy() // 拒绝策略
    );

    /**
     * 日期格式化器（线程安全）
     */
    private static final ThreadLocal<SimpleDateFormat> MONTH_FORMATTER = 
            ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyyMM"));

    /**
     * 并发查询多个分区
     * 
     * <p>【执行流程】</p>
     * <pre>
     * 1. 根据时间范围确定涉及的分区列表
     * 2. 创建CompletableFuture列表，每个分区对应一个Future
     * 3. 提交所有Future到线程池并发执行
     * 4. 使用allOf等待所有Future完成
     * 5. 合并各分区的查询结果并按时间排序
     * 6. 返回合并后的结果
     * </pre>
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 查询结果列表（按snapshottime升序排序）
     */
    public List<OdsRtSzdnSnapshotFlowAddcode> queryMultiPartitionParallel(
            Date startTime, Date endTime) {

        long queryStart = System.currentTimeMillis();

        // 步骤1：获取涉及的分区列表
        List<String> partitions = getPartitionsInRange(startTime, endTime);
        
        log.info("[并行查询开始] 时间范围: {} ~ {}, 涉及分区数: {}", 
                formatDate(startTime), formatDate(endTime), partitions.size());

        if (partitions.isEmpty()) {
            log.info("[并行查询结束] 无涉及分区，返回空列表");
            return Collections.emptyList();
        }

        // 步骤2：并发查询所有分区
        List<CompletableFuture<List<OdsRtSzdnSnapshotFlowAddcode>>> futures = 
                new ArrayList<>();

        for (String partition : partitions) {
            futures.add(queryPartitionAsync(partition, startTime, endTime));
        }

        // 步骤3：等待所有查询完成并合并结果
        CompletableFuture<Void> allFutures = CompletableFuture.allOf(
                futures.toArray(new CompletableFuture[0])
        );

        List<OdsRtSzdnSnapshotFlowAddcode> result = allFutures.thenApply(v -> {
            return futures.stream()
                    .map(future -> {
                        try {
                            return future.get();
                        } catch (InterruptedException | ExecutionException e) {
                            log.error("[分区查询失败]", e);
                            return Collections.<OdsRtSzdnSnapshotFlowAddcode>emptyList();
                        }
                    })
                    .flatMap(List::stream)
                    .sorted(Comparator.comparing(OdsRtSzdnSnapshotFlowAddcode::getSnapshottime))
                    .collect(Collectors.toList());
        }).join();

        long queryEnd = System.currentTimeMillis();
        log.info("[并行查询结束] 总记录数: {}, 耗时: {}ms", result.size(), queryEnd - queryStart);

        return result;
    }

    /**
     * 异步查询单个分区
     * 
     * <p>【实现细节】</p>
     * 使用CompletableFuture.supplyAsync提交异步任务，
     * 任务执行时调用Mapper查询指定分区的数据
     * 
     * @param partition 分区名
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return CompletableFuture包装的查询结果
     */
    private CompletableFuture<List<OdsRtSzdnSnapshotFlowAddcode>> queryPartitionAsync(
            String partition, Date startTime, Date endTime) {

        return CompletableFuture.supplyAsync(() -> {
            long start = System.currentTimeMillis();
            
            // 使用分区提示查询指定分区
            List<OdsRtSzdnSnapshotFlowAddcode> data = 
                    snapshotFlowMapper.queryByPartition(partition, startTime, endTime);
            
            long end = System.currentTimeMillis();
            log.debug("[分区查询完成] partition={}, 记录数={}, 耗时={}ms", 
                    partition, data.size(), end - start);
            
            return data;
        }, executorService);
    }

    /**
     * 获取时间范围内涉及的分区列表
     * 
     * <p>【算法逻辑】</p>
     * <pre>
     * 1. 创建Calendar实例，设置为开始时间
     * 2. 循环遍历每个月份，直到超过结束时间
     * 3. 每个月份生成对应的分区名（格式：p+yyyyMM）
     * 4. 返回分区名列表
     * </pre>
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 分区名列表，按时间顺序排列
     */
    public List<String> getPartitionsInRange(Date startTime, Date endTime) {
        List<String> partitions = new ArrayList<>();

        if (startTime == null || endTime == null || startTime.after(endTime)) {
            return partitions;
        }

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startTime);
        // 重置到当月第一天，确保包含起始月份
        startCal.set(Calendar.DAY_OF_MONTH, 1);
        startCal.set(Calendar.HOUR_OF_DAY, 0);
        startCal.set(Calendar.MINUTE, 0);
        startCal.set(Calendar.SECOND, 0);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endTime);

        // 循环遍历所有月份
        while (!startCal.after(endCal)) {
            String partition = "p" + MONTH_FORMATTER.get().format(startCal.getTime());
            partitions.add(partition);
            startCal.add(Calendar.MONTH, 1);
        }

        return partitions;
    }

    /**
     * 分页查询（跨分区优化版）
     * 
     * <p>【优化思路】</p>
     * <pre>
     * 传统分页：扫描所有分区获取所有数据，再进行分页（效率低）
     * 优化分页：
     * 1. 估算每个分区的记录数
     * 2. 根据偏移量计算起始分区
     * 3. 从起始分区开始获取数据
     * 4. 如果当前分区数据不足，继续从下一个分区获取
     * 5. 直到获取足够的数据或所有分区遍历完毕
     * </pre>
     * 
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @param pageNum   页码（从1开始）
     * @param pageSize  每页大小
     * @return 分页结果
     */
    public PageResult<OdsRtSzdnSnapshotFlowAddcode> queryWithPageOptimized(
            Date startTime, Date endTime, int pageNum, int pageSize) {

        long queryStart = System.currentTimeMillis();

        // 步骤1：获取涉及的分区列表
        List<String> partitions = getPartitionsInRange(startTime, endTime);

        if (partitions.isEmpty()) {
            return new PageResult<>(Collections.emptyList(), 0);
        }

        // 步骤2：估算总记录数（使用近似计数）
        long total = estimateTotalCount(partitions, startTime, endTime);

        // 步骤3：计算分页偏移量
        int offset = (pageNum - 1) * pageSize;
        int currentOffset = offset;
        int remainingSize = pageSize;

        List<OdsRtSzdnSnapshotFlowAddcode> result = new ArrayList<>();

        // 步骤4：遍历分区，定位起始分区并获取数据
        for (String partition : partitions) {
            // 获取当前分区的记录数
            long partitionCount = getPartitionCount(partition, startTime, endTime);

            if (currentOffset >= partitionCount) {
                // 当前分区数据不足，跳过
                currentOffset -= partitionCount;
                continue;
            }

            // 查询当前分区的数据
            List<OdsRtSzdnSnapshotFlowAddcode> partitionData = 
                    snapshotFlowMapper.queryByPartitionWithOffset(
                            partition, startTime, endTime, currentOffset, remainingSize);

            result.addAll(partitionData);

            if (result.size() >= pageSize) {
                // 已获取足够数据，截断并退出循环
                result = result.subList(0, pageSize);
                break;
            }

            // 更新剩余需要获取的数据量
            remainingSize -= partitionData.size();
            currentOffset = 0;
        }

        long queryEnd = System.currentTimeMillis();
        log.info("[分页查询完成] 页码={}, 每页={}, 返回={}, 总数={}, 耗时={}ms", 
                pageNum, pageSize, result.size(), total, queryEnd - queryStart);

        return new PageResult<>(result, total);
    }

    /**
     * 估算总记录数
     * 
     * <p>【实现方式】</p>
     * 遍历所有涉及的分区，累加每个分区的记录数
     * 
     * @param partitions 分区列表
     * @param startTime  开始时间
     * @param endTime    结束时间
     * @return 总记录数
     */
    private long estimateTotalCount(List<String> partitions, Date startTime, Date endTime) {
        long total = 0;
        for (String partition : partitions) {
            total += getPartitionCount(partition, startTime, endTime);
        }
        return total;
    }

    /**
     * 获取分区记录数
     * 
     * <p>【实现方式】</p>
     * 调用Mapper查询指定分区的记录数
     * 
     * @param partition 分区名
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 记录数
     */
    private long getPartitionCount(String partition, Date startTime, Date endTime) {
        try {
            return snapshotFlowMapper.countByPartition(partition, startTime, endTime);
        } catch (Exception e) {
            log.error("[分区计数失败] partition={}", partition, e);
            return 0;
        }
    }

    /**
     * 格式化日期（日志输出用）
     */
    private String formatDate(Date date) {
        if (date == null) {
            return "null";
        }
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    /**
     * 分页结果封装类
     */
    public static class PageResult<T> {
        private List<T> data;
        private long total;

        public PageResult(List<T> data, long total) {
            this.data = data;
            this.total = total;
        }

        public List<T> getData() {
            return data;
        }

        public long getTotal() {
            return total;
        }
    }
}
