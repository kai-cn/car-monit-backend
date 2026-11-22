#!/usr/bin/env python3
"""
@description 历史脚本 add-backend-druid-reflect.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python add-backend-druid-reflect.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
import json
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk25-reflect.json')
data = json.loads(p.read_text(encoding='utf-8'))
names = [
    'com.ruoyi.framework.config.properties.DruidProperties',
    'com.ruoyi.framework.config.DruidConfig',
    'com.ruoyi.framework.datasource.DynamicDataSource',
    'com.alibaba.druid.pool.DruidDataSource',
    'com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceBuilder',
]
existing = {e.get('name') for e in data}
for n in names:
    if n not in existing:
        data.append({'name': n, 'allDeclaredConstructors': True,
                     'allDeclaredMethods': True, 'allDeclaredFields': True})
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('entries', len(data))
