# 门架抓拍流水查询性能优化方案

## 📋 方案概述

本方案针对门架抓拍流水查询性能问题进行优化，采用 **Kafka + Elasticsearch + MySQL 分表** 的架构，解决原有实时查询 GaussDB 300G 单表的性能瓶颈。

### 原有架构问题
- ❌ GaussDB 单表 300G+，日均 50W+ 新增数据
- ❌ 跨服务 HTTP 调用，延迟高
- ❌ 模糊查询性能差
- ❌ 无高可用保障

### 优化后架构
```
┌─────────────────┐
│  car-monit-api  │  (GaussDB 数据源)
│  (数据变更监听)  │
└────────┬────────┘
         │ Kafka 消息
         ▼
┌─────────────────────────────────────────┐
│         Kafka Topic                     │
│      snapshot-flow-topic                │
│  消息格式: {operationType, data}        │
└─────────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────┐
    │  car-monit-backend (消费者)    │
    │  ┌──────────────────────────┐  │
    │  │  幂等性检查 (Redis)      │  │
    │  └────────────┬─────────────┘  │
    │               │                  │
    │     ┌─────────┴─────────┐        │
    │     ▼                   ▼        │
    │  MySQL 分表      Elasticsearch   │
    │  (按月分表)          (索引查询)   │
    └────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────┐
         │   查询请求        │
         │  (ES 优先)        │
         │  (降级 MySQL)     │
         └──────────────────┘
```

## 🚀 核心特性

### 1. 高性能查询
- **Elasticsearch**：毫秒级模糊查询和范围查询
- **车牌号模糊查询**：wildcard 查询
- **时间范围查询**：range 查询
- **等值查询**：term 查询（路段/管理中心/门架编号）

### 2. 高可用性
- **查询降级**：ES 不可用时自动降级到 MySQL
- **最终兜底**：保留原 HTTP 调用
- **服务健康检测**：ES 可用性实时检测

### 3. 数据一致性
- **Kafka 手动确认**：处理成功才提交偏移量
- **Redis 幂等性**：防止重复消费
- **消息重试**：失败自动重试
- **批量处理**：提高吞吐

### 4. 可扩展性
- **MySQL 按月分表**：避免单表过大
- **Kafka 分区**：支持并发消费
- **ES 索引**：可水平扩展

---

## 📁 新增/修改文件清单

### 配置类
| 文件 | 说明 |
|------|------|
| `ruoyi-framework/config/KafkaConfig.java` | Kafka 生产者/消费者配置 |
| `ruoyi-framework/config/ElasticsearchConfig.java` | ES 客户端配置 |
| `pom.xml` (根目录 + ruoyi-admin) | 添加 Kafka、ES 依赖 |
| `application.yml` | 添加 Kafka、ES 配置项 |

### 核心服务
| 文件 | 说明 |
|------|------|
| `ruoyi-common/utils/IdempotentUtil.java` | 幂等性工具类 |
| `ruoyi-common/core/redis/RedisCache.java` | 新增 setCacheObjectIfAbsent 方法 |
| `ruoyi-system/kafka/consumer/SnapshotFlowKafkaConsumer.java` | Kafka 消费者 |
| `ruoyi-system/elasticsearch/document/SnapshotFlowDocument.java` | ES 文档实体 |
| `ruoyi-system/elasticsearch/service/SnapshotFlowElasticsearchService.java` | ES 服务 |
| `ruoyi-system/sharding/ShardingTableUtil.java` | MySQL 分表工具 |
| `ruoyi-system/service/enhanced/SnapshotFlowEnhancedService.java` | 增强查询服务（ES 优先） |

### Controller 修改
| 文件 | 说明 |
|------|------|
| `OdsRtSzdnSnapshotFlowAddcodeController.java` | list/export 使用增强查询服务 |

### 文档
| 文件 | 说明 |
|------|------|
| `KAFKA_ES_INSTALL_GUIDE.md` | Kafka/ES 详细安装指南 |
| `download-packages.ps1` | 自动下载脚本 |
| `SNAPSHOT_FLOW_OPTIMIZATION_README.md` | 本文档 |

---

## 🛠️ 快速开始

### 1. 环境准备

#### 方式一：自动下载（推荐）
```powershell
# 在 PowerShell 中执行
cd d:\work\IdeaProjects\car-monit-backend-new
.\download-packages.ps1
```

#### 方式二：手动下载
参考 `KAFKA_ES_INSTALL_GUIDE.md` 手动下载。

### 2. 安装与配置

详细步骤参考：[KAFKA_ES_INSTALL_GUIDE.md](./KAFKA_ES_INSTALL_GUIDE.md)

快速步骤：
```
1. 解压到 D:\work\
   - zookeeper → D:\work\zookeeper
   - kafka → D:\work\kafka
   - elasticsearch → D:\work\elasticsearch

2. 配置各服务（参考安装指南）

3. 按顺序启动：
   ZooKeeper → Kafka → Elasticsearch
```

