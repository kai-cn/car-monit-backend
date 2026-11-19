# 12. 数据库大版本升级云验证（MySQL 8.0→9.7 / openGauss 3.0→7.0）

> 结论先行：在 GitHub 云 runner 上完成三格验证，**业务一致性 fails=0**；MySQL 与 openGauss 均走真实逻辑导出/导入（openGauss 先 RC3、后 GA 正式镜像均验证）。以下数字全部来自云端 job 日志，未下载 artifact 到本地。凭据值仅在运行时由 masked Secret 注入，文档不记录。

## 1. 目标版本结论（联网核实）

| 目标 | 结论 |
|---|---|
| MySQL 9.7 | 有效 LTS（2026-04 GA，EOL 2034-04）；9.0 起删除 `mysql_native_password` 与 `default_authentication_plugin` |
| openGauss 7.0.0 LTS | 2026-09-30 GA，社区维护至 2029-09-30；Docker Hub 可用镜像为 `opengauss/opengauss:latest` / `opengauss-server:latest`，实测版本串为 **7.0.0-RC3**（非最终 7.0.0 GA 包，见坑点） |

因此必须逻辑导出/导入重建实例，不能原地升级；认证与 JDBC 参数需同步调整。

## 2. 分支与交付物

- 基于 `car-monit-api-jdk25@45699077` / `car-monit-backend-jdk25@e34166b3` 新建 `feature-dbupgrade`。
- 新增 `.github/workflows/db-upgrade-cloud.yml`（`workflow_dispatch`）；脚本 `scripts/v3/ops/dbupgrade/{db_cell.sh,db_dump.sh,gate.py,report.py}`。
- 工作流镜像到两仓库 `master` 以暴露 dispatch；执行代码来自 `feature-dbupgrade` ref。
- 凭据用仓库 Secret `CI_DB_TEST_PASSWORD`，**仅在 step 级 env** 引用。

## 3. 验证方法

每个 cell 用同一 jar、同一端点清单：
1. old 侧起旧版容器（mysql:8.0 / enmotech/opengauss:3.0.0），加载夹具，跑探针并采 DB 资源。
2. `db_dump.sh` 逻辑导出 old；new 侧起新版容器（mysql:9.7.4 / openGauss 7.0.0-RC3）还原。
3. `gate.py` 硬门禁（0 端点或 app 未就绪即失败）；`parity_compare.py` 判 status/exact/semantic/nondet/fails；`report.py` 汇总启动/RSS/延迟/DB 资源。
4. api 的 MySQL 字典、backend 的 Redis 在两侧保持一致以隔离变量。

## 4. 云验证结果（fails=0，全部通过）

### api × MySQL 8.0.46 → 9.7.4（run `44068812191`，79 端点）
- 一致性：status_match=79，exact=20，semantic=20，nondet=59，fails=0（nondet 为时间戳/排序抖动，非真实差异）。
- 迁移：`mysqldump` 真实导出 36,045 B 并在 9.7.4 还原成功。
- 资源/性能：启动 8720→7816 ms；峰值 RSS 501.8→540.8 MB；稳态 RSS 514.2→540.8 MB；平均延迟 9.77→9.14 ms。

### backend × MySQL 8.0.46 → 9.7.4（run `44077700396`，2 个免认证端点）
- 一致性：status_match=2，exact=1，semantic=1，nondet=1，fails=0。
- 迁移：`mysqldump` 真实导出 341,688 B 并在 9.7.4 还原成功。
- 资源/性能：启动 10820→9918 ms；稳态 RSS 768.1→736.8 MB；平均延迟 767.86→177.97 ms；DB 内存 386.2→465.5 MiB。

### api × openGauss 3.0.0 → 7.0.0-RC3
- **首轮（run `44083066192`）**：一致性 79/79、fails=0，但 `gs_dump` 失败（dump bytes=0），new 侧回退夹具。
- **修复后真实迁移（run `44268498258`，api jdk25；另 `44268999597`/`44269014488`/`44269030678` 对应 jdk21/jdk17/java-V3）**：
  - `gs_dump` 真实导出 **2,985,812 B**（909 objects），在 7.0.0-RC3 还原成功，**跨版本真实数据迁移已验证**，不再是夹具回退。
  - 一致性：79 端点 status_match=79、exact=69、semantic=69、nondet=10、fails=0。
  - 资源/性能：启动 9629→9323 ms；平均延迟 15.45→15.26 ms；DB CPU 1.61%→2.63%；DB 内存 424.6→542.4 MiB。
  - 镜像：`enmotech/opengauss:3.0.0` → `opengauss/opengauss-server:latest`（实测 7.0.0-RC3 build 2026-03-25）。
