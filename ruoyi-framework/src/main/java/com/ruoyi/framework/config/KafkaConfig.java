package com.ruoyi.framework.config;

import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.annotation.EnableKafka;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.*;
import org.springframework.kafka.listener.ContainerProperties;

import java.util.HashMap;
import java.util.Map;

/**
 * Kafka配置类（生产级优化版）
 * <p>
 * 针对300G历史数据 + 每日50W新增的优化策略：
 * 1. 批量消费：max.poll.records=500，提高吞吐量
 * 2. 手动确认：MANUAL_IMMEDIATE，确保消息不丢失
 * 3. 增大拉取间隔：max.poll.interval.ms=300000，避免消费者被踢出
 * 4. 并发消费：concurrency=3，提高消费速度
 * 5. 增大缓冲区：fetch.max.bytes=52428800，提高批量拉取效率
 * </p>
 *
 * @author ruoyi
 */
@Configuration
@EnableKafka
public class KafkaConfig {

    /** Kafka服务器地址，格式：host1:port1,host2:port2 */
    @Value("${kafka.bootstrap-servers}")
    private String bootstrapServers;

    /** 消费者组ID，同一组内的消费者共同消费消息 */
    @Value("${kafka.consumer.group-id:snapshot-flow-consumer-group}")
    private String groupId;

    /** 是否自动提交偏移量，false表示手动确认，确保消息处理成功才提交 */
    @Value("${kafka.consumer.enable-auto-commit:false}")
    private boolean enableAutoCommit;

    /** 无偏移量时的重置策略：earliest=从最早开始（消费历史数据），latest=从最新开始 */
    @Value("${kafka.consumer.auto-offset-reset:earliest}")
    private String autoOffsetReset;

    /**
     * 每次拉取的最大记录数
     * 优化思路：300G历史数据 + 每日50W新增，需要提高批量拉取大小
     * 建议值：500（平衡吞吐量和内存占用）
     */
    @Value("${kafka.consumer.max-poll-records:500}")
    private int maxPollRecords;

    /**
     * 最大拉取间隔（毫秒）
     * 优化思路：处理大量数据时需要更长的处理时间，避免消费者被认为挂掉而踢出组
     * 建议值：300000（5分钟）
     */
    @Value("${kafka.consumer.max-poll-interval-ms:300000}")
    private int maxPollIntervalMs;

    /**
     * 单次拉取最大字节数
     * 优化思路：增大单次拉取的数据量，减少网络请求
     * 建议值：52428800（50MB）
     */
    @Value("${kafka.consumer.fetch-max-bytes:52428800}")
    private int fetchMaxBytes;

    /**
     * 会话超时时间（毫秒）
     * 优化思路：增大会话超时，避免网络波动导致消费者被踢出
     * 建议值：60000（1分钟）
     */
    @Value("${kafka.consumer.session-timeout-ms:60000}")
    private int sessionTimeoutMs;

    /** 生产者确认模式：all=所有副本确认，确保数据不丢失 */
    @Value("${kafka.producer.acks:all}")
    private String acks;

    /** 发送失败重试次数 */
    @Value("${kafka.producer.retries:3}")
    private int retries;

    /**
     * 消费者并发数
     * 优化思路：与Kafka分区数一致（假设主题有3个分区）
     * 建议值：3（根据主题分区数调整）
     */
    @Value("${kafka.listener.concurrency:3}")
    private int concurrency;

    /**
     * 配置Kafka生产者工厂
     * <p>
     * 生产级优化：
     * - ENABLE_IDEMPOTENCE=true：启用幂等性，防止重复发送
     * - acks=all：等待所有副本确认，确保数据可靠性
     * - retries=3：发送失败重试3次
     * - 用于发送死信队列消息
     * </p>
     */
    @Bean
    public ProducerFactory<String, String> producerFactory() {
        Map<String, Object> configProps = new HashMap<>();
        configProps.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        configProps.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.StringSerializer.class);
        configProps.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.StringSerializer.class);
        configProps.put(ProducerConfig.ACKS_CONFIG, acks);
        configProps.put(ProducerConfig.RETRIES_CONFIG, retries);
        configProps.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        return new DefaultKafkaProducerFactory<>(configProps);
    }

    /**
     * 配置KafkaTemplate
     * <p>
     * 用途：Spring提供的Kafka操作模板，简化消息发送操作
     * 主要用于发送死信队列消息
     * </p>
     */
    @Bean
    public KafkaTemplate<String, String> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    /**
     * 配置Kafka消费者工厂
     * <p>
     * 生产级优化（针对300G历史数据）：
     * 1. enable.auto.commit=false：禁用自动提交，手动确认消息
     * 2. auto.offset.reset=earliest：新消费者从最早消息开始（消费历史数据）
     * 3. max.poll.records=500：批量拉取500条，提高吞吐量
     * 4. max.poll.interval.ms=300000：5分钟处理时间，避免消费者被踢出
     * 5. fetch.max.bytes=52428800：50MB拉取大小，减少网络请求
     * 6. session.timeout.ms=60000：1分钟会话超时，提高稳定性
     * </p>
     */
    @Bean
    public ConsumerFactory<String, String> consumerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, enableAutoCommit);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, autoOffsetReset);
        props.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, maxPollRecords);
        props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, maxPollIntervalMs);
        props.put(ConsumerConfig.FETCH_MAX_BYTES_CONFIG, fetchMaxBytes);
        props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, sessionTimeoutMs);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, org.apache.kafka.common.serialization.StringDeserializer.class);
        return new DefaultKafkaConsumerFactory<>(props);
    }

    /**
     * 配置Kafka监听器容器工厂
     * <p>
     * 生产级优化：
     * - MANUAL_IMMEDIATE：手动立即确认模式，处理完立即提交偏移量
     * - concurrency：并发消费者数量，与分区数一致（3），充分利用分区并行
     * - 批量消息监听，提高处理效率
     * </p>
     */
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, String> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, String> factory = new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());
        factory.setConcurrency(concurrency);
        factory.setBatchListener(true);
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        return factory;
    }
}
