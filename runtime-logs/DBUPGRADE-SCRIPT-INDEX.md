<!--
@description 本文件由 AI 辅助编写或维护，用于记录项目实现、验证与交接信息。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
-->

# DB 升级验证 — 复现脚本索引（2026-11-18）

所有脚本位于 `D:/work/runtime-logs/`，token 统一由 `gh_cred.py` 从 `.gh_token_cache` 读取（无账号弹窗、不回显）。

## A. GitHub 云 CI 操作
| 脚本 | 用途 | 典型命令 |
|---|---|---|
| `dispatch-redacted.py` | 派发 workflow_dispatch，不回显 input（凭据安全） | `python dispatch-redacted.py kai-cn/car-monit-api db-upgrade-cloud.yml feature-dbupgrade db_scope=opengauss og_image_source=ga` |
| `dbupgrade-joblog.py` | 查 run 的 job/step 状态与失败步 | `python dbupgrade-joblog.py kai-cn/car-monit-api <run_id>` |
| `wait_dbupgrade.py` | 轮询多个 run 直到完成并报结论 | `python wait_dbupgrade.py kai-cn/car-monit-api:<run_id> <seconds>` |
| `fetch_joblog_cached.py` | 取 job 日志到本地分析（不下载 artifact） | `python fetch_joblog_cached.py <repo> <job_id> <local.log>` |
| `verify_realmig.py` | 从日志确认真实迁移（dump bytes>0）+ fails=0 | `python verify_realmig.py` |
| `cancel_dbupgrade_runs.py` | 取消某仓库全部进行中/排队的 db-upgrade-cloud run | `python cancel_dbupgrade_runs.py <repo>` |
| `list_artifacts.py` | 列 run 的 artifact id/name | `python list_artifacts.py <repo> <run_id>` |
| `get_ref.py` | 查远端分支 SHA | `python get_ref.py <repo> <branch>` |
| `check_remote_scripts.py` | 用 Contents API 校验远端文件字节/CRLF/关键串 | `python check_remote_scripts.py <repo> <branch> <path>` |
| `fetch_file_api.py` | 用 Contents API 取远端文件到本地 | `python fetch_file_api.py <repo> <branch> <path> <local_out>` |

## B. 推送/同步（git HTTPS 不稳时的可靠路径）
| 脚本 | 用途 | 典型命令 |
|---|---|---|
| `push_files_api.py` | Contents API 更新文件（`.sh` 自动 CRLF→LF） | `python push_files_api.py <repo> <branch> <base_dir> <relpath...>` |
| `push_dbupgrade_all_branches_api.py` | 把 4 个 harness 脚本同步到指定仓库多分支 | `python push_dbupgrade_all_branches_api.py api <base_dir> <branch...>` |
| `push_doc12.py` | 把 12 号文档推送到 4 个 api 分支 | `python push_doc12.py` |
| `push-branch-with-credential.py` | git HTTPS 推送分支（缓存 token，可能 connection reset，需重试） | `python push-branch-with-credential.py <repo_dir> <remote_url> <branch>` |
| `push-deployed-branch.py` | 推送 plumbing 生成的远端跟踪 ref | `python push-deployed-branch.py <repo_dir> <local_repo> <remote_url> <branch> <ref>` |
| `deploy_dbupgrade_to_branch.py` | git plumbing 把 harness 部署到分支（`.sh` LF 归一化） | `python deploy_dbupgrade_to_branch.py <api\|backend> <branch>` |
| `deploy_parity_assets_v3.py` | 给 java-V3 分支补 parity 夹具（二进制安全） | `python deploy_parity_assets_v3.py api car-monit-api-java-V3` |

## C. 仓库内交付物（feature-dbupgrade 及 6 分支）
- `.github/workflows/db-upgrade-cloud.yml`：`workflow_dispatch`，inputs `db_scope` / `og_image_source`（dockerhub|ga）/ `linux_runner`；master 上镜像一份才暴露 dispatch。
- `scripts/v3/ops/dbupgrade/db_cell.sh`：单侧容器/夹具/探针/资源采样；支持 `OG_NEW_IMAGES` 覆盖 new 侧镜像；`pick_image` 先本地 inspect。
- `scripts/v3/ops/dbupgrade/db_dump.sh`：`gs_dump` 用位置参数 + uid70 socket（真实迁移的关键修复）。
- `scripts/v3/ops/dbupgrade/gate.py`：0 端点/app 未就绪硬失败门禁。
- `scripts/v3/ops/dbupgrade/report.py`：一致性与资源/性能汇总。
- `docs/v3/review/12-db-upgrade-verification.md`：主文档（结果、踩坑、复现命令）。

## D. 本地诊断（WSL）
| 脚本 | 用途 |
|---|---|
| `probe_gsdump.sh` / `probe_gsdump2.sh` | 在 WSL 现有 opengauss 3.0 容器验证 gs_dump 可用调用形式 |
| `check_line_endings.py` / `check_local_scripts.py` / `validate_ga_changes.py` | 校验本地脚本行尾/结构/GA 改动 |
| `diag_fail.py` / `diag_fail2.py` | 从云端 job 日志定位失败上下文 |
| `extract_reports_only.py` | （早期尝试）下载 artifact 仅解包报告；用户后来要求“不下载 artifact”，已弃用 |

## E. 端到端复现顺序（新会话）
1. 确认 token 缓存：`python gh_cred.py` → `TOKEN_READY`。
2. 确认 workflow 已镜像到 master：`v3-github-actions-dispatch.py ensure-default --template <jdk25>/.github/workflows/db-upgrade-cloud.yml --path .github/workflows/db-upgrade-cloud.yml --repos kai-cn/car-monit-api`。
3. 派发：`python dispatch-redacted.py kai-cn/car-monit-api db-upgrade-cloud.yml feature-dbupgrade db_scope=opengauss og_image_source=ga`。
4. 轮询：`python wait_dbupgrade.py kai-cn/car-monit-api:<run_id> 600`。
5. 查结论：`python dbupgrade-joblog.py kai-cn/car-monit-api <run_id>`；需要详情用 `fetch_joblog_cached.py`。
6. 确认真实迁移：`python verify_realmig.py`（应见 dump bytes≈2,985,813、fails=0）。
7. 若需改脚本：本地改 → `push_files_api.py` 推到各分支（.sh 自动 LF）→ 重新 dispatch。