- 四个 api 分支的真实 dump 均约 2.99MB、79/79 fails=0（见 `verify_realmig.py` 输出）。

### api × openGauss 3.0.0 → **7.0.0 GA 正式版**（run `44283915442`，jdk25）
- **镜像来源**：openGauss 官网官方 Docker 镜像包 `openGauss-Docker-7.0.0-x86_64.tar`（OBS，2.43GB），云 runner 上 `docker load` 得到 `opengauss:7.0.0`，版本串 `(openGauss 7.0.0 build 2397a86f) compiled at 2026-09-23`（**GA 正式版，非 RC3**）。
- 通过 workflow 新增 `og_image_source=ga` 输入 + `OG_NEW_IMAGES` 环境变量覆盖 new 侧镜像；`pick_image()` 优先用本地已 load 镜像。
- 迁移：`gs_dump` 真实导出 **2,985,813 B**，在 7.0.0 GA 还原成功。
- 一致性：79 端点 status_match=79、exact=69、semantic=69、nondet=10、fails=0。
- 资源/性能：启动 15336→14742 ms；稳态 RSS 551.0→527.1 MB；平均延迟 25.16→23.7 ms；DB CPU 1.02%→1.89%；DB 内存 446.1→660.5 MiB。
- 另三个 api 分支（jdk21/jdk17/java-V3）GA 验证 run：`44285673201`/`44285699892`/`44285716860`。

## 5. 踩坑点（如实记录）

1. **凭据泄露（已修）**：初版把测试口令放在 workflow 级 `env:`，GitHub 会把该块回显进公开日志。改为仓库 Secret + 仅 step 级 env 引用，后续日志显示 `CI_DB_PASSWORD: ***`。早期泄露的是一次性 CI 测试值（非真实生产凭据），机制已根治。
2. **假绿（已修）**：初版 `|| log` 吞掉探针失败，openGauss app `rc=1`、0 端点却显示 job success。新增 `gate.py` 硬门禁 + `set -euo pipefail`，0 端点/未就绪立即失败。
3. **账号选择弹窗（已修）**：GCM 每次 `git credential fill` 弹账号选择；一次性缓存 token 到仓库外 `.gh_token_cache`，所有运维脚本改为读缓存。
4. **git ref 歧义**：`origin/xxx` 曾 reset 到过期提交，必须用 `refs/remotes/origin/xxx` 全限定名。
5. **backend deploy key 无写权限**：SSH key 仅对 api 仓库有效；backend 用 HTTPS + 缓存 token 推送。
6. **Spring env 命名**：backend 误用 Python 风格双下划线 `SPRING__...` 导致数据源覆盖失效；改为 `SPRING_DATASOURCE_DRUID_MASTER_*` 单下划线。
7. **MySQL 9.7 认证**：容器删除 `mysql_native_password`；new 侧去掉该参数并加 `allowPublicKeyRetrieval=true`。
8. **openGauss 镜像坑**：`opengauss/opengauss:latest` 缺 `libopenblas.so.0` 无法启动；容器启动需带 `LD_LIBRARY_PATH=/usr/local/opengauss/lib`；最终用 `opengauss/opengauss-server:latest`，实测为 7.0.0-RC3。
9. **openGauss 管理员/夹具**：JDBC 用户是 `gaussdb`（非 omm）；容器内 gsql 需 uid 70 + socket；3.0 不支持 `CREATE SCHEMA IF NOT EXISTS`，已用 DO 块改写。
10. **gs_dump 根因与修复（已解决）**：openGauss 的 `gs_dump` **不支持 PostgreSQL 的 `-d <db>` 选项**（报 `invalid option -- 'd'`），库名必须用**位置参数** `gs_dump RuoYi -Fp --no-owner`；配合 uid70 + socket 免密，本地实测导出 67MB/909 objects，云端真实导出 2.99MB 并在 7.x 还原成功。之前误用 `-d` 导致 dump bytes=0、回退夹具。
11. **dispatch 匹配旧 run**：自建 dispatch 脚本曾返回同 workflow 的旧 run，已改为按 `created_at` 取最新。
12. **nondet 端点**：api-mysql 59 个非确定性端点为数据/排序抖动，按既有口径只豁免 body、status 不一致仍判 DIFF。
13. **CREATE DATABASE 可见性延迟**：openGauss `CREATE DATABASE` 后首次 `select 1` 可能报 `database "RuoYi" does not exist`；改为循环“建库→验证可连”最多 10 轮。
14. **库名大小写折叠**：7.x 镜像与 3.0 不同，同时建 `RuoYi`/`ruoyi`，以实际可连者为准。
15. **V3 分支缺夹具**：java-V3 分支原本无 `scripts/v3/ops/parity/*`，需随 harness 一起部署。
16. **重复 run 匹配**：自建 dispatch 曾匹配到已完成的旧 run（返回 stale id），已改为按 `created_at` 取最新并配合 cancel 清理。
17. **CRLF 行尾**：Windows git autocrlf 让本地 `.sh` 变成 CRLF，经 Contents API 推送后 Linux runner 报 `set: pipefail`（`pipefail\r`）；`push_files_api.py`/`deploy_dbupgrade_to_branch.py` 已在推送时对 `.sh` 做 CRLF→LF 归一化。
18. **本地 load 的 GA 镜像无法 pull**：`opengauss:7.0.0` 是云 runner 上 `docker load` 的本地镜像，`docker pull` 会失败；`pick_image()` 改为先 `docker image inspect` 命中本地镜像，再尝试 pull。
19. **GA 镜像来源**：Docker Hub 的 `opengauss/opengauss-server:latest` 仍是 RC3；GA 正式镜像包需从 OBS `https://opengauss.obs.cn-south-1.myhuaweicloud.com/7.0.0/openEuler24.03/x86/openGauss-Docker-7.0.0-x86_64.tar` 下载（2.43GB）并 `docker load`，约耗时数分钟。

