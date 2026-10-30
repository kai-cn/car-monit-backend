package com.ruoyi.base.service.cdc;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * CDC配置类
 * 用于配置Kafka和ES同步相关参数
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "cdc")
public class CdcConfig {

    /**
     * Kafka配置
     */
    private KafkaConfig kafka = new KafkaConfig();

    /**
     * ES同步配置
     */
    private EsSyncConfig esSync = new EsSyncConfig();

    /**
     * 重试配置
     */
    private RetryConfig retry = new RetryConfig();

    @Data
    public static class KafkaConfig {
        /**
         * Bootstrap servers
         */
        private String bootstrapServers = "localhost:9092";

        /**
         * 消费者组ID
         */
        private String consumerGroupId = "snapshot-flow-cdc-group";

        /**
         * CDC主题名称
         */
        private String topic = "snapshot-flow-cdc";

        /**
         * 自动提交offset
         */
        private boolean autoCommit = true;

        /**
         * 自动提交间隔(ms)
         */
        private int autoCommitInterval = 1000;

        /**
         * 会话超时时间(ms)
         */
        private int sessionTimeout = 30000;

        /**
         * 并发消费者数量
         */
        private int concurrency = 3;
    }

    @Data
    public static class EsSyncConfig {
        /**
         * 是否启用ES同步
         */
        private boolean enabled = true;

        /**
         * 批量写入大小
         */
        private int batchSize = 500;

        /**
         * 批量写入间隔(ms)
         */
        private long batchInterval = 5000;

        /**
         * 异步写入线程数
         */
        private int asyncThreads = 2;
    }

    @Data
    public static class RetryConfig {
        /**
         * 最大重试次数
         */
        private int maxAttempts = 3;

        /**
         * 重试间隔(ms)
         */
        private long interval = 1000;

        /**
         * 重试间隔递增倍数
         */
        private double multiplier = 2.0;

        /**
         * 最大重试间隔(ms)
         */
        private long maxInterval = 30000;
    }
}
