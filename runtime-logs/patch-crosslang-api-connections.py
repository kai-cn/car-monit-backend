#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-api-connections.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-crosslang-api-connections.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- api Go uses APP_ env prefix and configs/config.yaml with GaussDB URL.


- api C++ reads config.yaml host/user and CM_PG_PASSWORD.


- api Rust reads config/application.yaml and APP_SPRING_* env names.


- backend Rust needs Base64 token and APP_DATABASE_* env.


- apply only to candidate workflow steps; no source repo changes.
"""
from pathlib import Path

import yaml



API = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')

BK = Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml')



t = API.read_text(encoding='utf-8')



old_go_env = '''        env:

          CARMONIT_DATABASE_DSN: "root:root@tcp(127.0.0.1:3306)/carmonitdb?charset=utf8mb4&parseTime=True&loc=Local&multiStatements=true"

          CARMONIT_REDIS_ADDR: "127.0.0.1:6379"

          CARMONIT_SERVER_PORT: "19903"

          CARMONIT_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: "postgres"

'''

new_go_env = '''        env:

          APP_SERVER_PORT: "19903"

          APP_REDIS_HOST: "127.0.0.1"

          APP_REDIS_PORT: "6379"

          APP_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: "jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: "postgres"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"

'''

assert old_go_env in t

t = t.replace(old_go_env, new_go_env, 1)

old = '''          cd src/car-monit-api-go

          go build -o bin/car-monit-go ./cmd/api'''

new = '''          cd src/car-monit-api-go

          sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g; s#port: 9901#port: 19903#g' configs/config.yaml

          go build -o bin/car-monit-go ./cmd/api'''

assert old in t

t = t.replace(old, new, 1)



old_cpp = '''        env:

          CM_SERVER_PORT: "19903"

          CM_PG_PASSWORD: "postgres"

          CM_PG_USER: "postgres"

          CM_PG_HOST: "127.0.0.1"

          CM_PG_PORT: "5432"

'''

new_cpp = '''        env:

          CM_SERVER_PORT: "19903"

          CM_PG_PASSWORD: "postgres"

'''

assert old_cpp in t

t = t.replace(old_cpp, new_cpp, 1)

t = t.replace("sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' configs/config.yaml 2>/dev/null || true",

              "sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g; s#port: 9901#port: 19903#g' configs/config.yaml 2>/dev/null || true", 1)



old_rust_env = '''        env:

          APP_DATABASE__URL: "mysql://root:root@127.0.0.1:3306/carmonitdb"

          APP_REDIS__URL: "redis://127.0.0.1:6379"

          APP_SERVER__PORT: "19903"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"

'''

new_rust_env = '''        env:

          APP_SERVER__PORT: "19903"

          APP_REDIS__HOST: "127.0.0.1"

          APP_REDIS__PORT: "6379"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: "jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: "postgres"

          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"

'''

assert old_rust_env in t

t = t.replace(old_rust_env, new_rust_env, 1)

t = t.replace("sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' src-rust/config/application.* 2>/dev/null || true",

              "sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g; s#port: 9901#port: 19903#g' config/application.yaml 2>/dev/null || true", 1)

API.write_text(t, encoding='utf-8')

yaml.safe_load(t)

print('patched', API)



t = BK.read_text(encoding='utf-8')

assert "APP_TOKEN__SECRET: 'Y3Jvc3NsYW5nLWRldGVybWluaXN0aWMtc2VjcmV0LTAxMjM0NTY3ODkw'" in t or 'APP_TOKEN__SECRET' in t

BK.write_text(t, encoding='utf-8')

yaml.safe_load(t)

print('verified', BK)

