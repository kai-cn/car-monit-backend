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
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

/**
 * 门架抓拍流水Kafka消费者
 * <p>
 * 用途：监听Kafka主题，消费门架流水变更消息，同步到MySQL分表和Elasticsearch
 * 核心流程：
 * 1. 从Kafka拉取批量消息
 * 2. 幂等性检查，防止重复处理
 * 3. 根据操作类型（INSERT/UPDATE/DELETE）处理数据
 * 4. 批量写入MySQL和ES
 * 5. 手动确认消息，确保数据一致性
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Component
public class SnapshotFlowKafkaConsumer {

    /** 幂等性工具，防止重复消费 */
    @Autowired
    private IdempotentUtil idempotentUtil;

    /** MySQL门架流水Service */
    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowService;

    /** Elasticsearch门架流水服务 */
    @Autowired
    private SnapshotFlowElasticsearchService elasticsearchService;

    @Value("${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}")
    private String snapshotFlowTopic;

    /**
     * 消费Kafka消息
     * <p>
     * 监听主题：snapshot-flow-topic
     * 消息格式：
     * {
     *   "operationType": "INSERT",  // 操作类型：INSERT/UPDATE/DELETE
     *   "data": { ... }             // 门架流水数据
     * }
     *
     * 可靠性保障：
     * 1. 幂等性：基于Redis防止重复处理
     * 2. 手动确认：处理成功后才提交偏移量
     * 3. 异常回滚：批量失败时清理幂等性标记，允许重试
     *
     * @param records Kafka消息记录列表
     * @param ack 确认对象，用于手动提交偏移量
     */
//    @KafkaListener(topics = "${kafka.topic.snapshot-flow:ods-rt-szdn-snapshot-flow}", containerFactory = "kafkaListenerContainerFactory")
    public void consume(List<ConsumerRecord<String, String>> records, Acknowledgment ack) {
        List<OdsRtSzdnSnapshotFlowAddcode> toSaveList = new ArrayList<>();
        List<SnapshotFlowDocument> esDocs = new ArrayList<>();
        List<String> processedIds = new ArrayList<>();

        try {
            for (ConsumerRecord<String, String> record : records) {
                String message = record.value();
                log.info("接收到Kafka消息: {}", message);
                OdsRtSzdnSnapshotFlowAddcode data = null;

                try {
                    JSONObject jsonObject = JSON.parseObject(message);
                    String operationType = jsonObject.getString("operationType");
                    data = jsonObject.getObject("data", OdsRtSzdnSnapshotFlowAddcode.class);

                    if (data == null || data.getBigId() == null) {
                        log.warn("消息数据为空或缺少bigId: {}", message);
                        continue;
                    }

                    String idempotentKey = data.getBigId();
                    if (!idempotentUtil.checkAndSet(idempotentKey)) {
                        log.info("消息已处理，跳过: {}", idempotentKey);
                        continue;
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

                } catch (Exception e) {
                    log.error("处理单条消息失败: {}", message, e);
                    if (data != null && data.getBigId() != null) {
                        idempotentUtil.remove(data.getBigId());
                    }
                }
            }

            if (!toSaveList.isEmpty()) {
                snapshotFlowService.saveBatch(toSaveList);
            }

            if (!esDocs.isEmpty()) {
                elasticsearchService.batchSave(esDocs);
            }

            ack.acknowledge();
            log.info("成功处理{}条消息", records.size());

        } catch (Exception e) {
            log.error("批量处理Kafka消息失败", e);
            for (String id : processedIds) {
                idempotentUtil.remove(id);
            }
            throw e;
        }
    }
}
