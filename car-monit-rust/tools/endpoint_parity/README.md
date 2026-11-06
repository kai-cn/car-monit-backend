# 两端接口对等校验（endpoint parity）

同一份 MySQL + Redis 上，把 Java 3.8.7 与 Rust 迁移版的每个 GET 端点逐一对照：
HTTP 状态、`code`/`msg`、`total`、`rows` 长度、键集合、嵌套对象的键/值/类型。
结论口径见 `docs/03-INTERFACE-VERIFICATION.md`。

## 前置条件

1. Java 已启动（默认 `http://127.0.0.1:9988`）。
2. Rust 已启动，且不能占用 Java 的 9988；仓库内 `config/application.yaml` 默认 9989
   与本机其它服务冲突，用 `build/run-rust.cmd` 起（它把端口固定成 9990 并关掉调度器）。
3. MySQL `127.0.0.1:3307/carmonitdb`、Redis `127.0.0.1:6379` 已就绪，两端指向同一份数据。
4. **两端各成一整套**：backend-Java(9988) 与 api 的 Java 端(9902) 共用 Redis db0，
   backend-Rust(9990) 与 `car-monit-api-rust`(9911) 共用 db15；
   `client.py` 的 `REDIS_DB_JAVA=0` / `REDIS_DB_RUST=15` 就按这个来取验证码与缓存。
   Java 端要用 `--vehicleMonitor.baseUrl=http://127.0.0.1:9902` 起，Rust 的配置指 9911，
   否则两端各打各的上游，`/base/*` 的比分是假的。
5. 登录账号只从环境变量读取（仓库里不留口令）：

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
- 只有**个别标量**不稳定时用 `VALUE_FREE`（按端点给一个路径正则），
  例如 `/manager/suspicious/{id}` 的 `*.paths` —— 那段路径点是腾讯 direction /
  本地路网规划服务的实时结果，同一时间窗内两端逐字节一致，跨窗会因路网刷新差几个点。
  用 `SHAPE_ONLY` 会把整个响应降级成只比结构，别滥用。

## 上游链路（backend → api）与路径变量类型专项

```bash
# backend 调 api 的链路：24 条带真实上游返回值，掩码 uuid/时间戳后比
python -m tools.endpoint_parity.api_chain_matrix

# Java 侧 @PathVariable 是数字类型的端点，用非法值探 GET（28 条量级）
python -m tools.endpoint_parity.pathvar_matrix --inventory   # 只看清单
python -m tools.endpoint_parity.pathvar_matrix               # 只探 GET
python -m tools.endpoint_parity.pathvar_matrix --writes      # 只探 DELETE/PUT/POST
python -m tools.endpoint_parity.pathvar_matrix --all         # 两类都探

# 写端点探针的前后行数快照（23 张表），用来证明探针没改动业务数据
python -m tools.endpoint_parity.db_snapshot.py before
python -m tools.endpoint_parity.db_snapshot.py diff
```

`pathvar_matrix.py` 直接从 Java 源码解析（控制器不止在 `ruoyi-admin`，`ruoyi-quartz`、
`ruoyi-generator` 也要扫），因此它能发现基线清单漏掉的控制器——`/oss/*` 就是这么露出来的。
GET 用 `1x`；写端点**不能**用 `1x`（宽松实现会当成 id=1，而 1 是 admin 用户/超级角色），
`--writes` 换成 `30000000x`：Java 在类型转换阶段就失败，宽松实现也只是 `WHERE id = 30000000` 命中 0 行。
配合 `db_snapshot.py` 的 before/diff 可以证明业务表一行没动。
Java 遇到非法数字会在进控制器之前失败，文案是
`请求参数类型不匹配，参数[jobIds]要求类型为：'[Ljava.lang.Long;'，但输入值为：'1,1x'`
——第三个占位是**整段**路径变量原文，不是出错的那一段。

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

## 写入路径（POST/PUT/DELETE）的矩阵 + 导入夹具

`compare.py` 只覆盖 GET，写入语义由这几个脚本盯（结果记录在 `docs/03` §7–§9）：

```bash
python -m tools.endpoint_parity.cron_matrix          # 59 条 Quartz 表达式的接受度与 nextValidTime
python -m tools.endpoint_parity.job_invoke_matrix    # 25 个 invokeTarget 的 sys_job_log 结果
python -m tools.endpoint_parity.job_write_matrix     # /monitor/job 写入端点的 18 条语义分支
python -m tools.endpoint_parity.post_smoke_matrix    # 14 个新增端点 × 两种请求体（last_insert_id / 非列字段守门）
python -m tools.endpoint_parity.write_crud_matrix    # manager_crud! 的 11 张表 POST→回读→DELETE
python -m tools.endpoint_parity.write_crud_matrix --only whiteinfo --verbose   # 子串过滤，别写 /manager/...

# Excel 导入：往自带模板追加数据行，再两端上传比原始响应
FX_TEMPLATE=config/templates/down/importCar.xlsx \
    python -m tools.endpoint_parity.xlsx_fixture build/cx.xlsx '[[0,"蓝色"],[1,"测CX0001"],[2,"客一"]]'
python -m tools.endpoint_parity.import_probe build/cx.xlsx

# /base/* 透传端点要先起桩上游（外部 Python 服务不在本仓库）
python -m tools.endpoint_parity.mock_vehicle_monitor --port 9901
```

起 Java 时必须把上游也指到桩，否则两端各打各的（jar 里默认是 9902 的真实 `car-monit-api`，
Rust 的配置指 9901），`/base/feerecords/{bigId}` 一类会出现假的 FAIL：

```bash
java -jar ruoyi-admin.jar --server.port=9988 --vehicleMonitor.baseUrl=http://127.0.0.1:9901
```

`sys_dict:*` 这类「读缓存直接出参」的端点要**先热缓存再比**：冷缓存下先调用的一方走 DB、
后调用的一方走缓存，出参就差一个 `params` 键（Java 冷：无 `params`；Java 热：原样回显
`{"@type":"java.util.HashMap"}`）。这不是两端代码的差异——同一端从冷启动跑两次就一致了。
清过 Redis 之后先 `curl` 一遍 `/system/dict/data/type/{任一 dictType}` 再跑 `compare.py`。

`write_crud_matrix` 从 `src/api/**/*.rs` 的 `manager_crud!` 宏块自动推导 route/table/列，
**两端用不同后缀的标记**（两端写同一个库，标记相同会各自认领对方的行），
按 POST 返回的 id 回读再删；`id`/审计列/带标记的列不参与比较。
它只软删行（DELETE 端点就是软删），收尾按打印出的 `parityW<stamp>` 前缀硬删。

三个矩阵都会自己清理建出来的行（`sys_job` 按任务名删、`sys_job_log` 按日志 id 删）；
耗时毫秒、自增 id、异常栈（只比首行）在比较前归一化。
两端同为 500、只差 MyBatis/SQLx 报错包装文案的，判 WARN 而不是 FAIL（`docs/03` §7.8）。

## CI

`.github/workflows/car-monit-rust.yml` 默认跑 `cargo fmt --check`、`cargo clippy`、
`cargo test`。两端对比需要本机 MySQL/Redis/Java，公共 runner 起不来，
所以只在 `workflow_dispatch` 且显式填入 `java_base`/`rust_base`/secrets 时才执行，
并以 `--strict` 的退出码作为门控。
