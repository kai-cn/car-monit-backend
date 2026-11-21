# 09 公开仓库安全加固记录（backend）

> 日期：2026-11-16；决策：参数化 + GitHub Secrets + 用户外部轮换；暂不公开；保留自托管 runner 但加固流程。
> 本目录被 `.git/info/exclude` 忽略，提交时需 `git add -f`。

## 1. 处置内容

### 凭据/地址参数化（工作树已无明文）
- `ruoyi-admin/src/main/resources/application.yml`：Redis host/password、JWT `token.secret`、
  MinIO `oss.*`、恒达 `hengda.secret`、`hendaUrl`、`roadPathUrl` 全部改为 `${ENV:...}` 注入，
  移除公网/内网 IP 与明文密钥。
- `ruoyi-admin/src/main/resources/application-druid.yml`：主库 URL/账号/口令与 Druid 控制台口令改为
  `${SPRING_DATASOURCE_DRUID_MASTER_*}` / `${DRUID_LOGIN_*}` 注入，移除生产库明文。
- `ruoyi-common/.../AliyunSMSUtil.java`：删除 main() 中 3 组阿里云 AccessKey/Secret，改为
  `ALIYUN_SMS_ACCESS_KEY_ID` / `ALIYUN_SMS_ACCESS_KEY_SECRET` 环境变量读取（6 参重载，可编译）。
- `ruoyi-system/.../DownloadTokenService.java`：`LEGACY_DEFAULT_SECRET` 为 denylist 常量（用于拒绝旧默认值），有意保留。
- 多语言镜像配置与文档：`car-monit-py/config/application.yml`、`app/settings.py`、
  `car-monit-rust/config/application.yaml`、`car-monit-go/configs/config.yaml`、`internal/config/config.go`、
  各 `.env.example`、`COMPATIBILITY.md`、`README-MIGRATION.md`、`docs/01-baseline/*` 等，
  明文口令与公网 IP 全部改为环境变量注入/占位符/回环地址。

### Workflow 加固
- `self-hosted-ci.yml`：删除 `push` 触发与 `runner`/AUTO_DEPLOY 输入，仅 `workflow_dispatch`；
  build 固定 `ubuntu-latest`；deploy job 加 `github.repository_owner == 'kai-cn'` 守卫。
- 全仓无 `pull_request_target` / `workflow_run`；`ci.yml` 的 `pull_request` job 全为云 runner。

### GitHub Secrets（repo 级，已写入 14 个）
`CI_MYSQL_PASSWORD`、`CI_INTERNAL_TOKEN`、`CI_EXPORT_SECRET`、`TRAFFIC_API_INTERNAL_TOKEN`、
`EXPORT_DOWNLOAD_SECRET`、`SPRING_DATASOURCE_DRUID_MASTER_PASSWORD`、`JWT_SECRET`、
`OSS_ACCESS_KEY`、`OSS_SECRET_KEY`、`HENDA_SECRET`、`ALIYUN_SMS_ACCESS_KEY_ID`、
`ALIYUN_SMS_ACCESS_KEY_SECRET`、`DRUID_LOGIN_USERNAME`、`DRUID_LOGIN_PASSWORD`。
其中轮换类密钥当前为占位值 `__ROTATE_ME__`，须由用户轮换后更新。
轮换后更新 Secrets 的方法：在 `D:\work\runtime-logs\secret-values.env` 写 `SECRET名=新值`（每行一条，绝不入库），
再运行 `python D:\work\runtime-logs\update_gh_secrets.py backend`（值经 sealed-box 加密传输、不回显、不落盘）。
注意 `CI_INTERNAL_TOKEN`（api 仓）与 `TRAFFIC_API_INTERNAL_TOKEN`（backend 仓）必须设为同一新令牌。

## 2. 上线前必须轮换（用户操作，值不写入本仓库/文档）
| 项 | 环境变量 | 状态 |
| --- | --- | --- |
| 阿里云短信 AccessKey ID/Secret | `ALIYUN_SMS_ACCESS_KEY_ID` / `ALIYUN_SMS_ACCESS_KEY_SECRET` | 旧 key 已在历史，须在阿里云控制台禁用并重建 |
| JWT 签名密钥 | `JWT_SECRET` | 须高强度随机；更新后所有登录态失效 |
| MinIO AccessKey/SecretKey | `OSS_ACCESS_KEY` / `OSS_SECRET_KEY` | 须轮换 |
| 恒达第三方 API secret | `HENDA_SECRET` | 须轮换并同步第三方 |
| MySQL 生产库口令（历史注释中的值） | `SPRING_DATASOURCE_DRUID_MASTER_PASSWORD` | 当前写入的是本地 3307 root 口令，生产须改 |
| Druid 控制台口令 | `DRUID_LOGIN_USERNAME` / `DRUID_LOGIN_PASSWORD` | 须轮换 |
| 导出下载签名密钥 | `EXPORT_DOWNLOAD_SECRET` | 当前为随机生成的有效值，可按需再轮换 |
| 后端↔api 内部令牌 | `TRAFFIC_API_INTERNAL_TOKEN`（与 api 的 `CI_INTERNAL_TOKEN` 一致） | 当前为随机生成值 |

> git 历史未重写：所有已轮换凭据在旧提交中仍可读取。公开仓库相当于公开历史；
> 因此**轮换是公开的前提**，而非可选项。轮换后旧值即失效，历史残留不构成可利用风险。
>
> **暴露面实测（2026-11-16）**：本仓库几乎所有远端分支（`master`、`car-monit-backend-jdk17/21/25`、
> `car-monit-cpp-local`、`car-monit-go-V2`、`car-monit-py-V2`、`car-monit-rust-V2`、`qoder/car-monit-cpp`）
> 的当前 tip 均含 henda / MinIO / Druid / 3 组阿里云 AK / 公网 IP 明文（仅 `main` 干净）。
> 本次参数化只落在 `car-monit-backend-java-V3` 工作分支。公开前**必须**完成上表全部轮换——
> 轮换后这些跨分支、跨历史的旧值同时失效。若需连分支 tip 也清除（新增提交、非历史重写），可另行处理。

## 3. 非阻断遗留（按运维节奏处理，不影响 push/CI）
- `car-monit-go/configs/config.yaml` 的 `root:root` 为本地 MySQL 默认值，生产由 `CARMONIT_DATABASE_DSN` 覆盖。
- `PARSITY_USER/PARITY_PASSWORD`、`KUBE_CONFIG` 两个 Secret 未创建：只被手动 dispatch job 引用，push 不触发；
  若后续手动跑 parity/K8s 部署需补建。

## 4. 复核
独立只读会话复核结论：**无阻断项，可 push 触发 CI**（详见会话记录）。
