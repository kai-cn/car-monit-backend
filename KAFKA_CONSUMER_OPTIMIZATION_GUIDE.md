# Kafka 消费者生产级优化指南

## 📊 问题背景

| 场景 | 数据规模 |
|------|----------|
| 历史数据 | 300G |
| 每日新增 | 50W+ 条 |
| 主题 | ods-rt-szdn-snapshot-flow |
| 表 | OdsRtSzdnSnapshotFlowAddcode |

---

## 🎯 核心问题与解决方案

| 问题 | 解决方案 | 实现位置 |
|------|----------|----------|
| 消息积压 | 批量消费 + 并发消费 + 增大缓冲区 | KafkaConfig, SnapshotFlowKafkaConsumerV2 |
| 重复消费 | Redis 幂等检查 + 手动确认 | IdempotentUtil, SnapshotFlowKafkaConsumerV2 |
| 消息丢失 | MANUAL_IMMEDIATE + 失败重试 + 死信队列 | KafkaConfig, SnapshotFlowKafkaConsumerV2 |
| 消费者被踢出 | max.poll.interval.ms=300000 | KafkaConfig |
| 处理失败 | 本地重试3次 + 死信队列兜底 | SnapshotFlowKafkaConsumerV2 |

---

## 📁 新增文件清单

| 文件 | 说明 |
|------|------|
| `SnapshotFlowKafkaConsumerV2.java` | 生产级消费者（替代旧版本） |
| `KafkaConfig.java` (已更新) | 生产级配置优化 |
| `application.yml` (已更新) | 新增主题和优化配置 |
| 本文档 | 优化说明文档 |

---

## 🔧 优化详解

---

### 1. 解决消息积压问题

#### 优化策略 1.1：批量拉取
```java
// KafkaConfig.java
max.poll.records=500  // 每次拉取500条
fetch.max.bytes=52428800  // 单次拉取50MB
```
**思路注释：**
- 从原来的100条提升到500条，减少网络往返
- 50MB缓冲区，充分利用网络带宽
- 平衡内存占用和吞吐量

---

#### 优化策略 1.2：并发消费
```java
// KafkaConfig.java
concurrency=3  // 3个并发消费者
```
**思路注释：**
- 假设Kafka主题有3个分区
- 1个消费者处理1个分区，充分利用并行
- 与分区数一致，避免分区重平衡问题

---

#### 优化策略 1.3：延长拉取间隔
```java
// KafkaConfig.java
max.poll.interval.ms=300000  // 5分钟
```
**思路注释：**
- 处理大量数据需要更长时间
- 避免消费者被认为挂掉而踢出组
- 给批量处理充足时间

---

### 2. 防止重复消费

#### 策略 2.1：Redis 幂等检查
```java
// IdempotentUtil.checkAndSet()
// 思路：
// 1. 用 Redis 的 SETNX 命令（原子操作）
// 2. key = snapshot:flow:idempotent:{bigId}
// 3. 设置成功 = 消息未处理，继续处理
// 4. 设置失败 = 消息已处理，直接跳过
// 5. 24小时过期，避免内存无限增长
```

**思路注释：**
- 利用 Redis 单线程特性保证原子性
- bigId 作为唯一键，业务层面保证唯一
- 异常时回滚幂等标记，允许重试

---

#### 策略 2.2：手动确认 + 批量保存
```java
// SnapshotFlowKafkaConsumerV2.consumeBatch()
// 思路：
// 1. 先收集所有成功的消息
// 2. 批量保存 MySQL 和 ES（减少IO）
// 3. 全部处理成功后才 ack
// 4. 异常时全部不 ack，回滚幂等标记
```

---

### 3. 防止消息丢失

#### 策略 3.1：MANUAL_IMMEDIATE 确认模式
```java
// KafkaConfig.java
factory.getContainerProperties().setAckMode(MANUAL_IMMEDIATE);
```
**思路注释：**
- 禁用自动提交，完全手动控制
- 处理完成立即提交，不等待
- 异常不提交，消息保留在 Kafka 可重试

---

#### 策略 3.2：本地重试 3 次
```java
// SnapshotFlowKafkaConsumerV2.retryProcess()
// 思路：
// 1. 单条消息处理失败先本地重试
// 2. 最多重试3次，每次间隔1秒
// 3. 重试成功直接 ack
// 4. 重试失败发送到死信队列
```

---

#### 策略 3.3：死信队列（DLQ）兜底
```java
// SnapshotFlowKafkaConsumerV2.sendToDLQ()
// 思路：
// 1. 重试仍然失败，不阻塞消费进度
// 2. 发送到死信主题：ods-rt-szdn-snapshot-flow-dlq
// 3. 保留原始消息、偏移量、失败原因
// 4. 后续人工介入分析和处理
```