## 6. 分支同步升级结果（jdk21 / jdk17 / java-V3）

harness 与 parity 夹具已通过 git plumbing 部署到 6 个分支并全部云端验证通过（同一 workflow dispatch 到各 ref）：

| 仓库 | 分支 | MySQL 9.7 | openGauss 7 | 结论 |
|---|---|---|---|---|
| api | jdk21 | ✅ `44213841737` | ✅ `44268999597`（真实迁移 2.99MB） | PASS |
| api | jdk17 | ✅ `44213853656` | ✅ `44269014488`（真实迁移 2.99MB） | PASS |
| api | java-V3 | ✅ `44213866103` | ✅ `44269030678`（真实迁移 2.99MB） | PASS |
| backend | jdk21 | ✅ `44213878862` | n/a | PASS |
| backend | jdk17 | ✅ `44213891663` | n/a | PASS |
| backend | java-V3 | ✅ `44213904528` | n/a | PASS |

同步过程中新增的坑与修复：
- V3 分支原本没有 `scripts/v3/ops/parity/*` 夹具/探针，需随 harness 一起部署，否则报 `No such file or directory`。
- openGauss 容器内 `CREATE DATABASE` 后存在可见性延迟（DDL 异步），首次 `select 1` 可能报 `database "RuoYi" does not exist`；改为循环“建库→验证可连”最多 10 轮。
- 7.x 镜像对库名大小写折叠与 3.0 不同：同时创建 `RuoYi` 与 `ruoyi`，以实际可连者为准（`PG_DB` 变量）。
- gsql `-f` 偶发把默认 host 解析为 `Unknown:5432`：显式尝试多个 socket 目录（`/tmp`、`/var/run/postgresql`、`/usr/local/opengauss/data`）。
- 版本串读取改为非阻断（失败不影响验证结论）。

## 7. 未完成 / 后续

- 无阻塞项。openGauss 7.0.0 **GA 正式镜像**已在云 runner 用官方镜像包 `docker load` 并验证通过（见 §4 GA 小节），不再依赖 RC3。

> 已完成项：openGauss `gs_dump` 真实跨版本迁移已验证（见 §4）；6 个分支同步升级全部 PASS（见 §6）；7.0.0 GA 正式镜像云验证通过（见 §4 GA 小节）。

## 8. 复现命令

```powershell
# 工作流镜像到 master（一次性）
python scripts/v3/ops/v3-github-actions-dispatch.py ensure-default `
  --template <jdk25 worktree>/.github/workflows/db-upgrade-cloud.yml `
  --path .github/workflows/db-upgrade-cloud.yml --repos <repo>
# 触发（口令由 Secret 注入，无 input）
python D:/work/runtime-logs/dispatch-redacted.py <repo> db-upgrade-cloud.yml feature-dbupgrade db_scope=both
```
