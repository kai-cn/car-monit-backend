<!--
@description 记录 WSL master 中按 body.code 非 200 端点和服务日志逐语言修复的过程、结果、复现步骤与脚本索引。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
-->

# WSL master 非 200 端点逐语言修复记录

## 基线

- 仅使用 `master`；api/backend 的 Java V3 已合并，不再同步 V3 分支。
- WSL 工作树：`/home/dev/IdeaProjects/car-monit-backend`、`/home/dev/IdeaProjects/car-monit-api`。
- 成功判据：`body.code == 200`；无 `code` 为待定；非 200 单独记录并复查。

## 已确认并修复的代码问题

- backend Java：`FLOW_APPLY_INFO`、`SYS_INDEX_MENU` 表名大小写与 Linux MySQL schema 不一致，已改为小写。
- backend Java：`SysJobLogController` 路径变量 `{configId}` 与方法参数 `jobLogId` 不一致，已改为 `{jobLogId}`。
- backend Java：`BigScreenController.tollGantryFwqList` 的 `type` 必填导致探测请求 500，已改为可选并默认空串。
- backend Java：`GenController.columnList` 缺少 `@PathVariable`，已补充。
- backend Java/schema：新增 `sys_upgrade_info` CI fixture，字段匹配 `SysUpgradeInfoMapper.xml`。
- backend Python/Go/Rust/C++：`geometry_copy1` 遗留表引用已改为现有 `geometry` 表。
- backend Go：新增 `VEHICLE_MONITOR_BASE_URL` 环境变量覆盖，统一下游地址。
- backend C++：`TOKEN__SECRET` 环境变量优先于配置文件默认 token，便于与 Java 签发 token 对齐。
- api Go：blocked self-test 端点由 501 改为与 Java/Rust/Python 一致的 HTTP 200 空响应；保留日志原因。
- api Go/Rust：`/api/v1/unified/{ds}/list` 先校验必填时间参数，再解析数据源，修正与 Java 的校验顺序差异。
- api Go：测试配置默认使用本地 PG 用户和 Kafka 环境变量占位。
- api Python：测试配置缺省 PG 口令使用受控测试占位。
- api C++：blocked self-test 端点不再执行后台任务，改为 200 空响应。
- 两仓 workflow：候选步骤统一注入 `TOKEN__SECRET`、`VEHICLE_MONITOR_BASE_URL`、`APP_VEHICLEMONITOR__BASEURL`。

## 复现步骤

1. 在 WSL 中确认 `/home/dev/IdeaProjects/car-monit-{backend,api}` 为 master 最新提交。
2. 启动 MySQL/Redis 等本地依赖，并按 `scripts/v3/ops/parity/sql/*.sql` 导入 fixture。
3. 重新编译 backend/api master 的 Java 与各语言候选。
4. 按 endpoint 清单运行契约测试，保存 `junit-contract.json`。
5. 用 `runtime-logs/analyze-endpoint-code.py` 统计 success/pending_no_code/non_200。
6. 查看候选 `app.log`，按错误文本定位代码并修复。
7. 重新提交、推送 master，重跑云端 workflow 并汇总 artifact。

## 脚本索引

- `runtime-logs/wsl-fix-github-clone.sh`：修复 WSL GitHub 解析并 clone master。
- `runtime-logs/wsl-sync-master.sh`：同步 WSL master。
- `runtime-logs/analyze-endpoint-code.py`：按 body.code 判据统计。
- `runtime-logs/analyze-crosslang-code.py`：跨语言 body.code 判据统计。
- `runtime-logs/patch-wsl-master-fixes.py` 至 `patch-wsl-master-fixes6.py`：逐批代码修复。
- `runtime-logs/repair-wsl-selftest-and-schema.py`：修复 Go 文件边界与 schema fixture。
- `runtime-logs/finalize-wsl-fixes.py`：最终修复与文档生成。
