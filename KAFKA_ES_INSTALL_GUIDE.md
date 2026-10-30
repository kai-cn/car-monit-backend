# Kafka 和 Elasticsearch 安装指南

## 目录
1. [环境准备](#环境准备)
2. [JDK 安装](#jdk-安装)
3. [ZooKeeper 安装](#zookeeper-安装)
4. [Kafka 安装](#kafka-安装)
5. [Elasticsearch 安装](#elasticsearch-安装)
6. [Kibana 安装（可选）](#kibana-安装可选)
7. [启动与验证](#启动与验证)

---

## 环境准备

### 目标安装目录
```
D:\work\
├── jdk\
├── zookeeper\
├── kafka\
└── elasticsearch\
```

### 系统要求
- 操作系统：Windows 10/11 或 Windows Server
- 内存：至少 8GB（推荐 16GB）
- 磁盘：至少 50GB 可用空间
- 网络：本地访问，无需公网

---

## JDK 安装

### 下载
- 下载地址：https://www.oracle.com/java/technologies/downloads/
- 版本选择：JDK 8 或 JDK 11（与项目匹配）
- 下载文件：jdk-8uxxx-windows-x64.exe 或 zip 包

### 安装步骤

1. **解压到目标目录**
   ```
   D:\work\jdk\
   ```

2. **配置环境变量**
   
   右键 "此电脑" → 属性 → 高级系统设置 → 环境变量
   
   - 新建系统变量：
     ```
     变量名：JAVA_HOME
     变量值：D:\work\jdk
     ```
   
   - 编辑 Path 变量，添加：
     ```
     %JAVA_HOME%\bin
     ```

3. **验证安装**
   ```cmd
   java -version
   javac -version
   ```

---

## ZooKeeper 安装

### 下载
- 下载地址：https://zookeeper.apache.org/releases.html
- 版本选择：Apache ZooKeeper 3.7.x 或 3.8.x（稳定版）
- 下载文件：apache-zookeeper-3.7.1-bin.tar.gz

### 安装步骤

1. **解压到目标目录**
   ```
   D:\work\zookeeper\
   ```

2. **配置 ZooKeeper**
   
   进入 `D:\work\zookeeper\conf` 目录，复制 `zoo_sample.cfg` 为 `zoo.cfg`
   
   编辑 `zoo.cfg`：
   ```properties
   # 数据存储目录
   dataDir=D:/work/zookeeper/data
   
   # 日志目录
   dataLogDir=D:/work/zookeeper/logs
   
   # 客户端端口
   clientPort=2181
   
   # 最大连接数
   maxClientCnxns=60
   ```

3. **创建数据和日志目录**
   ```
   D:\work\zookeeper\data\
   D:\work\zookeeper\logs\
   ```

4. **启动 ZooKeeper**
   
   打开命令行，进入 `D:\work\zookeeper\bin`：
   ```cmd
   zkServer.cmd
   ```
   
   看到 `binding to port 0.0.0.0/0.0.0.0:2181` 表示启动成功

---

## Kafka 安装

### 下载
- 下载地址：https://kafka.apache.org/downloads
- 版本选择：Apache Kafka 2.8.x 或 3.0.x（Scala 2.13）
- 下载文件：kafka_2.13-2.8.2.tgz

### 安装步骤

1. **解压到目标目录**
   ```
   D:\work\kafka\
   ```

2. **配置 Kafka**
   
   编辑 `D:\work\kafka\config\server.properties`：
   ```properties
   # Broker ID
   broker.id=0
   
   # 监听地址
   listeners=PLAINTEXT://:9092
   
   # 数据目录
   log.dirs=D:/work/kafka/logs
   
   # ZooKeeper 连接地址
   zookeeper.connect=localhost:2181
   
   # 消息保留时间（小时）
   log.retention.hours=168
   
   # 自动创建主题
   auto.create.topics.enable=true
   
   # 默认分区数
   num.partitions=3
   
   # 副本因子
   default.replication.factor=1
   ```

3. **创建日志目录**
   ```
   D:\work\kafka\logs\
   ```

4. **启动 Kafka**
   
   打开新的命令行窗口，进入 `D:\work\kafka`：
   ```cmd
   .\bin\windows\kafka-server-start.bat .\config\server.properties
   ```
   
   看到 `started (kafka.server.KafkaServer)` 表示启动成功

5. **创建测试主题（可选）**
   
   打开新的命令行窗口，进入 `D:\work\kafka\bin\windows`：
   ```cmd
   kafka-topics.bat --create --topic snapshot-flow-topic --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
   ```
   
   查看主题：
   ```cmd
   kafka-topics.bat --list --bootstrap-server localhost:9092
   ```

---

## Elasticsearch 安装

### 下载
- 下载地址：https://www.elastic.co/cn/downloads/past-releases/elasticsearch-7-15-2
- 版本选择：Elasticsearch 7.15.2（与代码中版本一致）
- 下载文件：elasticsearch-7.15.2-windows-x86_64.zip

### 安装步骤

1. **解压到目标目录**
   ```
   D:\work\elasticsearch\
   ```

2. **配置 Elasticsearch**
   
   编辑 `D:\work\elasticsearch\config\elasticsearch.yml`：
   ```yaml
   # 集群名称
   cluster.name: snapshot-flow-cluster
   
   # 节点名称
   node.name: node-1
   
   # 数据存储路径
   path.data: D:/work/elasticsearch/data
   
   # 日志路径
   path.logs: D:/work/elasticsearch/logs
   
   # 网络绑定地址
   network.host: 127.0.0.1
   
   # HTTP 端口
   http.port: 9200
   
   # 发现节点
   discovery.seed_hosts: ["127.0.0.1"]
   cluster.initial_master_nodes: ["node-1"]
   
   # 禁用 X-Pack 安全（开发环境）
   xpack.security.enabled: false
   ```

3. **创建数据和日志目录**
   ```
   D:\work\elasticsearch\data\
   D:\work\elasticsearch\logs\
   ```

4. **修改 JVM 配置（可选，根据内存调整）**
   
   编辑 `D:\work\elasticsearch\config\jvm.options`：
   ```
   -Xms2g
   -Xmx2g
   ```
   如果内存较小，可以改为 1g：
   ```
   -Xms1g
   -Xmx1g
   ```

5. **解决 Windows 启动问题**
   
   如果遇到 `java.nio.file.AccessDeniedException`，以管理员身份运行命令行。

6. **启动 Elasticsearch**
   
   打开命令行，进入 `D:\work\elasticsearch\bin`：
   ```cmd
   elasticsearch.bat
   ```
   
   看到 `started` 表示启动成功

7. **验证安装**
   
   浏览器访问：http://127.0.0.1:9200
   
   应该返回类似 JSON：
   ```json
   {
     "name" : "node-1",
     "cluster_name" : "snapshot-flow-cluster",
     "cluster_uuid" : "...",
     "version" : {
       "number" : "7.15.2",
       ...
     },
     "tagline" : "You Know, for Search"
   }
   ```

8. **创建 ES 索引（可选，应用启动时也会自动创建）**
   
   使用 Postman 或 curl 发送 PUT 请求：
   ```
   PUT http://127.0.0.1:9200/snapshot-flow
   {
     "mappings": {
       "properties": {
         "bigId": {"type": "keyword"},
         "platenumber": {"type": "text", "analyzer": "standard"},
         "snapshottime": {"type": "date"},
         "sectioncode": {"type": "keyword"},
         "orgcode": {"type": "keyword"},
         "gantrycode": {"type": "keyword"},
         "direction": {"type": "integer"}
       }
     }
   }
   ```

---

## Kibana 安装（可选）

### 下载
- 下载地址：https://www.elastic.co/cn/downloads/past-releases/kibana-7-15-2
- 版本选择：Kibana 7.15.2（与 ES 版本一致）
- 下载文件：kibana-7.15.2-windows-x86_64.zip

### 安装步骤

1. **解压到目标目录**
   ```
   D:\work\kibana\
   ```

2. **配置 Kibana**
   
   编辑 `D:\work\kibana\config\kibana.yml`：
   ```yaml
   server.port: 5601
   server.host: "127.0.0.1"
   elasticsearch.hosts: ["http://127.0.0.1:9200"]
   ```

3. **启动 Kibana**
   
   打开命令行，进入 `D:\work\kibana\bin`：
   ```cmd
   kibana.bat
   ```

4. **访问 Kibana**
   
   浏览器访问：http://127.0.0.1:5601

---

## 启动与验证

### 完整启动顺序

1. **启动 ZooKeeper**
   ```cmd
   cd D:\work\zookeeper\bin
   zkServer.cmd
   ```

2. **启动 Kafka**
   ```cmd
   cd D:\work\kafka
   .\bin\windows\kafka-server-start.bat .\config\server.properties
   ```

3. **启动 Elasticsearch**
   ```cmd
   cd D:\work\elasticsearch\bin
   elasticsearch.bat
   ```

4. **启动 Kibana（可选）**
   ```cmd
   cd D:\work\kibana\bin
   kibana.bat
   ```

### 验证服务

| 服务 | 地址 | 验证方式 |
|------|------|----------|
| ZooKeeper | localhost:2181 | 查看启动日志 |
| Kafka | localhost:9092 | 查看启动日志 |
| Elasticsearch | http://127.0.0.1:9200 | 浏览器访问 |
| Kibana | http://127.0.0.1:5601 | 浏览器访问 |

### 快速启动脚本（Windows）

创建 `start-all.bat` 到 `D:\work\` 目录：

```batch
@echo off
echo 正在启动 ZooKeeper...
start "ZooKeeper" cmd /k "cd /d D:\work\zookeeper\bin && zkServer.cmd"

timeout /t 5 /nobreak > nul

echo 正在启动 Kafka...
start "Kafka" cmd /k "cd /d D:\work\kafka && .\bin\windows\kafka-server-start.bat .\config\server.properties"

timeout /t 10 /nobreak > nul

echo 正在启动 Elasticsearch...
start "Elasticsearch" cmd /k "cd /d D:\work\elasticsearch\bin && elasticsearch.bat"

echo 所有服务启动中，请检查各窗口日志...
pause
```

创建 `stop-all.bat`：

```batch
@echo off
echo 正在停止服务...
taskkill /FI "WINDOWTITLE eq ZooKeeper*" /F
taskkill /FI "WINDOWTITLE eq Kafka*" /F
taskkill /FI "WINDOWTITLE eq Elasticsearch*" /F
echo 服务已停止
pause
```

---

## 常见问题

### 1. Kafka 启动失败
- 检查 ZooKeeper 是否正常启动
- 检查端口 2181、9092 是否被占用
- 查看 `D:\work\kafka\logs\` 下的日志

### 2. Elasticsearch 启动失败
- 检查 JDK 版本（需要 JDK 8 或 11）
- 检查内存是否足够
- 查看 `D:\work\elasticsearch\logs\` 下的日志

### 3. 端口被占用
使用以下命令查看端口占用：
```cmd
netstat -ano | findstr "2181"
netstat -ano | findstr "9092"
netstat -ano | findstr "9200"
```

### 4. 内存不足
- 减少 Elasticsearch 的 JVM 堆内存（修改 jvm.options）
- 关闭其他占用内存的程序

---

## 下一步

安装完成后：

1. 修改项目 `application.yml` 中的配置（如果需要）
2. 启动 car-monit-backend 应用
3. 发送测试消息到 Kafka 验证数据同步
4. 使用前端页面查询，验证 ES 查询性能

---

## 参考资料

- Kafka 官方文档：https://kafka.apache.org/documentation/
- Elasticsearch 官方文档：https://www.elastic.co/guide/en/elasticsearch/reference/7.15/index.html
- ZooKeeper 官方文档：https://zookeeper.apache.org/doc/current/
