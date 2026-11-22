#!/usr/bin/env python3
"""
@description 历史脚本 patch-crosslang-candidates.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-crosslang-candidates.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:

- api Go uses `-config`, not `-c`.

- api Rust binary is `car-monit-api-rust`, not `car-monit-rust`.

- api C++ binary is `car-monit-api`, built in `build-release`.

- backend Python needs DB password and Hengda secret for strict settings.

- backend Rust parse failure comes from malformed APP_DATABASE__POOL values;

  use the exact env names from the already-passing crosslang-parity workflow.
"""
from pathlib import Path
import yaml

BK = Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml')
API = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')

t = BK.read_text(encoding='utf-8')
t = t.replace(
    'TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\\n            python3 -m uvicorn app.main:app',
    'TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\\n            SPRING__DATASOURCE__DRUID__MASTER__PASSWORD=root \\\n            HENGDA__SECRET=pytest-only-hengda-signing-key-4d8e1a6b2f9c0357 \\\n            python3 -m uvicorn app.main:app', 1)
t = t.replace('''        env:
          APP_DATABASE__URL: "mysql://root:root@127.0.0.1:3306/carmonitdb"
          APP_REDIS__URL: "redis://127.0.0.1:6379"
          APP_SERVER__PORT: "19903"
''', '''        env:
          APP_DATABASE__URL: "jdbc:mysql://127.0.0.1:3306/carmonitdb?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=false&allowMultiQueries=true&serverTimezone=GMT%2B8"
          APP_DATABASE__USERNAME: root
          APP_DATABASE__PASSWORD: root
          APP_DATABASE__POOL__MINIDLE: '0'
          APP_DATABASE__POOL__MAXACTIVE: '10'
          APP_DATABASE__POOL__MAXWAIT: '30000'
          APP_REDIS__HOST: 127.0.0.1
          APP_REDIS__PORT: '6379'
          APP_SERVER__PORT: '19903'
''', 1)
BK.write_text(t, encoding='utf-8')
yaml.safe_load(t)
print('patched', BK)

t = API.read_text(encoding='utf-8')
t = t.replace('./bin/car-monit-go -c configs/config.yaml', './bin/car-monit-go -config configs/config.yaml', 1)
t = t.replace('cmake -S . -B build ', 'cmake -S . -B build-release ', 1)
t = t.replace('cmake --build build --parallel 2', 'cmake --build build-release --parallel 2', 1)
t = t.replace('./build/car-monit-cpp --config config', './build-release/car-monit-api --config configs/config.yaml', 1)
t = t.replace('./target/release/car-monit-rust > "$GITHUB_WORKSPACE/app.log"',
              './target/release/car-monit-api-rust > "$GITHUB_WORKSPACE/app.log"', 1)
API.write_text(t, encoding='utf-8')
yaml.safe_load(t)
print('patched', API)
