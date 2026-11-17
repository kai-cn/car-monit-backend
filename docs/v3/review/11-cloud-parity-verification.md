# 11 云端全接口 + 资源性能对比验收（backend 侧）

> 日期：2026-11-17。承接 10-public-cicd-native-verification.md。
> api 侧完整方法/坑点见 api 仓库 `docs/v3/review/11-cloud-parity-verification.md`；
> 本文档记录 backend 相关事实与跨语言对比。

## 1. 组件（随分支入库）

| 文件 | 作用 |
| --- | --- |
| `.github/workflows/parity-verify-cloud.yml` | backend native vs JVM（jdk × linux/windows）|
| `.github/workflows/crosslang-parity-cloud.yml` | **Java8 master 基线 vs Go/Python/Rust** 跨语言对比 |
| `scripts/v3/ops/parity/parity_probe.py` | 单变体探针（进程树 RSS、稳定性检测）|
| `scripts/v3/ops/parity/parity_compare.py` | 双变体对比（status/exact/semantic/nondet）|
| `scripts/v3/ops/parity/endpoints/backend.txt` | 免认证 GET 端点（`/captchaImage`、`/`）|
| `scripts/v3/ops/parity/sql/schema_carmonitdb.sql` | MySQL 全量 84 表结构 |
| `scripts/v3/ops/parity/sql/seed_carmonitdb.sql` | 核心表种子（sys_user/role/menu/dept/dict 等）|

## 2. backend 特有坑点（如实记录）

### 2.1 `process-aot` 绑定默认生命周期，jar 构建需 logs 目录
- 现象：`mvn -pl ruoyi-admin -am install` 在 `spring-boot-maven-plugin:4.1.2:process-aot` 失败
  （`Process terminated with exit code`）。
- 根因：为 native 构建引入的 `process-aot` execution 绑定在默认 lifecycle，AOT 会真实启动应用，
  logback 需 `/home/ruoyi/logs` 存在。
- 修复：jar 步骤前 `sudo mkdir -p /home/ruoyi/logs && sudo chown`。

### 2.2 backend 端点几乎都需要认证
- RuoYi 后端仅 `/captchaImage`、`/login`（POST）、`/getCode` 免认证。
- 探针只做 GET，故 backend 的 native-vs-jvm 全接口对比实质覆盖
  `/captchaImage`（随机验证码 → NONDET）+ 启动时间 + 峰值 RSS + 延迟。
- 全接口（79 端点）对比在 **api 侧**完成（api 的 GET 端点免认证且不受 Security 拦截）。

### 2.3 MySQL 8.0 首次启动慢
- 现象：`docker exec my mysqladmin ping` 通过后 `mysql` 客户端仍报
  `Can't connect ... socket '/var/run/mysqld/mysqld.sock'`。
- 修复：就绪检测与 schema/seed 加载全部改走 `-h127.0.0.1 -P3306 --protocol=TCP` + 重试。

## 3. 跨语言对比（Java8 vs Go/Python/Rust）

- 基线：`master` 分支 ruoyi-admin（Java 8 / Spring Boot 2.5）fat jar。
- 候选：`car-monit-go`（Go/gin/`cmd/server`）、`car-monit-py`（FastAPI+uvicorn）、
  `car-monit-rust`（Axum）。
- **C# / Kotlin / C++ 被跳过**：本仓库这三个目录只有部分迁移代码，**没有可运行的 HTTP 服务**，
  无法做接口对比（如实记录，不臆造结果）。
- 共同免认证 GET 端点：`/captchaImage`（返回随机验证码图片，body 必然 NONDET；
  因此跨语言对比主要看 **status 一致性 + 启动时间 + 峰值 RSS + 延迟**）。
- 所有变体共享同一 MySQL + Redis 种子。

## 4. 复现

```bash
# native vs jvm（backend）
gh workflow run parity-verify-cloud.yml -R kai-cn/car-monit-backend \
   --ref car-monit-backend-jdk25 -f jdk=25 -f platform=linux -f repeat=2

# 跨语言（Java8 vs go/python/rust）
gh workflow run crosslang-parity-cloud.yml -R kai-cn/car-monit-backend \
   --ref master -f langs=all
```

## 5. 结果
见 `docs/v3/review/11-results.md`。
