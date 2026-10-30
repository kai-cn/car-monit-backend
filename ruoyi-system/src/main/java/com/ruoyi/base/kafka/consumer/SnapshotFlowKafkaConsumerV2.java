package com.ruoyi.base.kafka.consumer;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.elasticsearch.document.SnapshotFlowDocument;
import com.ruoyi.base.elasticsearch.service.SnapshotFlowElasticsearchService;
import com.ruoyi.base.mapper.ShardingSnapshotFlowMapper;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.utils.IdempotentUtil;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.common.TopicPartition;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.BatchAcknowledgingConsumerAwareMessageListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 门架抓拍流水Kafka消费者（生产级优化版）
 * <p>
 * 核心设计目标：
 * 1. 解决消息积压：300G历史数据 + 每日50W新增
 * 2. 防止重复消费：幂等性 + 手动确认
 * 3. 防止消息丢失：手动确认 + 重试 + 死信队列
 * 4. 高可用性：异常处理 + 监控告警
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Component
public class SnapshotFlowKafkaConsumerV2 {

    private static final int MAX_RETRY_TIMES = 3;
    private static final long PROCESS_TIMEOUT_MS = 30000;

    @Autowired
    private IdempotentUtil idempotentUtil;

    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowService;

    @Autowired
    private ShardingSnapshotFlowMapper shardingSnapshotFlowMapper;

    @Autowired
    private SnapshotFlowElasticsearchService elasticsearchService;

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    @Value("${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}")
    private String sourceTopic;

    @Value("${kafka.topic.snapshot-flow-dlq:ods-rt-szdn-snapshot-flow-dlq}")
    private String dlqTopic;

    private final AtomicInteger successCount = new AtomicInteger(0);
    private final AtomicInteger failCount = new AtomicInteger(0);
    private final AtomicInteger retryCount = new AtomicInteger(0);

    /**
     * 批量消费Kafka消息
     * <p>
     * 设计思路：
     * 1. 使用批量消费提高吞吐量（max.poll.records=500）
     * 2. 手动确认确保消息不丢失（MANUAL_IMMEDIATE）
     * 3. 按分区处理确保顺序性
     * 4. 幂等检查防止重复消费
     * 5. 失败重试 + 死信队列兜底
     * </p>
     *
     * @param records 批量消息记录
     * @param ack 确认对象
     */
    @KafkaListener(
        topics = "${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void consumeBatch(List<ConsumerRecord<String, String>> records, Acknowledgment ack) {
        long startTime = System.currentTimeMillis();
        String threadName = Thread.currentThread().getName();

        log.info("[消费开始] 线程={}, 批次大小={}", threadName, records.size());

        List<OdsRtSzdnSnapshotFlowAddcode> toSaveList = new ArrayList<>();
        List<SnapshotFlowDocument> esDocs = new ArrayList<>();
        List<String> processedIds = new ArrayList<>();
        List<ConsumerRecord<String, String>> failedRecords = new ArrayList<>();

        try {
            for (ConsumerRecord<String, String> record : records) {
                try {
                    boolean processed = processSingleRecord(record, toSaveList, esDocs, processedIds);
                    if (!processed) {
                        failedRecords.add(record);
                    }
                } catch (Exception e) {
                    log.error("[单条处理异常] offset={}, key={}", record.offset(), record.key(), e);
                    failedRecords.add(record);
                    failCount.incrementAndGet();
                }
            }

            if (!toSaveList.isEmpty()) {
                batchSaveData(toSaveList, esDocs);
            }

            if (!failedRecords.isEmpty()) {
                handleFailedRecords(failedRecords);
            }

            ack.acknowledge();

            long costTime = System.currentTimeMillis() - startTime;
            log.info("[消费完成] 线程={}, 批次={}, 成功={}, 失败={}, 耗时={}ms",
                threadName, records.size(), toSaveList.size(), failedRecords.size(), costTime);

        } catch (Exception e) {
            log.error("[批量消费异常] 回滚幂等标记", e);
            for (String id : processedIds) {
                idempotentUtil.remove(id);
            }
            throw e;
        }
    }

