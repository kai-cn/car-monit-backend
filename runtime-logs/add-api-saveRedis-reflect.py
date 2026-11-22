#!/usr/bin/env python3

"""
@description 历史脚本 add-api-saveRedis-reflect.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python add-api-saveRedis-reflect.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import json

from pathlib import Path

p = Path(r'D:\work\runtime-logs\api25-reflect.json')

data = json.loads(p.read_text(encoding='utf-8'))

entry = {

    'name': 'com.ruoyi.base.domain.SysUtil',

    'allDeclaredConstructors': True,

    'allDeclaredMethods': True,

    'allDeclaredFields': True,

}

if not any(e.get('name') == entry['name'] for e in data):

    data.append(entry)

p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('entries', len(data))

