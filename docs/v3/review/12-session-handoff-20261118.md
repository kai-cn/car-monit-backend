# 12. 会话交接（2026-11-18 起，含 11-20 Java POM 升级收口）

## 11-18 基线
- workflow 全量扫描 `BAD=0`；H9 Go/Python 通过；H8 后续已在 11-20 收官。
- 工作记忆与脚本索引位于 `D:/work/runtime-logs/`。

## 2026-11-20 Java POM 升级收口
- api/backend master 升级到 Spring Boot 2 最终版 2.7.18；全部 Java 分支 POM 依赖以 Boot BOM 为版本基准。
- api 所有 Java 分支完成 Jedis → Lettuce（`spring-boot-starter-data-redis` + LettuceClusterClient）。
- 新增 Java-only workflow `java-upgrade-verify.yml`，避免 Boot2 分支被 Python/DB fixture/native clean 等非 Java job 阻断。
- 16/16 Java 分支云 runner run success，证据 `D:/work/runtime-logs/java-upgrade-runs.json`。
- GitHub 认证改为本地 token 缓存 helper，git credential fill/push 不再弹账号选择框。
- 当日工作记忆：`.workbuddy/memory/2026-11-20.md`。
