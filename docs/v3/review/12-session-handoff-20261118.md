# 会话交接（2026-11-18）

## 一句话现状
两仓库公开仓库安全加固、云 runner CICD/Release、api 全矩阵 native/JVM 对比已完成；
本轮完成凭据免弹窗、全分支 workflow 修复、H9 跨语言 Go/Python 对拍；
H8 backend native 与 H9 Rust 仍为技术阻塞，F1/F2 为用户名下真实凭据轮换。

## 关键决策
- 凭据值不写入仓库/文档/日志；API 脚本统一走 `gh_cred.py` 固定账号缓存。
- 两仓库保持 public；workflow 固定云 runner，PR 不触达自托管。
- 业务对比优先云 runner，不下载 artifact；云不可用时才用本地 runner。

## 已办
- Windows 所有 `car-monit-*` 工作树已 fetch；WSL 因 `E_FAIL` 未同步。
- `gh_api.ps1` 等 11 个脚本改为免 GCM 账号选择框。
- 全分支 workflow 扫描 `SCANNED=242 BAD=0`；`verify_remote_hardening.py` PASS。
- H9 run `44219301360`：Java8 基线、Go、Python 均 2 端点 `fails=0`；Rust 仍阻塞。
- H8：JVM 基线恢复 success；native 仍失败。
- api Boot3（jdk21/jdk17 + Mandrel25）79 端点 `fails=0`；api saveRedis 已修复；api jdk25/21/17 Boot4 7 端点字节级一致。

## 待办
1. H8：重跑带完整日志的 backend native run，或 WSL 恢复后本地复现。
2. H9 Rust：排查 sqlx 连接池认证/TLS。
3. WSL 分发 E_FAIL 恢复。
4. F1/F2 真实凭据轮换并用 `update_gh_secrets.py` 更新 Secrets。

## 证据
- workflow 修复日志：`D:\work\runtime-logs\scan-workflows2.log`、`fix-all-invalid2.log`
- H8：`D:\work\runtime-logs\h8-final3.log`、`h8-diag-final.log`（blob 404，缺失）
- H9：`D:\work\runtime-logs\h9-baseline4.log`、`h9-go2.log`、`h9-python4.log`、`h9-rust2.log`
- 任务清单：`D:\work\runtime-logs\公开仓库安全加固-任务清单.md`
- 脚本索引：`docs/v3/review/12-repro-index-20261118.md`
