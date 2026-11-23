<!--
@description 记录 endpoint body.code 判据下的逐项复查、代码修复、最终验证结果、复现步骤和脚本索引。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
-->

# Endpoint body.code 判据最终闭环

## 判定口径

- `body.code == 200`：请求成功。
- `body` 中没有 `code` 字段：结果待定。
- `body.code != 200`：单独记录，复查服务日志与源码；确认代码缺陷后修复。

## 过程

1. 以 WSL `/home/dev/IdeaProjects/car-monit-backend`、`car-monit-api` 的 `master` 为唯一基线。
2. 分析 `junit-contract.json` 中每个 endpoint 的 `body.code`，分类 success / pending_no_code / non_200。
3. 对照 `app.log`、`api.log` 定位非 200 根因，逐项修复源码、SQL fixture、环境变量和本机依赖。
4. 重新编译 backend/api master jar，启动 MySQL、Redis、PostgreSQL、ES 与 api 下游服务。
5. 使用管理员登录态重跑 302 endpoint 契约与压测。
6. 再次按 `body.code` 判据统计，并保留未通过项的真实业务语义。

## 已确认并修复的代码问题

### backend

- `FlowMessageInfoMapper.xml`、`SysIndexMenuMapper.xml`：Linux MySQL 表名大小写错误。
- `SysJobLogController`：路径变量 `{configId}` 与参数 `jobLogId` 不一致。
- `BigScreenController`：`type` 必填导致探测 500，改为可选。
- `GenController` / `GenTableServiceImpl`：路径变量、空表、空参数导致的 NPE。
- `FlowMessageInfoController` / `CarSuspiciousController`：空数据导出 NPE。
- `TableDataInfo`：默认成功码统一为 200。
- schema fixture：补充 `sys_upgrade_info`。
- Python/Go/Rust/C++：`geometry_copy1` 遗留表引用。
- Go：新增 `VEHICLE_MONITOR_BASE_URL` 覆盖。
- C++：`TOKEN__SECRET` 环境变量优先。
- workflow：统一 token、下游地址、JDK25、日志目录、datastore 就绪顺序。

### api

- Java/Python mapper：PostgreSQL 列名大小写与 `agentPk` 类型 cast。
- Java/Python/Go/C++：`now() - 180/3` 改为 PostgreSQL interval 写法。
- Go selftest：blocked 维护端点返回与 Java/Rust/Python 一致的 200 空响应。
- Go/Rust 统一查询：必填时间参数校验先于数据源解析。
- Go：Kafka 默认值本地化。
- Java：Elasticsearch host/port 支持环境变量覆盖。
- C++：blocked 自测端点不再制造后台任务噪声。

## 最终结果

- 本机打包：backend/api master 当前源码均成功重建 jar。
- 契约：302/302 成功。
- 压测：130680 请求，130680 ok，0 errors。
- body.code 判据：success=257，pending_no_code=41，non_200=4。
- 剩余非 200：
  - `/base/fitting/list`：api 上游 ES 索引未就绪，数据服务返回 503/UPSTREAM_ERROR；不是 backend 业务代码缺陷。
  - `/manager/confimfree/except/1`：占位 ID 1 无对应异常车辆流水。
  - `/manager/bigScreen/export/status/1`：占位 taskId 1 无对应导出任务。
  - `/manager/bigScreen/export/download/1`：缺少由 download-url 签发的下载令牌。
- 以上四项均保留真实响应，未伪装为 200；前三项属于环境/参数化数据，后一项属于前置步骤缺失。

## 复现步骤

1. 在 WSL 进入 `/home/dev/IdeaProjects/car-monit-backend` 与 `car-monit-api` master。
2. 启动 MySQL/Redis/PostgreSQL/ES，并导入 `scripts/v3/ops/parity/sql` 下对应 schema/seed。
3. 重新编译 backend master `ruoyi-admin` 与 api master `pro-business-api`。
4. 执行 `runtime-logs/wsl-local-retest-with-downstream.py`，通过环境变量提供管理员凭据和导出签名密钥。
5. 执行 `runtime-logs/analyze-endpoint-code.py <junit-contract.json> <out.json>`。
6. 查看 `endpoint-code-analysis.json` 中 success / pending_no_code / non_200 分类与 `junit-contract.json` 的具体 body。

## 脚本索引

- `wsl-local-retest-with-downstream.py`：启动 backend/api 下游并执行契约/压测。
- `analyze-endpoint-code.py`：按 body.code 判据统计。
- `summarize-non200.py`：非 200 错误分类。
- `rebuild-current-backend-master.sh`：重建 backend master jar。
- `start-local-pg.sh`、`load-local-pg-fixtures.sh`、`start-local-es.sh`：本机依赖启动与 fixture 导入。
- `patch-remaining-non200.py`、`patch-remaining-non200-2.py`、`patch-final-generator.py`、`patch-tabledatainfo-code.py`、`patch-last-code-issues.py`、`patch-pg-time-compat.py`、`patch-es-env.py`：逐批代码修复。
- `finalize-body-code-closure.py`：最终文档与证据归档。
