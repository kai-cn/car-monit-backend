# 10 公开仓库安全加固 + 云 runner CICD + native 镜像验收（backend 侧）

> 日期：2026-11-16 ~ 11-17；承接 09-public-repo-hardening.md。
> api 侧的完整记录见 api 仓库 `docs/v3/review/10-public-cicd-native-verification.md`，
> 本文档记录 backend 相关事实（两仓库共用同一套加固/实测方法）。

## 1. 全分支 workflow 加固

backend 改造 4 分支（car-monit-backend-jdk17/21/25、master），按统一原则：
- `self-hosted-ci.yml` 去 push 触发 + owner 守卫 + build 固定云 runner；
- `native-image.yml` / `selfhost-canary.yml` job 加 owner 守卫；
- `native-image-cloud.yml` 去 self-hosted 选项 + owner 守卫 + 后续 release_tag 上传（见 §4）。

git plumbing 建提交 + SSH:443 deploy key 快进推送；不变量校验全绿。

## 2. 云 runner 实测与既存缺陷修复

- 临时凭据轮换 + 公开解锁免费 Actions 分钟；canary success。
- backend native 首跑失败：远端分支落后本地提交（缺 `process-aot`/插件 1.1.14/mainClass）
  → 推送本地未推提交 `e23ecbc6`，并补 `/home/ruoyi/logs`（logback AOT 需要）→ native success（run `43905459051`）。
- backend ci 的 py 失败两类：
  1) 移除默认 JWT 密钥后空 key → `ci.yml` 注入 `TOKEN__SECRET` 测试夹具（pydantic env_nested_delimiter='__'，commit 82bc87c）；
  2) 时间炸弹测试（`datetime.now()` 使 8 月起算月份数随挂钟变化）+ 硬编码 `root:root` 断言 → 冻结 now + 去口令断言（commit 156954bd）。
- 最终 backend ci 全 job success。

## 3. native artifact 体积 bug

backend 同样受影响：native-image 产物应位于 `target/ruoyi-admin`，旧 `find -perm -u+x -print -quit`
会命中 9KB shim。统一修复为按 artifactId 精确定位 + 10MB 体积下限，推送 9 分支（含 backend 4 分支）。

## 4. Release 页面下载 native artifact

`native-image-cloud.yml` 加 `release_tag` 输入 + `publish` job（`gh release upload`），推送 backend 4 分支。
backend 未单独做 Release 上传实测（api 侧已端到端验证同一 workflow 模板，run `43912645154` publish success）。

## 5. native vs JVM 对比

backend 侧未单独跑业务对比（会话既有证据显示 backend 端点少：/login、/getInfo、/captchaImage；
api 侧新产物 7 端点对比见 api 仓库 10 号文档 §6）。如需 backend 对比可复用
`v3-compare-business.sh --app backend`。

## 6. 凭据轮换（用户后续必做）

本轮为测试值；公开前必须外部轮换全部真实凭据（清单见 09 号文档），轮换后用
`D:\work\runtime-logs\update_gh_secrets.py backend` 更新 Secrets。

## 7. 状态
两仓库当前 **public**（用户决定公开一段时间，不频繁切换）。git 历史未重写，靠轮换使旧值失效。
