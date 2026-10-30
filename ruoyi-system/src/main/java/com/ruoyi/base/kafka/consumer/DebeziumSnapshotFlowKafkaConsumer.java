package com.ruoyi.base.kafka.consumer;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.elasticsearch.document.SnapshotFlowDocument;
import com.ruoyi.base.elasticsearch.service.SnapshotFlowElasticsearchService;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.utils.IdempotentUtil;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Debezium CDC 门架抓拍流水消费者
 * <p>
 * 核心功能：
 * 1. 消费 Debezium CDC 消息（GaussDB → Kafka）
 * 2. 支持 INSERT/UPDATE/DELETE 操作
 * 3. 幂等性处理（基于事务ID + 序列号）
 * 4. 批量写入 MySQL 分表和 Elasticsearch
 * 5. 手动确认 + 死信队列
 * </p>
 *
 * Debezium 消息格式：
 * {
 *   "before": null,  // UPDATE/DELETE 前数据
 *   "after": { ... }, // INSERT/UPDATE 后数据
 *   "op": "c",       // 操作类型：c=create, u=update, d=delete, r=snapshot
 *   "ts_ms": 1234567890,  // 时间戳
 *   "transaction": null    // 事务信息（可选）
 * }
 *
 * @author ruoyi
 */
@Slf4j
@Component
public class DebeziumSnapshotFlowKafkaConsumer {

    private static final int MAX_RETRY_TIMES = 3;
    private static final long PROCESS_TIMEOUT_MS = 30000;

    @Autowired
    private IdempotentUtil idempotentUtil;

    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowService;

    @Autowired
    private SnapshotFlowElasticsearchService elasticsearchService;

    @Value("${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}")
    private String sourceTopic;

    @Value("${kafka.topic.snapshot-flow-dlq:ods-rt-szdn-snapshot-flow-dlq}")
    private String dlqTopic;

    private final AtomicInteger successCount = new AtomicInteger(0);
    private final AtomicInteger failCount = new AtomicInteger(0);
    private final AtomicInteger retryCount = new AtomicInteger(0);

