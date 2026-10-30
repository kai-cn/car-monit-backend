package com.ruoyi.base.service.cdc;

import com.alibaba.fastjson2.JSON;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 死信队列服务
 * 用于处理CDC同步失败的消息，支持重试和死信存储
 */
@Slf4j
@Service
public class DeadLetterQueueService {

    private static final String DLQ_KEY_PREFIX = "cdc:dlq:";
    private static final String DLQ_RETRY_KEY_PREFIX = "cdc:retry:";
    private static final String DLQ_DLQ_KEY_PREFIX = "cdc:dead:";

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    /**
     * 将消息加入重试队列
     *
     * @param message      CDC消息
     * @param delaySeconds 延迟秒数
     */
    public void addToRetryQueue(CdcMessage message, long delaySeconds) {
        String key = DLQ_RETRY_KEY_PREFIX + message.getMessageId();
        String value = JSON.toJSONString(message);

        redisTemplate.opsForValue().set(key, value, Duration.ofSeconds(delaySeconds));
        log.info("【死信队列】消息 {} 已加入重试队列，延迟 {} 秒", message.getMessageId(), delaySeconds);
    }

    /**
     * 将消息加入死信队列（重试多次失败后）
     *
     * @param message CDC消息
     */
    public void addToDeadLetterQueue(CdcMessage message) {
        String key = DLQ_DLQ_KEY_PREFIX + message.getMessageId();
        String value = JSON.toJSONString(message);

        redisTemplate.opsForValue().set(key, value, Duration.ofDays(7));
        log.error("【死信队列】消息 {} 已加入死信队列，重试次数: {}", message.getMessageId(), message.getRetryCount());
    }

    /**
     * 获取需要重试的消息
     *
     * @return 需要重试的消息列表
     */
    public List<CdcMessage> getRetryMessages() {
        Set<String> keys = redisTemplate.keys(DLQ_RETRY_KEY_PREFIX + "*");

        return keys.stream()
                .map(key -> {
                    String value = redisTemplate.opsForValue().get(key);
                    if (value != null) {
                        try {
                            return JSON.parseObject(value, CdcMessage.class);
                        } catch (Exception e) {
                            log.error("【死信队列】解析重试消息失败: {}", e.getMessage());
                            return null;
                        }
                    }
                    return null;
                })
                .filter(message -> message != null)
                .collect(Collectors.toList());
    }

    /**
     * 删除重试队列中的消息
     *
     * @param messageId 消息ID
     */
    public void removeFromRetryQueue(String messageId) {
        String key = DLQ_RETRY_KEY_PREFIX + messageId;
        redisTemplate.delete(key);
        log.debug("【死信队列】已从重试队列删除消息: {}", messageId);
    }

    /**
     * 获取死信队列中的消息
     *
     * @return 死信消息列表
     */
    public List<CdcMessage> getDeadLetterMessages() {
        Set<String> keys = redisTemplate.keys(DLQ_DLQ_KEY_PREFIX + "*");

        return keys.stream()
                .map(key -> {
                    String value = redisTemplate.opsForValue().get(key);
                    if (value != null) {
                        try {
                            return JSON.parseObject(value, CdcMessage.class);
                        } catch (Exception e) {
                            log.error("【死信队列】解析死信消息失败: {}", e.getMessage());
                            return null;
                        }
                    }
                    return null;
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    /**
     * 删除死信队列中的消息
     *
     * @param messageId 消息ID
     */
    public void removeFromDeadLetterQueue(String messageId) {
        String key = DLQ_DLQ_KEY_PREFIX + messageId;
        redisTemplate.delete(key);
        log.debug("【死信队列】已从死信队列删除消息: {}", messageId);
    }

    /**
     * 获取重试队列大小
     *
     * @return 队列大小
     */
    public long getRetryQueueSize() {
        Set<String> keys = redisTemplate.keys(DLQ_RETRY_KEY_PREFIX + "*");
        return keys != null ? keys.size() : 0;
    }

    /**
     * 获取死信队列大小
     *
     * @return 队列大小
     */
    public long getDeadLetterQueueSize() {
        Set<String> keys = redisTemplate.keys(DLQ_DLQ_KEY_PREFIX + "*");
        return keys != null ? keys.size() : 0;
    }
}