### 3. 应用配置

检查 `application.yml` 中的配置（默认已配置本地地址）：
```yaml
kafka:
  bootstrap-servers: 127.0.0.1:9092

elasticsearch:
  host: 127.0.0.1
  port: 9200
```

### 4. 启动应用

1. 确保 Redis 已启动
2. 启动 car-monit-backend
3. 观察日志，确认 Kafka 消费者和 ES 连接正常

---

## 📨 Kafka 消息格式

car-monit-api 需要发送如下格式的消息到 `snapshot-flow-topic`：

```json
{
  "operationType": "INSERT",
  "data": {
    "bigId": "唯一ID",
    "platenumber": "京A12345",
    "snapshottime": "2025-08-29 12:34:56",
    "sectioncode": "路段编号",
    "orgcode": "管理中心编号",
    "gantrycode": "门架编号",
    ...
  }
}
```

**operationType 取值**：
- `INSERT`：新增
- `UPDATE`：更新
- `DELETE`：删除

---

## 🔍 查询策略

### 查询流程
```
查询请求
    ↓
检测 ES 是否可用?
    ├─ 是 → 尝试 ES 查询
    │         ├─ 成功 → 返回结果 ✓
    │         └─ 失败 → 降级到 MySQL
    │
    └─ 否 → 降级到 MySQL
              ├─ 成功 → 返回结果 ✓
              └─ 失败 → 降级到原 HTTP 调用 (Controller)
```

### 支持的查询条件
| 字段 | 查询类型 | ES 实现 |
|------|----------|---------|
| platenumber | 全模糊 | wildcardQuery |
| snapshottime | 范围 | rangeQuery (gte/lte) |
| sectioncode | 等值 | termQuery |
| orgcode | 等值 | termQuery |
| gantrycode | 等值 | termQuery |

---

## 🗄️ MySQL 分表策略

### 分表规则
- **分表字段**：`snapshottime`（抓拍时间）
- **分表类型**：按月分表
- **表名格式**：`ods_rt_szdn_snapshot_flow_yyyyMM`
- **示例**：2025年8月 → `ods_rt_szdn_snapshot_flow_202508`

### 创建分表 SQL
```sql
-- 以 2025年8月 为例
CREATE TABLE ods_rt_szdn_snapshot_flow_202508 
LIKE ods_rt_szdn_snapshot_flow_addcode;

-- 提前创建未来几个月的表
CREATE TABLE ods_rt_szdn_snapshot_flow_202509 LIKE ods_rt_szdn_snapshot_flow_addcode;
CREATE TABLE ods_rt_szdn_snapshot_flow_202510 LIKE ods_rt_szdn_snapshot_flow_addcode;
```

---

## 🔧 监控与运维

### 关键日志
- Kafka 消费日志：`SnapshotFlowKafkaConsumer`
- ES 查询日志：`SnapshotFlowElasticsearchService`
- 降级日志：`SnapshotFlowEnhancedService`

### 健康检查
- ES 健康：`GET http://127.0.0.1:9200/_cluster/health`
- Kafka 主题：`kafka-topics.bat --list --bootstrap-server localhost:9092`
- 消费者组：`kafka-consumer-groups.bat --list --bootstrap-server localhost:9092`

### Redis 幂等键
键格式：`snapshot:flow:idempotent:{bigId}`
过期时间：24小时

---

## 📊 性能对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 查询延迟 | 秒级 | 毫秒级 |
| 模糊查询 | 慢/超时 | 快 |
| 并发支持 | 低 | 高 |
| 可用性 | 单点 | 多级降级 |
| 数据量 | 300G 单表 | ES + 分表 |

---

## ⚠️ 注意事项

### 1. 历史数据迁移
当前方案只处理实时增量数据，历史数据需要：
- 编写迁移脚本，从 GaussDB 批量读取
- 发送到 Kafka 或直接写入 ES 和 MySQL 分表

### 2. ES 索引管理
- 定期清理旧索引
- 监控索引大小
- 考虑索引冷热分离

### 3. Kafka 消息积压
- 监控消费者 lag
- 增加并发消费者数
- 必要时增加分区

### 4. MySQL 分表管理
- 定时任务提前创建下月分表
- 归档/删除旧分表数据

---

## 📚 相关文档

- [KAFKA_ES_INSTALL_GUIDE.md](./KAFKA_ES_INSTALL_GUIDE.md) - 详细安装指南
- 代码中文注释已添加到所有核心类

---

## 🤝 技术支持

如有问题，请查看：
1. 各服务的日志文件
2. KAFKA_ES_INSTALL_GUIDE.md 中的常见问题章节
3. 代码中的详细中文注释
