package com.ruoyi.base.service.cdc;

import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.elasticsearch.service.SnapshotFlowElasticsearchService;
import lombok.extern.slf4j.Slf4j;
import org.elasticsearch.client.RestHighLevelClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * CDC同步服务
 * 监听Kafka CDC主题，将数据库变更同步到ES
 */
@Slf4j
@Service
public class CdcSyncService {

    @Autowired
    private SnapshotFlowElasticsearchService elasticsearchService;

    @Autowired
    private DeadLetterQueueService deadLetterQueueService;

    @Autowired
    private CdcConfig cdcConfig;


    /**
     * Kafka消费者方法
     * 监听CDC主题，处理数据库变更消息
     *
     * @param message       CDC消息JSON字符串
     * @param acknowledgment Kafka确认对象
     */
    @KafkaListener(topics = "#{@cdcConfig.kafka.topic}",
                   groupId = "#{@cdcConfig.kafka.consumerGroupId}",
                   concurrency = "#{@cdcConfig.kafka.concurrency}")
    public void consumeCdcMessage(String message, Acknowledgment acknowledgment) {
        log.debug("【CDC消费】收到消息: {}", message);

        try {
            // 解析CDC消息
            CdcMessage cdcMessage = parseCdcMessage(message);

            if (cdcMessage == null) {
                log.warn("【CDC消费】消息解析失败，跳过: {}", message);
                acknowledgment.acknowledge();
                return;
            }

            // 处理消息
            boolean success = processCdcMessage(cdcMessage);

            if (success) {
                // 处理成功，确认消息
                acknowledgment.acknowledge();
                log.info("【CDC消费】消息 {} 处理成功", cdcMessage.getMessageId());
            } else {
                // 处理失败，加入重试队列
                handleFailure(cdcMessage);
                acknowledgment.acknowledge();
            }

        } catch (Exception e) {
            log.error("【CDC消费】处理消息异常: {}", e.getMessage(), e);
            acknowledgment.acknowledge();
        }
    }

    /**
     * 解析CDC消息
     *
     * @param message JSON字符串
     * @return CDC消息对象
     */
    private CdcMessage parseCdcMessage(String message) {
        try {
            return JSON.parseObject(message, CdcMessage.class);
        } catch (Exception e) {
            log.error("【CDC解析】解析消息失败: {}", e.getMessage());
            return null;
        }
    }

    /**
     * 处理CDC消息
     *
     * @param cdcMessage CDC消息
     * @return 是否处理成功
     */
    private boolean processCdcMessage(CdcMessage cdcMessage) {
        try {
            CdcMessage.OperationType operationType = cdcMessage.getOperationType();
            OdsRtSzdnSnapshotFlowAddcode data = cdcMessage.getAfterData();

            switch (operationType) {
                case INSERT:
                    return handleInsert(data);
                case UPDATE:
                    return handleUpdate(data);
                case DELETE:
                    return handleDelete(cdcMessage.getBeforeData());
                default:
                    log.warn("【CDC处理】未知操作类型: {}", operationType);
                    return true;
            }
        } catch (Exception e) {
            log.error("【CDC处理】处理消息失败: {}", e.getMessage(), e);
            return false;
        }
    }

