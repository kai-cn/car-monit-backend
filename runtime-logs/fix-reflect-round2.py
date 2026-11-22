#!/usr/bin/env python3

"""
@description 历史脚本 fix-reflect-round2.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python fix-reflect-round2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

import json

from pathlib import Path



# Boot3 api: create hints from jdk25 file + RedisProperties classes

p = Path(r'D:\work\runtime-logs\api25-reflect.json')

data = json.loads(p.read_text(encoding='utf-8'))

names = [

    'org.springframework.boot.autoconfigure.data.redis.RedisProperties',

    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Pool',

    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Cluster',

    'org.springframework.boot.autoconfigure.data.redis.RedisProperties$Sentinel',

]

existing = {e.get('name') for e in data}

for n in names:

    if n not in existing:

        data.append({'name': n, 'allDeclaredConstructors': True,

                     'allDeclaredMethods': True, 'allDeclaredFields': True})

out = Path(r'D:\work\runtime-logs\boot3-reflect.json')

out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('boot3 reflect', len(data))



# backend: MyBatis Configuration reflection

p = Path(r'D:\work\runtime-logs\bk25-reflect.json')

data = json.loads(p.read_text(encoding='utf-8'))

for n in ['org.apache.ibatis.session.Configuration', 'org.apache.ibatis.builder.xml.XMLConfigBuilder']:

    if not any(e.get('name') == n for e in data):

        data.append({'name': n, 'allDeclaredConstructors': True,

                     'allDeclaredMethods': True, 'allDeclaredFields': True})

p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('backend reflect', len(data))

