package com.ruoyi.base.service.cdc;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * CDC消息封装类
 * 用于封装从Kafka消费的CDC变更消息
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CdcMessage {

    /**
     * 操作类型
     */
    private OperationType operationType;

    /**
     * 数据源名称
     */
    private String sourceName;

    /**
     * 数据库名称
     */
    private String database;

    /**
     * 表名称
     */
    private String table;

    /**
     * 变更前的数据（DELETE或UPDATE操作）
     */
    private OdsRtSzdnSnapshotFlowAddcode beforeData;

    /**
     * 变更后的数据（INSERT或UPDATE操作）
     */
    private OdsRtSzdnSnapshotFlowAddcode afterData;

    /**
     * 变更时间
     */
    private LocalDateTime timestamp;

    /**
     * 消息唯一标识
     */
    private String messageId;

    /**
     * 重试次数
     */
    private int retryCount;

    /**
     * 操作类型枚举
     */
    public enum OperationType {
        /**
         * 插入
         */
        INSERT,

        /**
         * 更新
         */
        UPDATE,

        /**
         * 删除
         */
        DELETE
    }
}
