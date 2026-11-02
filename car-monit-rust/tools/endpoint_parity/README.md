# 两端接口对等校验（endpoint parity）

同一份 MySQL + Redis 上，把 Java 3.8.7 与 Rust 迁移版的每个 GET 端点逐一对照：
HTTP 状态、`code`/`msg`、`total`、`rows` 长度、键集合、嵌套对象的键/值/类型。
结论口径见 `docs/03-INTERFACE-VERIFICATION.md`。

## 前置条件

1. Java 已启动（默认 `http://127.0.0.1:9988`）。
2. Rust 已启动，且不能占用 Java 的 9988；仓库内 `config/application.yaml` 默认 9989
   与本机 Python 服务冲突，建议：`APP_SERVER__PORT=9990 cargo run`。
3. MySQL `127.0.0.1:3307/carmonitdb`、Redis `127.0.0.1:6379` 已就绪，两端指向同一份数据。
4. 登录账号只从环境变量读取（仓库里不留口令）：

   ```bash
   export PARITY_USER=admin
   export PARITY_PASSWORD='<本地库密码>'
   ```

   验证码开启时脚本会直接从 Redis `captcha_codes:{uuid}` 取答案，无需人工识别。

## 用法

```bash
cd car-monit-rust

# 1) 由基线文档生成端点清单（GET 297 条）
python -m tools.endpoint_parity.endpoints

# 2) 全量对比
python -m tools.endpoint_parity.compare --report build/parity-report.json

# 只查某几个模块 / 某几个前缀
python -m tools.endpoint_parity.compare --only /tool/gen --only /manager/confimfree

# CI：有硬差异就失败
python -m tools.endpoint_parity.compare --strict --quiet --report build/parity-report.json
```

常用参数：`--java-base`、`--rust-base`、`--endpoints`、`--report`、`--only`（可重复）、
`--skip`（可重复）、`--workers`（默认 6）、`--strict`、`--quiet`。
也可用环境变量 `PARITY_JAVA_BASE` / `PARITY_RUST_BASE` / `PARITY_ENDPOINTS` /
`PARITY_REPORT` / `PARITY_WORKERS` / `PARITY_REDIS_HOST` / `PARITY_REDIS_PORT` 设默认值。

## 结果分类

| 状态 | 判据 |
|---|---|
| OK | 无下列任何一项 |
| WARN | `ORDER-DIFF`（Jackson 继承字段在前 vs SQL 列序）、`MSG-DIFF`（MyBatis 与 sqlx 异常文案）、`TOTAL-WARN`（动态端点的 total 波动） |
| FAIL | `STATUS-DIFF` / `CODE-DIFF` / `MISSING` / `EXTRA` / `LEN-DIFF` / `TOTAL-DIFF` / `VALUE-DIFF` / `TYPE-DIFF` / `BIN-DIFF` / `JSON-BINARY-DIFF` |
| KNOWN | 依赖不可用上游或 Java 自身故障，仍会记录差异明细 |
| SKIP | 有写入/远端副作用的 GET（如 `syncAllGeometry`、`synchDb`），不请求 |

导出类端点只比状态、Content-Type 类别与文件头，不比字节
（`ExcelUtil.exportExcel` 的文件名是随机 UUID）。

## 数据不稳定时的处理

- 路径变量样例值集中在 `compare.py` 的 `S` / `RULES` / `SPECIAL_Q`；
  换数据集时只改这三处。
- 动态端点（登录日志、在线用户、缓存 INFO 等）前缀写进 `DYNAMIC`，
  它们的 `total` 只降级为 `TOTAL-WARN`；键名命中 `DYN_KEYS`（`createTime`、`token`…）
  的标量值不参与比较。
- 透传 `vehicleMonitor.baseUrl` 上游的端点每次返回随机主键，
  写进 `SHAPE_ONLY`：只比结构（键集合/类型/长度），不比标量值。

## 代码生成（Velocity 模板）专项对拍

`compare.py` 对二进制只比状态与文件头，`/tool/gen/download`、`/tool/gen/batchGenCode`
需要解压后按文件比，因此单独两个脚本：

```bash
# 逐模板：先采 Java 基准，再比 Rust（模板 key 与 Java 一致）
python -m tools.endpoint_parity.gen_preview_diff --table-id 231 --save-oracle
python -m tools.endpoint_parity.gen_preview_diff --table-id 231

# zip：单表 / 多表 / gen_table 全表
python -m tools.endpoint_parity.gen_zip_diff --table-name car_except_record
python -m tools.endpoint_parity.gen_zip_diff --tables car_except_record,car_info
python -m tools.endpoint_parity.gen_zip_diff --all-tables
```

`gen_zip_diff` 比条目名与顺序、每个条目的字节，另外打印 `Content-Type` /
`Content-Disposition` / `Content-Length`。Java 用 `java.util.zip`（DEFLATE），
Rust 用 STORE，压缩包本身不可能同字节，脚本比的是解压后的结果；
`Content-Length` 因此必然不等，不计入失败。基准文件按 `newline=''` 读写，
CRLF 不做归一——模板与产物都保留 CRLF，归一会掩盖真实差异。

## CI

`.github/workflows/car-monit-rust.yml` 默认跑 `cargo fmt --check`、`cargo clippy`、
`cargo test`。两端对比需要本机 MySQL/Redis/Java，公共 runner 起不来，
所以只在 `workflow_dispatch` 且显式填入 `java_base`/`rust_base`/secrets 时才执行，
并以 `--strict` 的退出码作为门控。
