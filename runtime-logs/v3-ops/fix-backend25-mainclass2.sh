#!/usr/bin/env bash

# @description 历史脚本 fix-backend25-mainclass2.sh：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash fix-backend25-mainclass2.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

p = Path('/home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/pom.xml')

t = p.read_text(encoding='utf-8')

needle = '                <artifactId>native-maven-plugin</artifactId>\n                <version>1.1.14</version>\n                <configuration>\n'

block_end = t.find('</configuration>', t.find(needle))

block = t[t.find(needle):block_end]

if '<mainClass>' not in block:

    t = t.replace(needle, needle + '                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>\n', 1)

    p.write_text(t, encoding='utf-8')

    print('PATCHED')

else:

    print('ALREADY')

PY

