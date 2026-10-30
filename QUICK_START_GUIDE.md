# 快速启动指南（针对当前目录结构）

## 📂 当前目录结构
```
D:\work\
├── kafka_2.13-4.0.0\          ← Kafka 4.0.0（已配置KRaft模式，无需ZooKeeper）
├── apache-zookeeper-3.7.1-bin\ ← ZooKeeper（暂时不需要）
└── elasticsearch-7.15.2\   ← Elasticsearch 7.15.2
```

---

## 🚀 快速启动（3步）

### 第 1 步：启动 Kafka

打开 **新的命令行窗口**，执行：
```cmd
cd /d D:\work\kafka_2.13-4.0.0
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

✅ 看到 `Kafka Server started` 表示启动成功

---

### 第 2 步：启动 Elasticsearch

打开 **新的命令行窗口**，执行：
```cmd
cd /d D:\work\elasticsearch-7.15.2
.\bin\elasticsearch.bat
```

✅ 浏览器访问 http://127.0.0.1:9200 验证

---

### 第 3 步：创建 Kafka 主题（可选）

打开 **新的命令行窗口**，执行：
```cmd
cd /d D:\work\kafka_2.13-4.0.0\bin\windows
kafka-topics.bat --create --topic snapshot-flow-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

查看主题：
```cmd
kafka-topics.bat --list --bootstrap-server localhost:9092
```

---

## ⚙️ 更新应用配置

检查 `ruoyi-admin/src/main/resources/application.yml` 中的配置：

```yaml
kafka:
  bootstrap-servers: 127.0.0.1:9092

elasticsearch:
  host: 127.0.0.1
  port: 9200
```

---

## 📋 端口说明

| 服务 | 端口 | 验证地址 |
|------|------|----------|
| Kafka | 9092 | 查看启动日志 |
| Elasticsearch | 9200 | http://127.0.0.1:9200 |
| Redis | 6379 | 确保已启动 |

---

## ❓ 常见问题

### Q1: Kafka 启动报错 "系统找不到指定的路径"
A: 检查 `server.properties` 中的 `log.dirs`，已修复为：
```properties
log.dirs=D:/work/kafka_2.13-4.0.0/logs
```

### Q2: Log4j 警告信息
A: 可以忽略，Kafka 4.0.0 仍兼容 Log4j 1.x 配置

### Q3: 需要 ZooKeeper 吗？
A: **不需要**！Kafka 4.0.0 使用 KRaft 模式，已内置控制器

---

## 🛑 停止服务

直接关闭各命令行窗口即可。
