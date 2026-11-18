# DB 大版本升级云验证 — 任务交接文档（2026-11-18 暂停点）

## 1. 任务目标与总体结论
- 目标：在 GitHub 云 runner 上完成 MySQL 8.0→9.7.4、openGauss 3.0.0→7.0.0（先 RC3 后 GA 正式版）升级验证 + 业务一致性 + 资源/性能对比；基于 jdk25 建 `feature-dbupgrade`，同步到 jdk21/jdk17/java-V3 分支。
- **结论：所有核心目标已达成**。MySQL 与 openGauss 均走真实逻辑导出/导入，业务一致性 fails=0；openGauss 用 GA 正式镜像（`opengauss:7.0.0`，build 2397a86f，2026-09-23）验证通过；6 个分支同步升级 PASS。
- 主文档：两仓库 `docs/v3/review/12-db-upgrade-verification.md`（已推送到 api 的 feature-dbupgrade + 3 分支）。

## 2. 分支与提交
- api 仓库 `feature-dbupgrade`：HEAD `751f9b57d2`（文档 GA 版）；workflow `7ce49c9838a3`（master 镜像）；脚本 `c699091316`/`4310e0c69f`（db_cell/db_dump）。
- backend 仓库 `feature-dbupgrade`：HEAD `8afd01e8e2a9f`（脚本同步）；backend 无 openGauss，只用 MySQL。
- 6 个同步分支（api/backend × jdk21/jdk17/java-V3）均已推送最终 harness + 夹具。
- 注意：本机 git HTTPS 推送经常 connection reset，最终用 GitHub **Contents API** 直接 PUT 文件（`push_files_api.py`），`.sh` 已做 CRLF→LF 归一化。

## 3. 已完成的验证（run id 与结论）
| Cell | run id | 结论 |
|---|---|---|
| api × MySQL 8.0.46→9.7.4 | 44268498258（jdk25）、44268999597/44269014488/44269030678 | 79 端点 fails=0，mysqldump 真实迁移 |
| backend × MySQL 8.0.46→9.7.4 | 44213878862/44213891663/44213904528 | 2 端点 fails=0，mysqldump 真实迁移 |
| api × openGauss 3.0→7.0.0-RC3 | 44268498258 等 | 79 端点 fails=0，gs_dump 真实导出 2.99MB |
| api × openGauss 3.0→**7.0.0 GA** | **44283915442**（jdk25） | 79/79 fails=0，GS dump 2,985,813B，版本串 7.0.0 build 2397a86f |
| api jdk21/17/java-V3 GA | 44285673201 / 44285699892 / 44285716860 | **暂停时仍在 in_progress（下载 2.4GB GA 镜像中）**，待恢复后查结论 |

## 4. 暂停时正在运行的任务（恢复后先做）
1. 查 3 个 GA 分支 run 结论：
   `python D:/work/runtime-logs/dbupgrade-joblog.py kai-cn/car-monit-api <run_id>`
   - 若失败，多为 openGauss old 侧启动竞态/GA 下载超时，按 §6 踩坑处理。
   - 若 success，把 run id 补入 12 号文档 §4 GA 小节并推送。
2. 不需要重新 dispatch jdk25（已 PASS）；只在失败时针对性重跑对应分支。

## 5. 关键资产（均在 D:/work/runtime-logs/）
- 凭据免交互：`gh_cred.py`（token 缓存 `.gh_token_cache`），所有脚本读缓存，不再弹 GCM 账号框。
- GitHub API 工具：`dispatch-redacted.py`（派发，不回显口令）、`get_ref.py`、`push_files_api.py`（Contents API PUT，.sh 自动 LF 归一化）、`push_dbupgrade_all_branches_api.py`（批量同步）、`fetch_joblog_cached.py`、`dbupgrade-joblog.py`、`wait_dbupgrade.py`、`verify_realmig.py`、`check_remote_scripts.py`。
- 复现脚本索引：见 `D:/work/runtime-logs/DBUPGRADE-SCRIPT-INDEX.md`（本目录）。
- 本地诊断：`probe_gsdump.sh`/`probe_gsdump2.sh`（在 WSL 现有 opengauss 容器验证 gs_dump 语法）。

## 6. 关键踩坑（完整见 12 号文档 §5）
1. openGauss `gs_dump` 用位置参数（`gs_dump RuoYi -Fp`），**不支持 `-d`**——这是真实迁移能否跑通的决定性修复。
2. GA 镜像从 OBS 下载 2.43GB tar 后 `docker load`，得到 `opengauss:7.0.0`；Docker Hub 的 `latest` 仍是 RC3。
3. `pick_image` 必须先 `docker image inspect`（本地 load 的 GA 镜像无法 pull）。
4. Windows CRLF 经 Contents API 推送会让 Linux bash 报 `set: pipefail`——推送脚本已归一化 LF。
5. openGauss uid70 + socket 免密；管理员 gaussdb；CREATE DATABASE 可见性延迟需重试；库名 RuoYi/ruoyi 都建。
6. 凭据只放 step 级 env 引用 Secret，workflow/job 级 env 会被 GitHub 回显进公开日志。

## 7. 环境状态（暂停时）
- WSL openEuler-24.03-LTS-SP4：此前因拉大镜像 E_FAIL，本次已恢复并在本地现有 opengauss 容器验证 gs_dump。
- 凭据缓存 `.gh_token_cache` 有效；GitHub API 可达；raw.githubusercontent.com 走代理会 10054（用 api.github.com 替代）。
- 两仓库仍 public（用户此前决定，未改回 private）。
