#!/usr/bin/env python3

"""
@description 历史脚本 diff_bodies.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python diff_bodies.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Inspect actual body diffs for the DIFF endpoints."""

import json

from pathlib import Path



out = Path(r'D:\work\runtime-logs\parity-local')

jar = json.loads((out / 'jar.json').read_text(encoding='utf-8'))

nat = json.loads((out / 'native.json').read_text(encoding='utf-8'))

jb = {e['endpoint']: e for e in jar['endpoints']}

nb = {e['endpoint']: e for e in nat['endpoints']}



targets = ['/base/feeGantry/list', '/base/sysutil/saveRedis', '/base/vehicleweight/map']

for t in targets:

    a, b = jb.get(t), nb.get(t)

    print('=' * 70)

    print('ENDPOINT', t)

    print('  jar   status=%s bytes=%s sha=%s' % (a['status'], a['bytes'], a['sha256']))

    print('  native status=%s bytes=%s sha=%s' % (b['status'], b['bytes'], b['sha256']))

    ja, jn = a.get('body', ''), b.get('body', '')

    print('  body identical:', ja == jn)

    if ja != jn:

        # find first divergence

        i = 0

        for i in range(min(len(ja), len(jn))):

            if ja[i] != jn[i]:

                break

        print('  first diff at char', i)

        print('  jar   ...', repr(ja[max(0, i-80):i+120]))

        print('  native...', repr(jn[max(0, i-80):i+120]))

    if b['status'] != a['status']:

        print('  native body tail:', repr(jn[-300:]))

