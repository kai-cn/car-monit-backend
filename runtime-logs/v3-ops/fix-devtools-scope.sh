#!/usr/bin/env bash

# @description 历史脚本 fix-devtools-scope.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash fix-devtools-scope.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

for root in (Path('/home/dev/IdeaProjects'), Path('/mnt/d/work/IdeaProjects')):

    for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):

        p = root/repo/'ruoyi-admin/pom.xml'

        t = p.read_text(encoding='utf-8')

        old = '            <artifactId>spring-boot-devtools</artifactId>\n            <optional>true</optional>'

        new = '            <artifactId>spring-boot-devtools</artifactId>\n            <scope>provided</scope>'

        if old in t:

            p.write_text(t.replace(old,new,1),encoding='utf-8')

            print('PATCHED',p)

        elif '<scope>provided</scope>' in t:

            print('SKIP',p)

        else:

            print('NOT_FOUND',p)

PY