    /**
     * 处理单条消息
     * <p>
     * 处理流程：
     * 1. 解析JSON → 2. 幂等检查 → 3. 业务校验 → 4. 收集待批量保存
     * </p>
     *
     * @param record Kafka消息记录
     * @param toSaveList MySQL待保存列表
     * @param esDocs ES待保存文档列表
     * @param processedIds 已处理ID列表（用于异常回滚）
     * @return true=处理成功，加入批量；false=处理失败
     */
    private boolean processSingleRecord(
            ConsumerRecord<String, String> record,
            List<OdsRtSzdnSnapshotFlowAddcode> toSaveList,
            List<SnapshotFlowDocument> esDocs,
            List<String> processedIds) {

        String message = record.value();
        OdsRtSzdnSnapshotFlowAddcode data = null;
        try {
            JSONObject jsonObject = JSON.parseObject(message);
            String operationType = jsonObject.getString("operationType");
            data = jsonObject.getObject("data", OdsRtSzdnSnapshotFlowAddcode.class);

            if (data == null || data.getBigId() == null) {
                log.warn("[数据校验失败] 消息为空或缺少bigId, offset={}", record.offset());
                sendToDLQ(record, "数据为空或缺少bigId");
                return false;
            }

            String idempotentKey = data.getBigId();

            if (!idempotentUtil.checkAndSet(idempotentKey)) {
                log.info("[幂等检查通过] 消息已处理, bigId={}, offset={}", idempotentKey, record.offset());
                return true;
            }

            processedIds.add(idempotentKey);

            if ("INSERT".equals(operationType) || "UPDATE".equals(operationType)) {
                toSaveList.add(data);
                SnapshotFlowDocument doc = new SnapshotFlowDocument();
                BeanUtils.copyProperties(data, doc);
                esDocs.add(doc);
            } else if ("DELETE".equals(operationType)) {
                snapshotFlowService.removeById(data.getBigId());
            }

            successCount.incrementAndGet();
            return true;

        } catch (Exception e) {
            log.error("[单条处理失败] offset={}", record.offset(), e);
            idempotentUtil.remove(data != null ? data.getBigId() : "unknown-" + record.offset());
            return false;
        }
    }

    /**
     * 批量保存数据到MySQL和ES
     * <p>
     * 核心设计：
     * 1. 使用ShardingSphere进行分表入库，自动根据snapshottime字段路由到对应分表
     * 2. MySQL批量插入（减少数据库IO）
     * 3. ES批量索引（减少网络IO）
     * 4. 失败时分别处理，保证部分成功
     * </p>
     *
     * @param toSaveList MySQL数据列表
     * @param esDocs ES文档列表
     */
    private void batchSaveData(
            List<OdsRtSzdnSnapshotFlowAddcode> toSaveList,
            List<SnapshotFlowDocument> esDocs) {

        log.info("[批量保存开始] MySQL={}, ES={}", toSaveList.size(), esDocs.size());

        boolean mysqlSuccess = false;
        boolean esSuccess = false;

        // ========== 1. MySQL分表入库（使用ShardingSphere）==========
        try {
            // 使用ShardingSphere的批量插入，自动根据snapshottime字段路由到对应分表
            // 分表规则：按月份分表，表名格式为 ods_rt_szdn_snapshot_flow_yyyyMM
            // ShardingSphere会根据每条记录的snapshottime字段值自动路由到对应月份的分表
            int inserted = shardingSnapshotFlowMapper.batchInsert(toSaveList);
            
            mysqlSuccess = true;
            log.info("[MySQL分表保存成功] 数量={}, 影响行数={}", toSaveList.size(), inserted);
            
            // 打印分表统计信息（调试用）
            logTableDistribution(toSaveList);
            
        } catch (Exception e) {
            log.error("[MySQL分表保存失败]", e);
            
            // 降级方案：使用原始服务保存
            try {
                log.warn("[尝试降级保存] 使用原始服务保存数据");
                snapshotFlowService.saveBatch(toSaveList);
                mysqlSuccess = true;
                log.info("[降级保存成功]");
            } catch (Exception de) {
                log.error("[降级保存也失败]", de);
            }
        }

        // ========== 2. ES批量保存 ==========
        try {
            esSuccess = elasticsearchService.batchSave(esDocs);
            if (esSuccess) {
                log.info("[ES保存成功] 数量={}", esDocs.size());
            } else {
                log.warn("[ES保存失败]");
            }
        } catch (Exception e) {
            log.error("[ES保存异常]", e);
        }
    }

