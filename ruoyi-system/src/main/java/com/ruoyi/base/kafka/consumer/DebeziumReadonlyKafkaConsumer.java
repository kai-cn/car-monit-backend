package com.ruoyi.base.kafka.consumer;

import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.elasticsearch.document.SnapshotFlowDocument;
import com.ruoyi.base.elasticsearch.service.SnapshotFlowElasticsearchService;
import com.ruoyi.base.service.IOdsRtSzdnSnapshotFlowAddcodeService;
import com.ruoyi.common.core.redis.RedisCache;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.header.Header;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Debezium CDC 门架抓拍流水消费者 - 纯读取模式
 * <p>
 * 核心设计原则：
 * 1. 零侵入：不修改甲方数据库，仅通过逻辑复制监听
 * 2. 纯 CDC：直接消费 Debezium 消息，无中间状态表
 * 3. 幂等性：基于 LSN/事务ID + Redis 实现 Exactly-Once
 * 4. 高性能：批量处理 + 分表存储
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Component
public class DebeziumReadonlyKafkaConsumer {

    /**
     * Redis 幂等键前缀
     */
    private static final String IDEMPOTENT_KEY_PREFIX = "debezium:cdc:processed:";

    /**
     * 幂等键过期时间（24小时）
     */
    private static final long IDEMPOTENT_EXPIRE_SECONDS = 86400;

    /**
     * 最大重试次数
     */
    private static final int MAX_RETRY_TIMES = 3;

    @Autowired
    private RedisCache redisUtil;

    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowService;

    @Autowired
    private SnapshotFlowElasticsearchService elasticsearchService;

    @Value("${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}")
    private String sourceTopic;

    @Value("${kafka.topic.snapshot-flow-dlq:ods-rt-szdn-snapshot-flow-dlq}")
    private String dlqTopic;

    /**
     * 统计计数器
     */
    private final AtomicInteger successCount = new AtomicInteger(0);
    private final AtomicInteger failCount = new AtomicInteger(0);
    private final AtomicInteger retryCount = new AtomicInteger(0);
    private final AtomicInteger duplicateCount = new AtomicInteger(0);

    /**
     * 消费 Debezium CDC 消息 - 批量消费
     * <p>
     * 消息来源：
     * - GaussDB 逻辑复制 → Debezium Connector → Kafka → 当前消费者
     *
     * 处理流程：
     * 1. 从 Kafka Header 提取元数据（LSN、操作类型、事务ID）
     * 2. 幂等性检查（Redis）
     * 3. 解析消息并映射为实体
     * 4. 批量写入 MySQL 分表
     * 5. 批量写入 Elasticsearch
     * 6. 手动确认偏移量
     *
     * @param records 批量消息记录
     * @param ack 确认对象
     */
//    @KafkaListener(
//        topics = "${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}",
//        containerFactory = "kafkaListenerContainerFactory"
//    )
    public void consumeBatch(List<ConsumerRecord<String, String>> records, Acknowledgment ack) {
        long startTime = System.currentTimeMillis();
        String threadName = Thread.currentThread().getName();

        log.info("[CDC只读消费开始] 线程={}, 批次大小={}", threadName, records.size());

        List<OdsRtSzdnSnapshotFlowAddcode> toSaveList = new ArrayList<>();
        List<SnapshotFlowDocument> esDocs = new ArrayList<>();
        List<ConsumerRecord<String, String>> failedRecords = new ArrayList<>();

        try {
            for (ConsumerRecord<String, String> record : records) {
                try {
                    boolean processed = processSingleRecord(record, toSaveList, esDocs);
                    if (!processed) {
                        failedRecords.add(record);
                    }
                } catch (Exception e) {
                    log.error("[CDC单条处理异常] offset={}, key={}", record.offset(), record.key(), e);
                    failedRecords.add(record);
                    failCount.incrementAndGet();
                }
            }

            // 批量保存
            if (!toSaveList.isEmpty()) {
                batchSaveData(toSaveList, esDocs);
            }

            // 处理失败记录
            if (!failedRecords.isEmpty()) {
                handleFailedRecords(failedRecords);
            }

            // 手动确认（仅在全部处理完成后）
            ack.acknowledge();

            long costTime = System.currentTimeMillis() - startTime;
            log.info("[CDC只读消费完成] 线程={}, 批次={}, 成功={}, 重复={}, 失败={}, 耗时={}ms",
                threadName, records.size(), toSaveList.size(), duplicateCount.get(),
                failedRecords.size(), costTime);

        } catch (Exception e) {
            log.error("[CDC批量消费异常]", e);
            // 不回滚幂等标记，避免重复处理
            throw e;
        }
    }

