#!/usr/bin/env bash

# @description 历史脚本 add-trace-random.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash add-trace-random.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies 按脚本原有逻辑准备环境变量、参数与权限。
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

python3 - <<'PY'

from pathlib import Path

root = Path('/mnt/d/work/IdeaProjects')

needle = '                        <buildArg>--no-fallback</buildArg>'

add = needle + '\n                        <buildArg>--trace-object-instantiation=java.util.Random</buildArg>'

for repo in ('car-monit-backend-jdk21',):

    p = root / repo / 'ruoyi-admin/pom.xml'

    t = p.read_text(encoding='utf-8')

    if 'trace-object-instantiation' in t:

        print('SKIP', p)

    elif needle in t:

        p.write_text(t.replace(needle, add, 1), encoding='utf-8')

        print('PATCHED', p)

    else:

        print('FATAL needle missing', p)

PY