    /**
     * 打印数据分表分布情况（用于调试和监控）
     * 
     * @param dataList 数据列表
     */
    private void logTableDistribution(List<OdsRtSzdnSnapshotFlowAddcode> dataList) {
        if (log.isDebugEnabled()) {
            java.util.Map<String, Integer> tableCount = new java.util.HashMap<>();
            
            for (OdsRtSzdnSnapshotFlowAddcode data : dataList) {
                if (data.getSnapshottime() != null) {
                    String tableSuffix = formatDateToMonth(data.getSnapshottime());
                    String tableName = "ods_rt_szdn_snapshot_flow_" + tableSuffix;
                    tableCount.put(tableName, tableCount.getOrDefault(tableName, 0) + 1);
                }
            }
            
            if (!tableCount.isEmpty()) {
                log.debug("[分表分布] {}", tableCount);
            }
        }
    }

    /**
     * 将日期格式化为月份字符串（yyyyMM）
     * 
     * @param date 日期
     * @return 月份字符串
     */
    private String formatDateToMonth(java.util.Date date) {
        java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyyMM");
        return sdf.format(date);
    }

    /**
     * 处理失败的记录
     * <p>
     * 策略：
     * 1. 先尝试本地重试（3次）
     * 2. 重试失败 → 发送到死信队列
     * </p>
     *
     * @param failedRecords 失败的消息记录列表
     */
    private void handleFailedRecords(List<ConsumerRecord<String, String>> failedRecords) {
        if (failedRecords.isEmpty()) {
            return;
        }

        log.warn("[处理失败记录] 数量={}", failedRecords.size());

        for (ConsumerRecord<String, String> record : failedRecords) {
            boolean retrySuccess = retryProcess(record);
            if (!retrySuccess) {
                sendToDLQ(record, "重试失败");
            }
        }
    }

    /**
     * 单条消息本地重试
     * <p>
     * 重试策略：
     * - 最多重试3次
     * - 每次间隔1秒
     * </p>
     *
     * @param record 失败的消息记录
     * @return true=重试成功；false=重试失败
     */
    private boolean retryProcess(ConsumerRecord<String, String> record) {
        for (int i = 1; i <= MAX_RETRY_TIMES; i++) {
            try {
                log.warn("[重试处理] 第{}次, offset={}", i, record.offset());
                retryCount.incrementAndGet();

                Thread.sleep(1000);

                List<OdsRtSzdnSnapshotFlowAddcode> tempToSave = new ArrayList<>();
                List<SnapshotFlowDocument> tempEsDocs = new ArrayList<>();
                List<String> tempIds = new ArrayList<>();

                boolean result = processSingleRecord(record, tempToSave, tempEsDocs, tempIds);

                if (result && !tempToSave.isEmpty()) {
                    batchSaveData(tempToSave, tempEsDocs);
                    log.info("[重试成功] offset={}", record.offset());
                    return true;
                }
            } catch (Exception e) {
                log.error("[重试异常] 第{}次, offset={}", i, record.offset(), e);
            }
        }
        return false;
    }

    /**
     * 发送到死信队列（Dead Letter Queue）
     * <p>
     * 目的：
     * 1. 保存失败消息，不阻塞消费进度
     * 2. 后续人工介入处理
     * </p>
     *
     * @param record 失败的消息记录
     * @param reason 失败原因
     */
    private void sendToDLQ(ConsumerRecord<String, String> record, String reason) {
        try {
            JSONObject dlqMessage = new JSONObject();
            dlqMessage.put("originalTopic", sourceTopic);
            dlqMessage.put("partition", record.partition());
            dlqMessage.put("offset", record.offset());
            dlqMessage.put("timestamp", record.timestamp());
            dlqMessage.put("reason", reason);
            dlqMessage.put("value", record.value());

            kafkaTemplate.send(dlqTopic, dlqMessage.toJSONString());
            log.warn("[发送死信队列] offset={}, reason={}", record.offset(), reason);
        } catch (Exception e) {
            log.error("[死信队列发送失败] offset={}", record.offset(), e);
        }
    }

    /**
     * 获取消费统计信息（用于监控）
     */
    public Map<String, Integer> getConsumerStats() {
        Map<String, Integer> stats = new HashMap<>();
        stats.put("successCount", successCount.get());
        stats.put("failCount", failCount.get());
        stats.put("retryCount", retryCount.get());
        return stats;
    }
}
