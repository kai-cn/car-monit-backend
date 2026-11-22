<!--
@description 记录 endpoint body.code 判据下的本机复测、非 200 端点复查、代码修复、跨语言 JSON 记录与复现步骤。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# Endpoint body.code 判据复测与缺陷修复记录

## 判定口径

- `body` JSON 中 `code == 200`：请求成功。
- `body` 中没有 `code` 字段：结果待定。
- `body.code != 200`：单独记录并复查。
- 统计时间：2026-11-22 23:45:04

## 本机复测结果

- 修复前：success=217，pending_no_code=35，non_200=50。
- 单独复查端点：`/base/geometry/syncAllGeometry`。
- 修复前返回：`status=200`，`body.code=500`，错误为 `Table carmonitdb.geometry_copy1 doesn’t exist`。
- 复查结论：`ruoyi-system/src/main/resources/mapper/base/GeometryMapper.xml` 引用了当前 schema 中不存在的遗留表 `geometry_copy1`，属于代码缺陷。
- 代码修复：将 `syncAllGeometry` 改为仅基于现有 `geometry` 表的幂等查询；无待补齐区段时返回空集合，端点返回 `code=200`。
- 修复后：重新编译 backend master 成功；契约 302/302；`success=218`，`pending_no_code=35`，`non_200=49`；目标端点 `body.code=200`。
- 压测：715 请求，707 ok，0 传输错误，8 个业务 4xx，0 个 5xx。

## 跨语言 JSON 记录

跨语言 artifact 中的 `junit-contract.json` 确实保存了每个 endpoint 的具体 `body`，可按同一判据离线复查。

| source | endpoints | body_recorded | success | pending_no_code | non_200 |
| --- | ---: | ---: | ---: | ---: | ---: |
| api/baseline/junit-contract.json | 79 | 61 | 36 | 41 | 2 |
| api/cpp/out/junit-contract.json | 79 | 65 | 5 | 72 | 2 |
| api/go/out/junit-contract.json | 79 | 76 | 41 | 23 | 15 |
| api/python/out/junit-contract.json | 79 | 66 | 4 | 73 | 2 |
| api/rust/out/junit-contract.json | 79 | 63 | 36 | 40 | 3 |
| backend/baseline/junit-contract.json | 302 | 295 | 220 | 31 | 51 |
| backend/cpp/out/junit-contract.json | 302 | 301 | 1 | 1 | 300 |
| backend/go/out/junit-contract.json | 302 | 299 | 234 | 37 | 31 |
| backend/python/out/junit-contract.json | 302 | 300 | 2 | 2 | 298 |
| backend/rust/out/junit-contract.json | 302 | 298 | 231 | 38 | 33 |

## 复现步骤

1. WSL 启动 `mysql_wsl` 与 `redis_wsl`，确认 `carmonitdb` 有种子数据。
2. 执行 `runtime-logs/rebuild-fixed-backend-master.sh` 重新编译 backend master。
3. 设置 `CARMONIT_ADMIN_USER/CARMONIT_ADMIN_PASSWORD` 后执行 `runtime-logs/wsl-local-auth-retest.sh`。
4. 执行 `runtime-logs/sync-auth-evidence.py` 同步证据。
5. 执行 `runtime-logs/analyze-endpoint-code.py <junit-contract.json> <out.json>` 按新判据统计。
6. 查看 `endpoint-code-analysis.json` 中 `/base/geometry/syncAllGeometry` 的 `code` 与 `verdict`。

## 脚本索引

| 脚本 | 用途 |
| --- | --- |
| `runtime-logs/analyze-endpoint-code.py` | 单个契约 JSON 的 body.code 判据统计 |
| `runtime-logs/analyze-crosslang-code.py` | 跨语言契约 JSON 的 body.code 判据统计 |
| `runtime-logs/check-geometry-tables.sh` | 检查 geometry 表与遗留表 |
| `runtime-logs/rebuild-fixed-backend-master.sh` | 重建修复后的 jar |
| `runtime-logs/wsl-local-auth-retest.sh` | 本机管理员鉴权契约与压测复测 |
| `runtime-logs/sync-auth-evidence.py` | 同步 WSL 证据到 canonical runtime-logs |
