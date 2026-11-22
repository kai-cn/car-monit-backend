#!/usr/bin/env python3

"""
@description 历史脚本 fix-two-native-issues.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fix-two-native-issues.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import json

from pathlib import Path



# backend: MyBatis Configuration reflection

p = Path(r'D:\work\runtime-logs\bk25-reflect.json')

data = json.loads(p.read_text(encoding='utf-8'))

entry = {'name': 'com.baomidou.mybatisplus.core.MybatisConfiguration',

         'allDeclaredConstructors': True, 'allDeclaredMethods': True}

if not any(e.get('name') == entry['name'] for e in data):

    data.append(entry)

p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('backend reflect entries', len(data))



# boot3: include MySQL error resource bundle

p = Path(r'D:\work\runtime-logs\api-boot3-module-pom.xml')

t = p.read_text(encoding='utf-8')

needle = '                        <buildArg>--no-fallback</buildArg>'

add = needle + '\n                        <buildArg>-H:IncludeResources=com/mysql/cj/LocalizedErrorMessages.*</buildArg>'

if 'LocalizedErrorMessages' not in t:

    t = t.replace(needle, add, 1)

p.write_text(t, encoding='utf-8')

print('boot3 resource included', 'LocalizedErrorMessages' in t)

