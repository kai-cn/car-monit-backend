# 会话交接总览（2026-11-17 收尾）—— 另一会话请从此文件读起

> 本文件是自包含的进度快照；细节分别在下方"文档索引"列出的文件中。
> 用户在本轮最后的明确诉求：记录工作记忆、已办/待办、文档和脚本索引，方便另一会话接续。

## 0. 一句话现状
两仓库（`kai-cn/car-monit-api`、`kai-cn/car-monit-backend`）已 param 化明文、加固全部 workflow、
实测 native/JVM CICD 与 Release 上传、完成云上 native-vs-JVM（jdk17/21/25 × linux/windows）
及跨语言全接口+资源性能对比；**全部 run 结束、文档入库推送、两仓库仍 public（用户决定公开一段时间）**。
只剩少量"技术增强待办"（见 §3）和用户侧凭据真实轮换（F1/F2）。

## 1. 关键决策（别再反复确认）
- 凭据：明文全部参数化；本轮用**测试值**跑 CICD；**用户必须在外部轮换真实凭据**后用
  `D:\work\runtime-logs\update_gh_secrets.py` 更新 Secrets。git 历史不重写（靠轮换使旧值失效）。
- 仓库可见性：**保持 public**，不频繁切换（避免风控）；**无自动改回 private 的看门狗**。
- Runner：保留自托管注册供本地联调；所有 workflow 构建固定云 runner，部署 job 加 owner 守卫，
  PR 永不触达自托管。
- 公开仓库免费 Actions 分钟可绕过私有仓库的账号支付阻断（annotation:
  "recent account payments have failed..."）。

## 2. 已办（DONE）
### 2.1 安全加固与 CICD（11-16）
- 明文参数化：backend/api 主配置、多语言副本、代码硬编码、文档/测试弱口令（api/backend 09 号文档）。
- 全分支 workflow 加固：12 分支/61 处；不变量校验 `verify_remote_hardening.py` PASS。
- GitHub Secrets：api 4 / backend 14（测试值）。独立只读复核无阻断项后推送（SSH:443 + deploy key；HTTPS 被重置）。
- 云 runner 暴露的 6 类既存 CI 缺陷全修（Go 1.26.11、Python 源码编译、backend native AOT+日志目录、
  TOKEN__SECRET 测试夹具、时间炸弹测试、parity Java-only 豁免）。
- 成功 run：api master `43908432856` / pr `43908459793` / native `43905084757`；backend native `43905459051`、ci 全绿。

### 2.2 artifact 体积 bug + Release（11-16~17）
- 根因：`find -perm -u+x -print -quit` 误选 9KB `libjvm.so` shim（artifact 仅 1331B）。
  修为按 artifactId 精确取 `target/<module>`（Windows `.exe`）+ 10MB 下限门禁，推 9 分支。
  api native 重跑 `43910432157` → artifact 120MB zip（内含 368MB 二进制）。
- `native-image-cloud.yml` 加 `release_tag` 输入 + `publish` job（`gh release upload`）。
  tag `v3.0.0-native-test`，run `43912645154` publish success；Release 共 7 资产
  （linux bin+sha / windows exe+sha / standalone / manifest / SHA256SUMS）。
- 本地业务对比（云产物 native vs 同版 JVM）：7/7 端点字节级一致；native 启动 2.65s/305MB vs JVM 16.9s/598MB。
  Windows native CICD `43914875664` build+publish success。

### 2.3 云上全接口 + 资源性能对比（11-17，"一路推到底"轮，最新）
- harness（两仓库 jdk25 分支入库）：`scripts/v3/ops/parity/`（parity_probe.py、parity_compare.py、
  endpoints/api.txt 79 GET、SQL 夹具）；workflow `parity-verify-cloud.yml`（从 pom 自动识别 JDK，
  matrix=platform）+ backend master `crosslang-parity-cloud.yml`。
- api jdk25 linux 79 端点完整对比：native vs JVM 启动 6913→903ms(7.7×)、
  RSS 514.5→309.8MB(1.66×)、延迟 13.58→2.79ms(4.9×)；67 exact + 11 nondet + **1 真差异**
  `/base/sysutil/saveRedis` native 500（SysUtil AOT 反射缺失）。
- api jdk17/21 JVM 基线 79 端点全 success；**Boot4 native 仅 JDK25 可运行**。
- backend jdk25/21/17 JVM 基线 2 端点 success；native 启动 `masterDataSource: null` NPE（Druid AOT 未完成）。
- 跨语言（run `44006210631`）：Java8 903ms/134MB vs **Go 302ms/15.3MB**（快 3×省 8.8×）；
  Rust 启动 rc=1、Python 依赖失败；C#/Kotlin/C++ 无 HTTP 服务无法比。
