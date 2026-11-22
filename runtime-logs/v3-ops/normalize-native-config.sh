#!/usr/bin/env bash

# @description 历史脚本 normalize-native-config.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash normalize-native-config.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

set -euo pipefail

python3 - <<'PY'

from pathlib import Path

import json

W = Path('/mnt/d/work/IdeaProjects')

L = Path('/home/dev/IdeaProjects')



# api jdk17: 4-thread experiment did not help; remove

p = L/'car-monit-api-jdk17/pro-business-api/pom.xml'

t = p.read_text(encoding='utf-8').replace('                        <buildArg>-J-XX:ActiveProcessorCount=4</buildArg>\n','')

p.write_text(t, encoding='utf-8')



# backend: remove diagnostic trace, BasicMarker and over-broad logback reflection

for repo in ('car-monit-backend-jdk21','car-monit-backend-jdk17'):

    p = L/repo/'ruoyi-admin/pom.xml'

    t = p.read_text(encoding='utf-8')

    for frag in (

        '                        <buildArg>--trace-object-instantiation=java.util.Random</buildArg>\n',

        '                        <buildArg>--initialize-at-build-time=org.slf4j.helpers.BasicMarker</buildArg>\n',

    ):

        t = t.replace(frag, '')

    p.write_text(t, encoding='utf-8')



    rp = L/repo/'ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json'

    data = json.loads(rp.read_text(encoding='utf-8'))

    keep = [e for e in data if not e['name'].startswith('ch.qos.logback.')]

    keep.extend([

        {'name':'ch.qos.logback.core.encoder.LayoutWrappingEncoder','allDeclaredMethods':True,'allDeclaredConstructors':True},

        {'name':'ch.qos.logback.core.pattern.PatternLayoutEncoderBase','allDeclaredMethods':True,'allDeclaredConstructors':True},

        {'name':'ch.qos.logback.classic.encoder.PatternLayoutEncoder','allDeclaredMethods':True,'allDeclaredConstructors':True},

        {'name':'ch.qos.logback.core.ConsoleAppender','allDeclaredMethods':True,'allDeclaredConstructors':True},

        {'name':'ch.qos.logback.core.rolling.RollingFileAppender','allDeclaredMethods':True,'allDeclaredConstructors':True},

    ])

    rp.write_text(json.dumps(keep, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

PY



# canonical WSL poms -> Windows worktrees

for pair in \

  'car-monit-api-jdk21:pro-business-api/pom.xml' \

  'car-monit-api-jdk17:pro-business-api/pom.xml' \

  'car-monit-backend-jdk21:ruoyi-admin/pom.xml' \

  'car-monit-backend-jdk17:ruoyi-admin/pom.xml'; do

  repo=${pair%%:*}; rel=${pair#*:}

  cp -f "/home/dev/IdeaProjects/$repo/$rel" "/mnt/d/work/IdeaProjects/$repo/$rel"

  echo "SYNCED $repo/$rel"

done

echo NORMALIZED_OK

