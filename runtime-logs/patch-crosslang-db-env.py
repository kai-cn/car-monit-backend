#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-db-env.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-crosslang-db-env.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- backend Rust token.secret must be Base64; use a deterministic base64 value.


- api Go/C++/Rust/Python configs contain fixed 192.168.56.10 and gaussdb.


  sed the checked-out configs to 127.0.0.1/postgres and inject the password.


- this affects only CI candidate workspaces, not repository source.
"""
from pathlib import Path

import yaml



BK = Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml')

API = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')



t = BK.read_text(encoding='utf-8')

t = t.replace("          APP_SERVER__PORT: '19903'\n", "          APP_SERVER__PORT: '19903'\n          APP_TOKEN__SECRET: 'Y3Jvc3NsYW5nLWRldGVybWluaXN0aWMtc2VjcmV0LTAxMjM0NTY3ODkw'\n", 1)

BK.write_text(t, encoding='utf-8')

yaml.safe_load(t)

print('patched', BK)



t = API.read_text(encoding='utf-8')

# Python uses pro-business-api resources; inject env instead of editing all config files.

old = '''            TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\

            python3 -m uvicorn app.main:app'''

new = '''            TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\

            SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=postgres \\

            SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL='jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false' \\

            SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=postgres \\

            SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD=postgres \\

            python3 -m uvicorn app.main:app'''

assert old in t

t = t.replace(old, new, 1)

# Go config: replace fixed host/user and inject APP_ env.

old = '''          cd src/car-monit-api-go

          go build -o bin/car-monit-go ./cmd/api'''

new = '''          cd src/car-monit-api-go

          sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g' configs/config.yaml

          go build -o bin/car-monit-go ./cmd/api'''

assert old in t

t = t.replace(old, new, 1)

t = t.replace('          CARMONIT_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"\n',

              '          CARMONIT_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"\n          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"\n          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: "postgres"\n', 1)

# C++ needs CM_PG_PASSWORD and local PG host/user.

old = '''        env:

          CM_SERVER_PORT: "19903"

        run: |

          set -euo pipefail

          cd src-cpp/car-monit-api-cpp'''

new = '''        env:

          CM_SERVER_PORT: "19903"

          CM_PG_PASSWORD: "postgres"

          CM_PG_USER: "postgres"

          CM_PG_HOST: "127.0.0.1"

          CM_PG_PORT: "5432"

        run: |

          set -euo pipefail

          cd src-cpp/car-monit-api-cpp'''

assert old in t

t = t.replace(old, new, 1)

t = t.replace("sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' configs/config.yaml 2>/dev/null || true",

              "sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g' configs/config.yaml 2>/dev/null || true", 1)

# Rust needs local PG and password env.

old = '''          cd src-rust/car-monit-api-rust

          cargo build --release'''

new = '''          cd src-rust/car-monit-api-rust

          sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g' config/application.yaml

          cargo build --release'''

assert old in t

t = t.replace(old, new, 1)

old_env = '''        env:

          APP_DATABASE__URL: "postgres://postgres:postgres@127.0.0.1:5432/RuoYi"

          APP_REDIS__URL: "redis://127.0.0.1:6379"

          APP_SERVER__PORT: "19903"

'''

if old_env in t:

    t = t.replace(old_env, old_env + '          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"\n', 1)

else:

    t = t.replace('          APP_SERVER__PORT: "19903"\n', '          APP_SERVER__PORT: "19903"\n          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: "postgres"\n', 1)

API.write_text(t, encoding='utf-8')

yaml.safe_load(t)

print('patched', API)

