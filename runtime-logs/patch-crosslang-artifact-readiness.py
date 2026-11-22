#!/usr/bin/env python3
"""
@description 历史脚本 patch-crosslang-artifact-readiness.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-crosslang-artifact-readiness.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:

- upload-artifact `path` is newline-delimited; comma-separated values are treated

  as a single path and produce no artifact.

- readiness based on /captchaImage depends on business behavior and delays runs.

  TCP readiness is stable and endpoint assertions are done by JUnit separately.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
OLD_PATH = 'path: out/junit-contract.json,out/junit-load.json,out/*.log'
NEW_PATH = ('path: |\n            out/junit-contract.json\n            out/junit-load.json\n'
            '            out/*.log')
OLD_READY = 'for i in $(seq 1 180); do curl -fsS -o /dev/null http://127.0.0.1:19903/captchaImage && break; sleep 1; done'
NEW_READY = 'for i in $(seq 1 180); do (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1 && break; sleep 1; done'

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD_PATH in t, p
    t = t.replace(OLD_PATH, NEW_PATH, 1)
    t = t.replace(OLD_READY, NEW_READY)
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
