# 第三方库替换进度与阻塞说明（2026-11-08）

## 已完成：Kafka → librdkafka 2.15.1

- 提交：`da07184 refactor(kafka): 传输层替换为 librdkafka，删除自研协议层`
- 行数：`+501 / −1505`（净减 1004 行）；`KafkaClient.cpp` 849 → 376，删除 `KafkaCodec.{hpp,cpp}`（562 行）
- 依赖获取：vcpkg manifest（`vcpkg.json`，baseline `6fdd23fa`），本机 vcpkg 在 `D:\work\IdeaProjects\vcpkg`。
  因本机 schannel 吊销检查不可达，vcpkg 内置 curl 下载 GitHub 会报 `error 35`；解决方式是
  `curl --ssl-no-revoke` 预下载到 `vcpkg/downloads/`（文件名规则：工具类为 `SHA512 前8位-原名`）。
- 配置对齐：`enable.auto.commit=false` + `enable.auto.offset.store=false`；`max.poll.records=500`
  由 `poll()` 每批上限实现；`session.timeout.ms` / `max.poll.interval.ms` / `fetch.max.bytes` 直接透传；
  `partition.assignment.strategy=range`、`isolation.level=read_uncommitted` 对齐 Java 默认值。
- 业务语义保持不变（`SnapshotFlowKafkaConsumer`）：批量 500、手动提交、Redis 幂等、重试 3×1s、DLQ、
  写库失败不提交位点。写库失败时用 `rd_kafka_seek_partitions` 回退本批最小位点，立即重投。
- 单元测试：`carmonit_tests` ALL TESTS PASSED（含新增 KafkaConfig 默认值/引导串解析断言）。

### 实测（cm-verify-rd3，真实 Kafka 2.12-2.8.2）

console-producer 在 Windows 下会把每条输入复制成两条，因此 4 条测试消息实际入 topic 8 条：

- 消费 8 条，落库 1 行（同一 bigId 的重复消息被幂等去重），成功计数 1，失败计数 4
- DLQ 20 条 = 4 条非法消息 × 5（首次校验失败 1 + 本地重试 3 + 终态“重试失败”1）；与 Java 行为一致
- 位点提交：partition=0 nextOffset=8（全部消费完才提交）
- 吞吐 0.3 条/秒、平均延迟 18.8s（延迟含消息在 topic 中排队的时间，不是传输层耗时）

## 阻塞：D 盘空间耗尽

- 测试前 D 盘可用接近 0，Kafka 启动即报 `IOException: 磁盘空间不足`（segment 预分配），MSVC 也报 C1060。
- 删除的临时数据被系统转移到回收站，`Clear-RecycleBin -DriveLetter D -Force` 未能释放空间
  （执行超时/无报错，可用空间不变）。
- 为让机器可用，已把 `build/` 下所有 `.obj/.lib` 截断为 0 字节，并清空临时 Kafka/ZK 数据目录；
  当前 D 盘约 120MB。**下次编译会全量重编，需要 ≥2GB 可用空间。**

### 恢复步骤（需要人工）

1. 清空 D 盘回收站（预计释放 ≥1.4GB），或腾出 ≥2GB 可用空间。
2. 重新配置并编译：
   `cmake -S . -B build -DCMAKE_PREFIX_PATH=<repo>/vcpkg_installed/x64-windows`
   `cmake --build build --config Release --target carmonit_tests carmonit_kafka_verify --parallel 1`
3. 起临时 ZK/Kafka 时使用低占用参数（否则 50 个 `__consumer_offsets` 分区会预分配掉数百 MB）：
   `--override log.segment.bytes=4194304 --override offsets.topic.num.partitions=1
    --override offsets.topic.replication.factor=1 --override transaction.state.log.num.partitions=1
    --override transaction.state.log.replication.factor=1`
4. 继续下一项：MySQL → libmysqlclient（COM_STMT），保持 `Params/bind` 调用面，
   跑 `carmonit_db_verify` 27 项矩阵 + QPS 前后对照。

## 本轮自主决策记录

- 选型表的 MySQL 走官方 Connector/C 预编译包（本机 `D:\work\mysql-8.0.30-winx64` 已含头文件与 `libmysql.lib`），
  不用 vcpkg `libmysql`（需从源码整包编译，依赖 boost/openssl，磁盘与时间都不允许）。
- Kafka 用 librdkafka C API（同一库的 C++ wrapper 仅在其上做薄封装），保留精确的位点存储/回退控制。
- 现有 `build/` 目录生成于 vcpkg 工具链接入之前，无法中途切换 toolchain，因此用 `CMAKE_PREFIX_PATH`
  指向 `vcpkg_installed/x64-windows`，并在 CMake 里用 `$<TARGET_RUNTIME_DLLS>` 拷贝 DLL。
- bcrypt vendor 的 `include/bcrypt` 目录从 PUBLIC 改为 PRIVATE：它会遮蔽 Windows SDK 的 `<bcrypt.h>`，
  导致引入 librdkafka 后 `ncrypt.h/wincrypt.h` 编译失败。
