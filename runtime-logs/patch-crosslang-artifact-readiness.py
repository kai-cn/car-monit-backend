#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-artifact-readiness.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Fix crosslang workflow artifact paths and readiness checks.

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