- 全部 run 完成、11 号文档（方法+结果）两仓库入库推送。

## 3. 待办（TODO，非阻塞）
- [ ] F1/F2 用户外部轮换全部真实凭据 + 用 `update_gh_secrets.py` 更新 Secrets（现为测试值）。
- [ ] H8 backend native Druid 动态数据源 AOT 元数据（masterDataSource NPE）—— 后端 native 化真实阻塞点。
- [ ] H8b api `/base/sysutil/saveRedis` native 500 —— 补 SysUtil 的 `@RegisterReflectionForBinding`。
- [ ] H9 Rust 启动 rc=1 / Python 依赖失败调配；Go 端点路径与 Java8 对齐（端点 MISSING）。
- [ ] C#/Kotlin/C++ 无 HTTP 服务，若需对比要另起服务化改造（用户未明确要求）。

## 4. 2026-11-18 增补
- 新交接文档：`car-monit-api-java-V3` / `car-monit-backend-java-V3` 源分支
  `docs/v3/review/12-session-handoff-20261118.md`
- 新脚本索引：同路径 `12-repro-index-20261118.md`
- 工作记忆：`car-monit-api-java-V3/.workbuddy/memory/2026-11-18.md`
- 本轮关键结果：workflow 全量扫描 `BAD=0`、H9 Go/Python 通过、H8 native 仍阻塞、WSL E_FAIL。

## 5. 文档索引
| 文件 | 内容 |
| --- | --- |
| `D:\work\runtime-logs\公开仓库安全加固-任务清单.md` | 全阶段 A–H 任务清单与状态（**主进度表**） |
| `D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md` | 全部脚本、run id、日志证据索引（H 节为最新轮） |
| `D:\work\runtime-logs\SESSION-HANDOFF.md` | 本文件，自包含快照 |
| 两仓库 `docs/v3/review/09-public-repo-hardening.md` | 凭据轮换清单（无明文） |
| 两仓库 `docs/v3/review/10-public-cicd-native-verification.md` | CICD/native/Windows 完整记录 |
| 两仓库 jdk25 分支 `docs/v3/review/11-cloud-parity-verification.md` | 云全接口对比方法+10 坑点+复现 |
| 两仓库 jdk25 分支 `docs/v3/review/11-results.md` | 云对比实测数字（api/backend/跨语言） |
| `D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\MEMORY.md` | 长期笔记（顶部有交接提示） |
| 同目录 `2026-11-17.md` | 当日工作日志（末节为本轮） |

## 5. 脚本索引（均在 `D:\work\runtime-logs\`，非仓库）
- GitHub API/日志：`gh_api.ps1`、`gh_runs.ps1`、`gh_jobs.ps1`、`monitor_runs.ps1`、`gh_joblog.py`、
  `save_joblog.py`、`save_full_joblog.py`、`download_artifact.py`。
- 凭据/Secrets：`set_gh_secrets.py`、`do_rotate_temp.py`、`update_gh_secrets.py`（轮换后用）、`add_deploy_key.py`。
- workflow 改造（git plumbing）：`harden_workflows.py`、`verify_remote_hardening.py`、
  `fix_artifact_selection.py`、`add_native_release.py`、`scan_branches.py`、`branch_files.py`。
- 本轮对比：`deploy_parity_to_branch.py`（二进制安全部署 harness 到任意分支）、`update_master_file.py`、
  `run_business_compare.sh`、`run_perf_compare.sh`、`checkports.sh`。
- 日志证据：`api-jdk17-fail.log`、`api-jdk21-linux.log`、`bk-jdk17-v3.log`、`bk-jdk25-final.log`、
  `xl-{go,rust,python}.log`、`business-compare-20261117.log`、`perf-compare-20261117.log`。
- 仓库内（jdk25 分支 `scripts/v3/ops/parity/`）：`parity_probe.py`、`parity_compare.py`、`endpoints/*`、`sql/*`。

## 6. 复现入口（另一会话要重跑时）
1. 确认两仓仍 public（`& D:\work\runtime-logs\gh_api.ps1 -Method GET -Uri https://api.github.com/repos/kai-cn/car-monit-api | Select-String private`）。
2. api 完整对比：dispatch `parity-verify-cloud.yml` on `car-monit-api-jdk25`，inputs `platform=linux,repeat=2`。
3. backend：同 workflow on `car-monit-backend-jdk25/21/17`。
4. 跨语言：dispatch backend master `crosslang-parity-cloud.yml`，inputs `langs=all`。
5. 看结果：`& D:\work\runtime-logs\gh_runs.ps1 -Repo ... -PerPage 5`；失败查 `save_full_joblog.py <repo> <job_id> <out>`。
6. 改 harness 后用 `deploy_parity_to_branch.py <api|backend> <branch>` 部署（勿用 text 模式搬 .gz）。