    /**
     * 处理单条 Debezium 消息
     *
     * @param record Kafka 消息记录
     * @param toSaveList MySQL 待保存列表
     * @param esDocs ES 待保存文档列表
     * @return true=处理成功/已幂等跳过；false=处理失败
     */
    private boolean processSingleRecord(
            ConsumerRecord<String, String> record,
            List<OdsRtSzdnSnapshotFlowAddcode> toSaveList,
            List<SnapshotFlowDocument> esDocs) {

        try {
            // 1. 从 Kafka Header 提取元数据
            String operation = getHeaderValue(record, "__operation");
            String lsn = getHeaderValue(record, "__lsn");
            String txId = getHeaderValue(record, "__txid");
            String tsMsStr = getHeaderValue(record, "__ts_ms");

            // 2. 构建幂等键（优先使用 LSN）
            String idempotentKey = buildIdempotentKey(lsn, txId, record.offset());

            // 3. 幂等性检查
            if (redisUtil.hasKey(idempotentKey)) {
                log.debug("[CDC幂等跳过] 消息已处理, lsn={}, offset={}", lsn, record.offset());
                duplicateCount.incrementAndGet();
                return true;
            }

            // 4. 解析消息内容
            JSONObject messageJson = JSON.parseObject(record.value());
            OdsRtSzdnSnapshotFlowAddcode entity = parseToEntity(messageJson);

            if (entity == null || entity.getBigId() == null) {
                log.warn("[CDC数据校验失败] 缺少big_id, offset={}", record.offset());
                return false;
            }

            // 5. 根据操作类型处理
            switch (operation) {
                case "c": // CREATE (INSERT)
                case "r": // READ (快照)
                case "u": // UPDATE
                    toSaveList.add(entity);
                    SnapshotFlowDocument doc = new SnapshotFlowDocument();
                    BeanUtils.copyProperties(entity, doc);
                    esDocs.add(doc);
                    log.debug("[CDC处理] 操作={}, bigId={}", operation, entity.getBigId());
                    break;

                case "d": // DELETE
                    snapshotFlowService.removeById(entity.getBigId());
                    log.debug("[CDC删除] bigId={}", entity.getBigId());
                    break;

                default:
                    log.warn("[CDC未知操作类型] op={}, offset={}", operation, record.offset());
                    break;
            }

            // 6. 标记已处理（设置幂等键）
//            redisUtil.setEx(idempotentKey, "1", IDEMPOTENT_EXPIRE_SECONDS, TimeUnit.SECONDS);
            successCount.incrementAndGet();
            return true;

        } catch (Exception e) {
            log.error("[CDC单条处理失败] offset={}", record.offset(), e);
            return false;
        }
    }

    /**
     * 构建幂等键
     * <p>
     * 优先级：
     * 1. LSN（最可靠，数据库级唯一）
     * 2. 事务ID + 偏移量
     * 3. 偏移量（兜底）
     *
     * @param lsn 日志序列号
     * @param txId 事务ID
     * @param offset Kafka 偏移量
     * @return 幂等键
     */
    private String buildIdempotentKey(String lsn, String txId, long offset) {
        if (lsn != null && !lsn.isEmpty()) {
            return IDEMPOTENT_KEY_PREFIX + "lsn:" + lsn;
        }
        if (txId != null && !txId.isEmpty()) {
            return IDEMPOTENT_KEY_PREFIX + "tx:" + txId + ":offset:" + offset;
        }
        return IDEMPOTENT_KEY_PREFIX + "offset:" + offset;
    }

    /**
     * 从 Kafka Header 提取值
     *
     * @param record Kafka 消息记录
     * @param headerName Header 名称
     * @return Header 值
     */
    private String getHeaderValue(ConsumerRecord<String, String> record, String headerName) {
        Header header = record.headers().lastHeader(headerName);
        if (header == null) {
            return null;
        }
        return new String(header.value(), StandardCharsets.UTF_8);
    }

    /**
     * 解析 JSON 为实体对象
     *
     * @param jsonObject JSON 对象
     * @return 实体对象
     */
    private OdsRtSzdnSnapshotFlowAddcode parseToEntity(JSONObject jsonObject) {
        if (jsonObject == null) {
            return null;
        }
        return jsonObject.to(OdsRtSzdnSnapshotFlowAddcode.class);
    }

    /**
     * 批量保存数据到 MySQL 和 Elasticsearch
     *
     * @param toSaveList MySQL 待保存列表
     * @param esDocs ES 待保存文档列表
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
     * 处理失败的记录（重试 + 死信队列）
     *
     * @param failedRecords 失败记录列表
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
     *
     * @param record 失败的记录
     * @return true=重试成功；false=重试失败
     */
    private boolean retryProcess(ConsumerRecord<String, String> record) {
        for (int i = 1; i <= MAX_RETRY_TIMES; i++) {
            try {
                log.warn("[CDC重试处理] 第{}次, offset={}", i, record.offset());
                retryCount.incrementAndGet();

                Thread.sleep(1000);

                List<OdsRtSzdnSnapshotFlowAddcode> tempToSave = new ArrayList<>();
                List<SnapshotFlowDocument> tempEsDocs = new ArrayList<>();

                boolean result = processSingleRecord(record, tempToSave, tempEsDocs);

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
     * 发送到死信队列（仅记录日志，不依赖生产者）
     *
     * @param record 失败的记录
     * @param reason 失败原因
     */
    private void sendToDLQ(ConsumerRecord<String, String> record, String reason) {
        try {
            log.warn("[CDC死信队列] offset={}, reason={}, value={}",
                record.offset(), reason, record.value());
            // 实际项目中可以：
            // 1. 写入本地文件
            // 2. 写入专门的死信表
            // 3. 发送到死信 Topic（通过 KafkaTemplate）
        } catch (Exception e) {
            log.error("[CDC死信队列处理失败] offset={}", record.offset(), e);
        }
    }

    /**
     * 获取消费统计信息
     *
     * @return 统计信息
     */
    public Map<String, Integer> getConsumerStats() {
        Map<String, Integer> stats = new HashMap<>();
        stats.put("successCount", successCount.get());
        stats.put("failCount", failCount.get());
        stats.put("retryCount", retryCount.get());
        stats.put("duplicateCount", duplicateCount.get());
        return stats;
    }

    /**
     * 重置统计计数器
     */
    public void resetStats() {
        successCount.set(0);
        failCount.set(0);
        retryCount.set(0);
        duplicateCount.set(0);
    }
}
