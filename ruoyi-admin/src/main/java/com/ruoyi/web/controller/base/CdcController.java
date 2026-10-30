package com.ruoyi.web.controller.base;

import com.ruoyi.base.service.cdc.CdcConfig;
import com.ruoyi.base.service.cdc.CdcMessage;
import com.ruoyi.base.service.cdc.CdcSyncService;
import com.ruoyi.base.service.cdc.DeadLetterQueueService;
import com.ruoyi.common.core.domain.AjaxResult;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * CDC同步管理Controller
 * 提供CDC队列管理、手动重试等功能
 */
@RestController
@RequestMapping("/base/cdc")
public class CdcController {

    @Autowired
    private DeadLetterQueueService deadLetterQueueService;

    @Autowired
    private CdcSyncService cdcSyncService;

    @Autowired
    private CdcConfig cdcConfig;

    /**
     * 获取CDC队列状态
     *
     * @return 队列状态信息
     */
    @GetMapping("/status")
    public AjaxResult getQueueStatus() {
        Map<String, Object> status = new HashMap<>();
        
        status.put("retryQueueSize", deadLetterQueueService.getRetryQueueSize());
        status.put("deadLetterQueueSize", deadLetterQueueService.getDeadLetterQueueSize());
        status.put("kafkaTopic", cdcConfig.getKafka().getTopic());
        status.put("consumerGroupId", cdcConfig.getKafka().getConsumerGroupId());
        status.put("maxRetryAttempts", cdcConfig.getRetry().getMaxAttempts());

        return AjaxResult.success(status);
    }

    /**
     * 获取死信队列消息列表
     *
     * @return 死信消息列表
     */
    @GetMapping("/dead-letters")
    public AjaxResult getDeadLetterMessages() {
        List<CdcMessage> messages = deadLetterQueueService.getDeadLetterMessages();
        return AjaxResult.success(messages);
    }

    /**
     * 获取重试队列消息列表
     *
     * @return 重试消息列表
     */
    @GetMapping("/retry-messages")
    public AjaxResult getRetryMessages() {
        List<CdcMessage> messages = deadLetterQueueService.getRetryMessages();
        return AjaxResult.success(messages);
    }

    /**
     * 手动重试指定死信消息
     *
     * @param messageId 消息ID
     * @return 操作结果
     */
    @PostMapping("/retry/{messageId}")
    public AjaxResult retryMessage(@PathVariable String messageId) {
        boolean success = cdcSyncService.retryMessage(messageId);
        
        if (success) {
            return AjaxResult.success("重试成功");
        } else {
            return AjaxResult.error("重试失败，消息不存在或处理失败");
        }
    }

    /**
     * 批量重试所有死信消息
     *
     * @return 操作结果
     */
    @PostMapping("/retry-all")
    public AjaxResult retryAllDeadMessages() {
        int successCount = cdcSyncService.retryAllDeadMessages();
        return AjaxResult.success("批量重试完成，成功 " + successCount + " 条");
    }

    /**
     * 删除指定死信消息
     *
     * @param messageId 消息ID
     * @return 操作结果
     */
    @DeleteMapping("/dead-letters/{messageId}")
    public AjaxResult deleteDeadLetterMessage(@PathVariable String messageId) {
        deadLetterQueueService.removeFromDeadLetterQueue(messageId);
        return AjaxResult.success("删除成功");
    }

    /**
     * 清空死信队列
     *
     * @return 操作结果
     */
    @DeleteMapping("/dead-letters/clear")
    public AjaxResult clearDeadLetterQueue() {
        List<CdcMessage> messages = deadLetterQueueService.getDeadLetterMessages();
        messages.forEach(message -> 
            deadLetterQueueService.removeFromDeadLetterQueue(message.getMessageId())
        );
        return AjaxResult.success("已清空死信队列");
    }

    /**
     * 获取CDC配置信息
     *
     * @return 配置信息
     */
    @GetMapping("/config")
    public AjaxResult getConfig() {
        return AjaxResult.success(cdcConfig);
    }
}