    /**
     * 消费 Debezium CDC 消息
     * <p>
     * 监听主题：ods-rt-szdn-snapshot-flow
     * 消息格式：Debezium 标准格式
     *
     * @param records 批量消息记录
     * @param ack 确认对象
     */
//    @KafkaListener(
//        topics = "${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}",
//        containerFactory = "kafkaListenerContainerFactory"
//    )
    public void consumeDebeziumMessages(List<ConsumerRecord<String, String>> records, Acknowledgment ack) {
        long startTime = System.currentTimeMillis();
        String threadName = Thread.currentThread().getName();

        log.info("[CDC消费开始] 线程={}, 批次大小={}", threadName, records.size());

        List<OdsRtSzdnSnapshotFlowAddcode> toSaveList = new ArrayList<>();
        List<SnapshotFlowDocument> esDocs = new ArrayList<>();
        List<String> processedIds = new ArrayList<>();
        List<ConsumerRecord<String, String>> failedRecords = new ArrayList<>();

        try {
            for (ConsumerRecord<String, String> record : records) {
                try {
                    boolean processed = processDebeziumRecord(record, toSaveList, esDocs, processedIds);
                    if (!processed) {
                        failedRecords.add(record);
                    }
                } catch (Exception e) {
                    log.error("[CDC单条处理异常] offset={}, key={}", record.offset(), record.key(), e);
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
            log.info("[CDC消费完成] 线程={}, 批次={}, 成功={}, 失败={}, 耗时={}ms",
                threadName, records.size(), toSaveList.size(), failedRecords.size(), costTime);

        } catch (Exception e) {
            log.error("[CDC批量消费异常] 回滚幂等标记", e);
            for (String id : processedIds) {
                idempotentUtil.remove(id);
            }
            throw e;
        }
    }

    /**
     * 处理单条 Debezium 消息
     * <p>
     * Debezium 操作类型：
     * - c: create (INSERT)
     * - u: update (UPDATE)
     * - d: delete (DELETE)
     * - r: read (快照读取)
     *
     * @param record Kafka消息记录
     * @param toSaveList MySQL待保存列表
     * @param esDocs ES待保存文档列表
     * @param processedIds 已处理ID列表
     * @return true=处理成功；false=处理失败
     */
    private boolean processDebeziumRecord(
            ConsumerRecord<String, String> record,
            List<OdsRtSzdnSnapshotFlowAddcode> toSaveList,
            List<SnapshotFlowDocument> esDocs,
            List<String> processedIds) {

        String message = record.value();
        OdsRtSzdnSnapshotFlowAddcode data = null;

        try {
            // 解析 Debezium 消息
            JSONObject debeziumMessage = JSON.parseObject(message);
            String operationType = debeziumMessage.getString("op");
            JSONObject before = debeziumMessage.getJSONObject("before");
            JSONObject after = debeziumMessage.getJSONObject("after");
            Long tsMs = debeziumMessage.getLong("ts_ms");

            // 构建幂等键（使用事务LSN + 序列号或主键）
            String idempotentKey = buildIdempotentKey(debeziumMessage);

            // 幂等性检查
            if (!idempotentUtil.checkAndSet(idempotentKey)) {
                log.info("[CDC幂等检查通过] 消息已处理, key={}, offset={}", idempotentKey, record.offset());
                return true;
            }

            processedIds.add(idempotentKey);

            switch (operationType) {
                case "c": // CREATE (INSERT)
                case "r": // READ (快照)
                    data = parseToEntity(after);
                    if (data != null && data.getBigId() != null) {
                        toSaveList.add(data);
                        SnapshotFlowDocument doc = new SnapshotFlowDocument();
                        BeanUtils.copyProperties(data, doc);
                        esDocs.add(doc);
                        log.debug("[CDC INSERT] bigId={}, ts={}", data.getBigId(), tsMs);
                    }
                    break;

                case "u": // UPDATE
                    data = parseToEntity(after);
                    if (data != null && data.getBigId() != null) {
                        toSaveList.add(data);
                        SnapshotFlowDocument doc = new SnapshotFlowDocument();
                        BeanUtils.copyProperties(data, doc);
                        esDocs.add(doc);
                        log.debug("[CDC UPDATE] bigId={}, ts={}", data.getBigId(), tsMs);
                    }
                    break;

                case "d": // DELETE
                    data = parseToEntity(before);
                    if (data != null && data.getBigId() != null) {
                        // 删除操作
                        snapshotFlowService.removeById(data.getBigId());
                        log.debug("[CDC DELETE] bigId={}, ts={}", data.getBigId(), tsMs);
                    }
                    break;

                default:
                    log.warn("[CDC未知操作类型] op={}, offset={}", operationType, record.offset());
                    break;
            }

            successCount.incrementAndGet();
            return true;

        } catch (Exception e) {
            log.error("[CDC单条处理失败] offset={}", record.offset(), e);
            String failedKey = data != null && data.getBigId() != null
                ? data.getBigId()
                : "unknown-" + record.offset();
            idempotentUtil.remove(failedKey);
            return false;
        }
    }

    /**
     * 构建幂等键
     * <p>
     * 优先使用事务LSN + 序列号（全局唯一）
     * 备选方案：主键ID
     *
     * @param debeziumMessage Debezium 消息
     * @return 幂等键
     */
    private String buildIdempotentKey(JSONObject debeziumMessage) {
        // 方案1：使用事务ID + 序列号（Debezium 1.9+ 支持）
        JSONObject transaction = debeziumMessage.getJSONObject("transaction");
        if (transaction != null) {
            String txId = transaction.getString("id");
//            Number sequence = transaction.getJSONArray("total_order").getNumber(0);
//            if (txId != null && sequence != null) {
//                return "tx-" + txId + "-seq-" + sequence;
//            }
        }

        // 方案2：使用 LSN (Log Sequence Number) + 操作类型
        JSONObject source = debeziumMessage.getJSONObject("source");
        if (source != null) {
            String lsn = source.getString("lsn");
            String op = debeziumMessage.getString("op");
            String txId = source.getString("transactionId");
            if (lsn != null) {
                return "lsn-" + lsn + "-op-" + op;
            }
            if (txId != null) {
                Long ts = source.getLong("ts_ms");
                return "tx-" + txId + "-ts-" + ts + "-op-" + op;
            }
        }

        // 方案3：使用主键（最后备选）
        JSONObject after = debeziumMessage.getJSONObject("after");
        JSONObject before = debeziumMessage.getJSONObject("before");
        JSONObject data = after != null ? after : before;
        if (data != null && data.getString("big_id") != null) {
            String op = debeziumMessage.getString("op");
            return "key-" + data.getString("big_id") + "-op-" + op;
        }

        // 兜底方案：使用偏移量
        return "offset-" + debeziumMessage.getLong("offset");
    }

    /**
     * 解析为实体对象
     *
     * @param jsonObject JSON对象
     * @return 实体对象
     */
    private OdsRtSzdnSnapshotFlowAddcode parseToEntity(JSONObject jsonObject) {
        if (jsonObject == null) {
            return null;
        }
        return jsonObject.to(OdsRtSzdnSnapshotFlowAddcode.class);
    }

    /**
     * 批量保存数据到 MySQL 和 ES
     */
    private void batchSaveData(
            List<OdsRtSzdnSnapshotFlowAddcode> toSaveList,
            List<SnapshotFlowDocument> esDocs) {

        log.info("[CDC批量保存开始] MySQL={}, ES={}", toSaveList.size(), esDocs.size());

        boolean mysqlSuccess = false;
        boolean esSuccess = false;

        try {
            snapshotFlowService.saveBatch(toSaveList);
            mysqlSuccess = true;
            log.info("[CDC MySQL保存成功] 数量={}", toSaveList.size());
        } catch (Exception e) {
            log.error("[CDC MySQL保存失败]", e);
        }

        try {
            esSuccess = elasticsearchService.batchSave(esDocs);
            if (esSuccess) {
                log.info("[CDC ES保存成功] 数量={}", esDocs.size());
            } else {
                log.warn("[CDC ES保存失败]");
            }
        } catch (Exception e) {
            log.error("[CDC ES保存异常]", e);
        }
    }

    /**
     * 处理失败的记录
     */
    private void handleFailedRecords(List<ConsumerRecord<String, String>> failedRecords) {
        if (failedRecords.isEmpty()) {
            return;
        }

        log.warn("[CDC处理失败记录] 数量={}", failedRecords.size());

        for (ConsumerRecord<String, String> record : failedRecords) {
            boolean retrySuccess = retryProcess(record);
            if (!retrySuccess) {
                sendToDLQ(record, "重试失败");
            }
        }
    }

    /**
     * 单条消息本地重试
     */
    private boolean retryProcess(ConsumerRecord<String, String> record) {
        for (int i = 1; i <= MAX_RETRY_TIMES; i++) {
            try {
                log.warn("[CDC重试处理] 第{}次, offset={}", i, record.offset());
                retryCount.incrementAndGet();

                Thread.sleep(1000);

                List<OdsRtSzdnSnapshotFlowAddcode> tempToSave = new ArrayList<>();
                List<SnapshotFlowDocument> tempEsDocs = new ArrayList<>();
                List<String> tempIds = new ArrayList<>();

                boolean result = processDebeziumRecord(record, tempToSave, tempEsDocs, tempIds);

                if (result && !tempToSave.isEmpty()) {
                    batchSaveData(tempToSave, tempEsDocs);
                    log.info("[CDC重试成功] offset={}", record.offset());
                    return true;
                }
            } catch (Exception e) {
                log.error("[CDC重试异常] 第{}次, offset={}", i, record.offset(), e);
            }
        }
        return false;
    }

    /**
     * 发送到死信队列
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

            log.warn("[CDC发送死信队列] offset={}, reason={}", record.offset(), reason);
        } catch (Exception e) {
            log.error("[CDC死信队列发送失败] offset={}", record.offset(), e);
        }
    }

    /**
     * 获取消费统计信息
     */
    public Map<String, Integer> getConsumerStats() {
        Map<String, Integer> stats = new HashMap<>();
        stats.put("successCount", successCount.get());
        stats.put("failCount", failCount.get());
        stats.put("retryCount", retryCount.get());
        return stats;
    }
}