**死信队列消息格式：**
```json
{
  "originalTopic": "ods-rt-szdn-snapshot-flow",
  "partition": 0,
  "offset": 12345,
  "timestamp": 1716700000000,
  "reason": "重试失败",
  "value": "原始消息内容..."
}
```

---

### 4. 批量处理优化

#### 策略 4.1：MySQL 批量插入
```java
// SnapshotFlowKafkaConsumerV2.batchSaveData()
// 思路：
// 1. 先收集到 List 中
// 2. 一次性 saveBatch 插入 MySQL
// 3. 减少数据库连接开销
// 4. 配合数据库批量参数，性能提升显著
```

---

#### 策略 4.2：ES 批量索引
```java
// SnapshotFlowElasticsearchService.batchSave()
// 思路：
// 1. 使用 Bulk API
// 2. 一次请求提交多个文档
// 3. 减少网络请求次数
```

---

## 📋 配置详解

### application.yml 新增配置
```yaml
kafka:
  topic:
    # 源主题：门架流水
    snapshot-flow: ods-rt-szdn-snapshot-flow
    # 死信主题：处理失败的消息
    snapshot-flow-dlq: ods-rt-szdn-snapshot-flow-dlq
  
  consumer:
    # 批量拉取大小：500条
    max-poll-records: 500
    # 最大拉取间隔：5分钟
    max-poll-interval-ms: 300000
    # 单次拉取最大字节：50MB
    fetch-max-bytes: 52428800
    # 会话超时：1分钟
    session-timeout-ms: 60000
```

---

## 🔍 监控与运维

### 1. 消费进度监控
```bash
# 查看消费者组 lag
kafka-consumer-groups.bat --bootstrap-server localhost:9092 \
  --group snapshot-flow-consumer-group --describe
```

### 2. 死信队列监控
```bash
# 查看死信队列消息
kafka-console-consumer.bat --bootstrap-server localhost:9092 \
  --topic ods-rt-szdn-snapshot-flow-dlq --from-beginning
```

### 3. 应用监控指标
`SnapshotFlowKafkaConsumerV2.getConsumerStats()` 返回：
```json
{
  "successCount": 100000,
  "failCount": 5,
  "retryCount": 15
}
```

---

## ⚠️ 注意事项

### 1. Kafka 主题分区数
- 当前配置 concurrency=3，建议主题分区数 ≥ 3
- 如果分区数 < 3，调整 concurrency 与分区数一致
- 分区数过多会增加管理开销

### 2. Redis 内存
- 幂等键保留24小时
- 每日50W条，50W * 100字节 ≈ 50MB/天
- 确保 Redis 有足够内存

### 3. 历史数据消费
- auto.offset.reset=earliest，新消费者从最早开始
- 生产环境首次启动可能需要消费大量历史数据
- 监控 lag 指标，确保消费进度正常

### 4. 死信队列处理
- 定期检查死信队列
- 分析失败原因
- 修复后手动重新投递

---

## 🔄 新旧消费者切换

### 旧消费者
- 文件：`SnapshotFlowKafkaConsumer.java`
- 状态：保留作为参考

### 新消费者（推荐使用）
- 文件：`SnapshotFlowKafkaConsumerV2.java`
- 状态：生产级优化版

**切换方法：**
1. 确认新消费者编译通过
2. 注释掉旧消费者的 @KafkaListener
3. 启动应用测试新消费者
4. 监控日志和 lag 指标

---

## 📈 性能预期

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 消费速度 | ~100条/秒 | ~1000-2000条/秒 |
| 批量大小 | 100条 | 500条 |
| 并发度 | 1 | 3 |
| 消息丢失风险 | 中 | 低（死信兜底） |
| 重复消费风险 | 中 | 低（Redis幂等） |

---

## 📞 故障排查

### 问题1：消费 lag 持续增长
**排查步骤：**
1. 检查消费者是否正常运行
2. 查看应用日志是否有异常
3. 检查 MySQL 和 ES 是否响应慢
4. 适当增加 concurrency（但不超过分区数）

### 问题2：重复消费
**排查步骤：**
1. 检查 Redis 是否正常
2. 检查幂等键是否正确设置
3. 查看是否有异常导致 ack 失败

### 问题3：消息进入死信队列
**排查步骤：**
1. 查看死信队列消息的 reason 字段
2. 检查 MySQL/ES 连接
3. 检查数据格式是否正确
4. 修复后手动重新投递
