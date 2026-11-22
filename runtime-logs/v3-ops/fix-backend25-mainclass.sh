#!/usr/bin/env bash

# @description 历史脚本 fix-backend25-mainclass.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash fix-backend25-mainclass.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

p = Path('/home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/pom.xml')

t = p.read_text(encoding='utf-8')

if '<mainClass>com.ruoyi.RuoYiApplication</mainClass>' not in t:

    t = t.replace('                <configuration>\n                    <buildArgs>',

                  '                <configuration>\n                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>\n                    <buildArgs>', 1)

if 'SLF4JServiceProvider' not in t:

    t = t.replace('                    <buildArgs>\n',

                  '                    <buildArgs>\n                        <buildArg>-H:IncludeResources=META-INF/services/org.slf4j.spi.SLF4JServiceProvider</buildArg>\n', 1)

if 'initialize-at-run-time=org.slf4j' not in t:

    t = t.replace('                    <buildArgs>\n',

                  '                    <buildArgs>\n                        <buildArg>--initialize-at-run-time=org.slf4j,org.apache.commons.logging,org.apache.logging.slf4j,org.apache.logging.log4j</buildArg>\n', 1)

p.write_text(t, encoding='utf-8')

print('FIXED', p)

PY