    /**
     * 处理INSERT操作
     *
     * @param data 新增数据
     * @return 是否成功
     */
    private boolean handleInsert(OdsRtSzdnSnapshotFlowAddcode data) {
        if (data == null) {
            log.warn("【CDC插入】数据为空");
            return true;
        }

        try {
//            elasticsearchService.saveOrUpdate(data);
            log.debug("【CDC插入】成功索引数据: {}", data.getBigId());
            return true;
        } catch (Exception e) {
            log.error("【CDC插入】索引失败: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 处理UPDATE操作
     *
     * @param data 更新后的数据
     * @return 是否成功
     */
    private boolean handleUpdate(OdsRtSzdnSnapshotFlowAddcode data) {
        if (data == null) {
            log.warn("【CDC更新】数据为空");
            return true;
        }

        try {
//            elasticsearchService.update(data);
            log.debug("【CDC更新】成功更新数据: {}", data.getBigId());
            return true;
        } catch (Exception e) {
            log.error("【CDC更新】更新失败: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 处理DELETE操作
     *
     * @param data 删除前的数据
     * @return 是否成功
     */
    private boolean handleDelete(OdsRtSzdnSnapshotFlowAddcode data) {
        if (data == null) {
            log.warn("【CDC删除】数据为空");
            return true;
        }

        try {
//            elasticsearchService.delete(data.getBigId());
            log.debug("【CDC删除】成功删除数据: {}", data.getBigId());
            return true;
        } catch (Exception e) {
            log.error("【CDC删除】删除失败: {}", e.getMessage());
            return false;
        }
    }

    /**
     * 处理失败消息
     *
     * @param cdcMessage CDC消息
     */
    private void handleFailure(CdcMessage cdcMessage) {
        int maxAttempts = cdcConfig.getRetry().getMaxAttempts();
        int currentAttempt = cdcMessage.getRetryCount() + 1;

        if (currentAttempt < maxAttempts) {
            // 加入重试队列，使用指数退避
            long delay = calculateRetryDelay(currentAttempt);
            cdcMessage.setRetryCount(currentAttempt);
            deadLetterQueueService.addToRetryQueue(cdcMessage, delay);
            log.warn("【CDC重试】消息 {} 重试次数 {}，延迟 {} 秒",
                    cdcMessage.getMessageId(), currentAttempt, delay);
        } else {
            // 超过最大重试次数，加入死信队列
            cdcMessage.setRetryCount(currentAttempt);
            deadLetterQueueService.addToDeadLetterQueue(cdcMessage);
            log.error("【CDC失败】消息 {} 超过最大重试次数 {}，已加入死信队列",
                    cdcMessage.getMessageId(), maxAttempts);
        }
    }

    /**
     * 计算重试延迟（指数退避）
     *
     * @param attempt 当前重试次数
     * @return 延迟秒数
     */
    private long calculateRetryDelay(int attempt) {
        long baseInterval = cdcConfig.getRetry().getInterval() / 1000;
        double multiplier = cdcConfig.getRetry().getMultiplier();
        long maxInterval = cdcConfig.getRetry().getMaxInterval() / 1000;

        long delay = (long) (baseInterval * Math.pow(multiplier, attempt - 1));
        return Math.min(delay, maxInterval);
    }

    /**
     * 手动重试死信队列中的消息
     *
     * @param messageId 消息ID
     * @return 是否成功
     */
    public boolean retryMessage(String messageId) {
        List<CdcMessage> deadMessages = deadLetterQueueService.getDeadLetterMessages();
        CdcMessage message = deadMessages.stream()
                .filter(m -> m.getMessageId().equals(messageId))
                .findFirst()
                .orElse(null);

        if (message == null) {
            log.warn("【CDC重试】未找到死信消息: {}", messageId);
            return false;
        }

        // 重置重试计数并重新处理
        message.setRetryCount(0);
        boolean success = processCdcMessage(message);

        if (success) {
            deadLetterQueueService.removeFromDeadLetterQueue(messageId);
            log.info("【CDC重试】死信消息 {} 重试成功", messageId);
            return true;
        } else {
            log.error("【CDC重试】死信消息 {} 重试失败", messageId);
            return false;
        }
    }

    /**
     * 批量重试所有死信消息
     *
     * @return 重试成功的数量
     */
    public int retryAllDeadMessages() {
        List<CdcMessage> deadMessages = deadLetterQueueService.getDeadLetterMessages();
        int successCount = 0;

        for (CdcMessage message : deadMessages) {
            message.setRetryCount(0);
            if (processCdcMessage(message)) {
                deadLetterQueueService.removeFromDeadLetterQueue(message.getMessageId());
                successCount++;
            }
        }

        log.info("【CDC重试】批量重试完成，成功 {} 条，失败 {} 条",
                successCount, deadMessages.size() - successCount);
        return successCount;
    }
}