## 6b. CI/CD 中文注释轮（2026-11-17 末，用户要求"所有 CICD 配置/脚本加中文注释"）
- 范围（用户确认）：仅活跃分支 api/backend 的 V3+jdk17/21/25+master（10 分支），
  形式=文件头说明块 + 关键节点行内注释，不改动任何逻辑。
- 工具：`D:\work\runtime-logs\annotate_cicd.py`（基于远端 ref + 内容哈希去重 + YAML 语义不变校验，
  `--dry-run`/`--apply`/`--only`）；`fix_annotation_job_marker.py`（精准删除误把触发器标成 job 的行）。
- 结果：10 分支远端 ref 全部加注释并推送（api 5 + backend 5，各 2 次提交：注释 + 修正）。
  覆盖 117 个 workflow 文件（全部有中文头、YAML 全合法、误标 job 行 0）+ 43 个唯一脚本
  （api V3 工作分支 39 个 + parity 工具等）。
- 修正细节：初次注释把 `workflow_dispatch` 等触发器误标为 job，已用 fix 脚本清零并推送。
- 注意：两个 jdk25 分支在注释期间有另一会话的新提交（api `67de907` SysUtil AOT、backend `5b6793b`
  Druid 修复），已 fetch 最新 tip 后重做注释，未覆盖；这两个 native 待办现已由那会话修复。
- 推送均用 SSH:443 + 对应 deploy key（HTTPS 被网络重置）。

## 7. 约束（务必遵守）
- 凭据值不写入记忆/仓库/文档/日志，仅运行时注入。
- 审阅/修复/复核记录在 `docs/v3/review/`（backend 的 docs 被 .git/info/exclude 忽略，需 `git add -f`）。
- push 前门禁：独立只读复核通过；推送用 SSH:443 + 对应 deploy key（HTTPS 被网络重置）。
- `.codebuddy` 目录是项目数据，不要删除。


## 8. 2026-11-19 收尾交接
- 当前流程：云 runner 快速迭代时先推最小修复；收尾前统一独立审核。
- DB 升级 GA 已全部 success，12 号 DB 文档已补录四分支。
- H9 跨语言已全部 `fails=0`（Java8 基线、Go、Python、Rust）；Rust 根因与 `APP_*` env 修复见当日记忆。
- H8 backend native 仍在快速迭代：Forest 代理字段已批量改为可选注入（`5d10e75f`），
  最终 run `44524395943` 收尾时仍在 native build，需先查结论再决定是否继续。
- 今日工作记忆：`car-monit-api-java-V3/.workbuddy/memory/2026-11-19.md`；
  脚本索引：`公开仓库安全加固-脚本与证据索引.md` J 节。


## 9. 2026-11-19 最后交接
- runtime-logs 已清理凭据后入库 backend 源分支：最终 `a38f49a1`，独立审核 PASS，HTTPS 推送成功。
- H9 已收口：Java8/Go/Python/Rust 均 fails=0；Rust 通过 `APP_DATABASE__*`/`APP_REDIS__*` env 覆盖内嵌配置。
- H8 仍在快速迭代：所有 Forest `*Api` 字段可选；OSS 只禁用 native 进程；AWS 资源方案已撤销。
  当前 run `44544743332` native build 中，结果待确认。
- 下一会话恢复点：先查 `44544743332`；若仍失败，以完整 app log tail 定位下一阻塞，不再盲试 AWS include。


## 10. 2026-11-20 H8 收官
- H8 backend native 已通过，run `44683333011`：2 端点 `status_match=2`、`nondet=2`、**fails=0**。
- 性能：启动 16826→3613 ms，RSS 624.9→395.0 MB，延迟 307.77→6.24 ms。
- 修复要点：Forest 字段可选、SysFileServiceImpl 去 Lombok 全参构造、OssTemplate 初始化降级、AWS 资源 include 撤销。
- H8+H9 均已收口；剩余 F1/F2 用户侧真实凭据轮换。


## 11. 2026-11-20 Java POM 升级收口
- Boot2 master 到 2.7.18；所有 Java 分支 BOM 化依赖治理完成。
- Jedis → Lettuce 完成；所有相关代码与 catch 兼容性修复完成。
- 新增 Java-only workflow，Boot2 分支单独验证；Boot3/Boot4 用 parity workflow。
- 16/16 云 runner run success；证据 `java-upgrade-runs.json`。
- 工作记忆：api-java-V3 `.workbuddy/memory/2026-11-20.md`。
