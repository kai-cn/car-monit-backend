#!/usr/bin/env python3
"""
@description 为跨语言 workflow 的 api 候选注入本地 PostgreSQL/Redis 配置，消除 gaussdb 凭据错误。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/patch-crosslang-api-local-db.py
@dependencies backend/api 两仓库 master 工作树中的 crosslang-full-parity-cloud.yml。
"""
from pathlib import Path

FILES = [
    Path('/home/dev/IdeaProjects/car-monit-backend/.github/workflows/crosslang-full-parity-cloud.yml'),
    Path('/home/dev/IdeaProjects/car-monit-api/.github/workflows/crosslang-full-parity-cloud.yml'),
]
OLD_PY = """          TOKEN__SECRET: junit-cloud-secret-deterministic-0123456789abcdef
          VEHICLE_MONITOR_BASE_URL: \"http://127.0.0.1:9902\""" 
NEW_PY = """          TOKEN__SECRET: junit-cloud-secret-deterministic-0123456789abcdef
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: \"jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false\"
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: postgres
          VEHICLE_MONITOR_BASE_URL: \"http://127.0.0.1:9902\""" 
OLD_GO = """          CARMONIT_TOKEN_SECRET: \"junit-cloud-secret-deterministic-0123456789abcdef\""" 
NEW_GO = """          CARMONIT_TOKEN_SECRET: \"junit-cloud-secret-deterministic-0123456789abcdef\"
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: \"jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false\"
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: postgres"""
OLD_CPP = """          CM_PG_PASSWORD: \"postgres\"""" 
NEW_CPP = """          CM_PG_PASSWORD: \"postgres\"
          CM_PG_USER: postgres
          CM_PG_HOST: 127.0.0.1
          CM_PG_PORT: '5432'"""

for p in FILES:
    t = p.read_text(encoding='utf-8')
    if OLD_PY in t:
        t = t.replace(OLD_PY, NEW_PY, 1)
    elif 'SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres\n          VEHICLE_MONITOR_BASE_URL' not in t:
        print('MISS_PY', p)
    if OLD_GO in t:
        t = t.replace(OLD_GO, NEW_GO, 1)
    elif 'APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres' not in t:
        print('MISS_GO', p)
    if OLD_CPP in t:
        t = t.replace(OLD_CPP, NEW_CPP, 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
