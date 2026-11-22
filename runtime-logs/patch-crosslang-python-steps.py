#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-python-steps.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-crosslang-python-steps.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- requirements.txt uses an editable local package; pip must run inside the


  Python module directory, otherwise '-e .' points at the repo root and fails.


- api Python has no config/application.yml; DB is configured from env.


- keep deterministic TOKEN__SECRET for settings validation.
"""
from pathlib import Path

import yaml



BACKEND = Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml')

API = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')



t = BACKEND.read_text(encoding='utf-8')

old = '''          python3 -m pip install -q -r src/car-monit-py/requirements.txt

          sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' src/car-monit-py/config/application.yml

          (cd src/car-monit-py && TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903 > "$GITHUB_WORKSPACE/app.log" 2>&1) &

'''

new = '''          (cd src/car-monit-py && \\

            python3 -m pip install -q -r requirements.txt && \\

            sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' config/application.yml && \\

            TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\

            python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903 > "$GITHUB_WORKSPACE/app.log" 2>&1) &

'''

assert old in t

BACKEND.write_text(t.replace(old, new, 1), encoding='utf-8')

yaml.safe_load(BACKEND.read_text(encoding='utf-8'))

print('patched', BACKEND)



t = API.read_text(encoding='utf-8')

old = '''          python3 -m pip install -q -r src/car-monit-api-python/requirements.txt

          sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' src/car-monit-api-python/config/application.yml

          (cd src/car-monit-api-python && TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903 > "$GITHUB_WORKSPACE/app.log" 2>&1) &

'''

new = '''          (cd src/car-monit-api-python && \\

            python3 -m pip install -q -r requirements.txt && \\

            TOKEN__SECRET=junit-cloud-secret-deterministic-0123456789abcdef \\

            python3 -m uvicorn app.main:app --host 127.0.0.1 --port 19903 > "$GITHUB_WORKSPACE/app.log" 2>&1) &

'''

assert old in t

API.write_text(t.replace(old, new, 1), encoding='utf-8')

yaml.safe_load(API.read_text(encoding='utf-8'))

print('patched', API)

