#!/usr/bin/env python3

"""
@description 历史脚本 append-java-upgrade-final.py：向交接文档追加结构化记录；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python append-java-upgrade-final.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path



A = {

 r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md': '''



## 2026-11-20 Java POM 升级收口

- api/backend master 升级到 Spring Boot 2 最终版 2.7.18；全部 Java 分支 POM 依赖以 Boot BOM 为版本基准。

- api 所有 Java 分支完成 Jedis → Lettuce（`spring-boot-starter-data-redis` + LettuceClusterClient）。

- 16/16 Java 分支云 runner 验证 success；run id 见 `java-upgrade-runs.json`。

- 认证改为本地 token 缓存 helper，git credential fill/push 不再弹账号选择框。

''',

 r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md': '''



## M. Java POM 升级与凭据免弹窗

- 认证：`gh_cred.py`、`git-credential-ghcached.py`、`configure-gh-credential-helper.py`。

- POM 盘点/迁移：`survey-all-poms.py`、`migrate-api-jedis-to-lettuce.py`、

  `upgrade-poms-boot-managed.py`、`dedupe-redis-starter.py`。

- 本地修复：`local-finalize-pom-comments.py`、`local-fix-dependency-management.py`、

  `local-fix-lettuce-connection.py`、`local-simplify-lettuce-client.py`、

  `local-fix-lombok-jdk25.py`、`local-pin-lombok-dm.py`、`local-fix-mysql-coordinates.py`、

  `local-align-backend-bom.py`、`local-fix-base64-jdk25.py`、

  `local-preserve-jvm-jar.py`、`local-upgrade-compiler-any.py`、

  `local-upgrade-module-compiler.py`、`local-fix-redis-cluster-provider.py`、

  `local-fix-unreachable-catch.py`、`local-add-java-upgrade-workflow.py`。

- 云验证：`dispatch-java-upgrade-verification.py`、`collect-java-upgrade-runs.py`、

  `diagnose-failed-java-upgrade.py`、`redispatch-java-upgrade.py`。

- 新 workflow：`java-upgrade-verify.yml`（Java-only Maven package）。

- 证据：`java-upgrade-runs.json`（16/16 success）、`java-upgrade-logs/`（失败迭代日志）。

''',

 r'D:\work\runtime-logs\SESSION-HANDOFF.md': '''



## 11. 2026-11-20 Java POM 升级收口

- Boot2 master 到 2.7.18；所有 Java 分支 BOM 化依赖治理完成。

- Jedis → Lettuce 完成；所有相关代码与 catch 兼容性修复完成。

- 新增 Java-only workflow，Boot2 分支单独验证；Boot3/Boot4 用 parity workflow。

- 16/16 云 runner run success；证据 `java-upgrade-runs.json`。

- 工作记忆：api-java-V3 `.workbuddy/memory/2026-11-20.md`。

''',

 r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md': '''



## 2026-11-20 Java POM 升级收口

- Boot2 master 2.7.18；Java 分支 POM 依赖治理与 Jedis→Lettuce 完成。

- 16/16 云 runner 验证 success；证据 `java-upgrade-runs.json`。

- Java-only workflow `java-upgrade-verify.yml` 用于 Boot2 分支，避免非 Java job 干扰。

''',

 r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md': '''



## 2026-11-20 Java POM 升级增补

- 认证 helper：`git-credential-ghcached.py`、`configure-gh-credential-helper.py`。

- 验证入口：`dispatch-java-upgrade-verification.py`、`collect-java-upgrade-runs.py`。

- 证据：`java-upgrade-runs.json` 16/16 success；失败迭代日志在 `java-upgrade-logs/`。

- Java-only workflow：`.github/workflows/java-upgrade-verify.yml`。

''',

}



for path_str,text in A.items():

    p=Path(path_str)

    if not p.exists():

        print('MISSING',path_str); continue

    cur=p.read_text(encoding='utf-8')

    marker=text.strip().splitlines()[0]

    if marker in cur:

        print('SKIP',p.name); continue

    p.write_text(cur.rstrip()+'\n'+text,encoding='utf-8')

    print('APPENDED',p.name)

