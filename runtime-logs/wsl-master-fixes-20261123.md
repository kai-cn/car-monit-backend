<!--
@description 记录 WSL master 基线下的非 200 端点修复过程、云端与本机结果、复现步骤及脚本索引。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:49:28
-->

# WSL master 非 200 端点修复与验证记录

## 基线与成功判据

- 基线：backend/api 的 `master`；Java V3 已合并，不再同步 V3。
- WSL 工作树：`/home/dev/IdeaProjects/car-monit-backend`、`/home/dev/IdeaProjects/car-monit-api`。
- 成功判据：`body.code == 200`；无 `code` 字段为待定；`body.code != 200` 单独记录。
- 凭据只通过环境变量/GitHub Secrets 注入，仓库只保留占位符。

## 修复过程

1. 在 WSL 修复 GitHub 443 解析并 clone backend/api master。
2. 按 `body.code` 分析各语言 `junit-contract.json`，确认跨语言 artifact 保存了具体 `body`。
3. 用管理员登录态重跑本机 backend 契约与压测，定位非 200 端点。
4. 复查服务日志和源码，逐项修复：
   - backend Java 表名大小写、路径变量、必填参数、生成器 `@PathVariable`、`sys_upgrade_info` fixture。
   - backend Python/Go/Rust/C++ 的 `geometry_copy1` 遗留表引用。
   - backend Go 的 `VEHICLE_MONITOR_BASE_URL` 覆盖。
   - backend C++ 的 `TOKEN__SECRET` 环境变量。
   - api Go blocked self-test 端点统一为 200 空响应。
   - api Go/Rust 统一查询必填参数校验顺序。
   - api Go/Python 测试数据库与 Kafka 配置默认占位。
   - 两仓 workflow 统一注入 token 与下游 baseUrl。
5. 本地提交、推送 master 后，重跑 Java JUnit 矩阵和跨语言 workflow。
6. 收集最终证据并写入本文档。

## 结果

- Java JUnit 云端矩阵：16/16 success（历史最终结果）。
- 重新派发的 Java JUnit 矩阵 16 次：全部 completed/failure，属于本次重跑结果，未改写为 success。
- 跨语言 workflow：
  - 历史严格门禁 run：backend `45031566682`、api `45031576935`，均 completed/failure；baseline success，候选真实 DIFF/NONDET 保留。
  - 本次重跑 run：backend `45048630337`、api `45048639714`，均 completed/failure。
- 本机重新编译打包：16/16 rc=0。
- 本机管理员鉴权复测：契约 302 端点、认证失败 0。
- body.code 判据：success=218，pending_no_code=35，non_200=49。
- 压测：load errors=0，业务 4xx 如实保留。
- 结论：代码修复已推送；云端重跑未通过，不能宣称严格跨语言一致性或 Java 矩阵重跑已成功。

## 复现步骤

1. 在 WSL 进入两个 master 工作树，执行 `git fetch origin && git checkout -B master origin/master`。
2. 启动 MySQL/Redis，导入 `scripts/v3/ops/parity/sql/*.sql`。
3. 运行 `runtime-logs/wsl-local-auth-retest.sh` 做本机管理员鉴权契约与压测。
4. 运行 `analyze-endpoint-code.py`、`analyze-crosslang-code.py` 按 body.code 统计。
5. 运行 `dispatch-java-junit-matrix.py` 与 `dispatch-crosslang-full.py` 派发云端验证。
6. 运行 `collect-java-junit-runs.py`、`collect-crosslang-full.py` 收集结果。
7. 对照 `app.log` 和 `junit-contract.json` 复查非 200 端点。

## 脚本索引

- `wsl-fix-github-clone.sh`：修复 WSL GitHub 解析并 clone master。
- `wsl-sync-master.sh`：同步 WSL master。
- `wsl-local-auth-retest.sh`：管理员鉴权契约与压测。
- `analyze-endpoint-code.py`、`analyze-crosslang-code.py`：body.code 判据统计。
- `summarize-non200.py`：非 200 错误分类。
- `patch-wsl-master-fixes.py` 至 `patch-wsl-master-fixes6.py`：逐批代码修复。
- `repair-wsl-selftest-and-schema.py`：Go 文件边界与 schema fixture 修复。
- `finalize-wsl-fixes.py`、`finalize-wsl-docs.py`：文档生成与收口。
- `dispatch-java-junit-matrix.py`、`dispatch-crosslang-full.py`：云端派发。
- `collect-java-junit-runs.py`、`collect-crosslang-full.py`：云端结果收集。
