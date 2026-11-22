#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-readiness.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Use TCP readiness instead of /captchaImage for Java JUnit workflow.

Idea:
- several branches return 4xx/3xx or throw application-specific errors on
  /captchaImage before the full endpoint suite starts; this is not a service
  startup failure.
- bash /dev/tcp checks that the HTTP port is accepting connections without
  depending on a business endpoint.
- endpoint correctness is measured separately by the JUnit contract suite.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD = 'if curl -fsS -o /dev/null http://127.0.0.1:19903/captchaImage; then echo "service ready after ${i}s"; exit 0; fi'
NEW = 'if (echo > /dev/tcp/127.0.0.1/19903) >/dev/null 2>&1; then echo "service port ready after ${i}s"; exit 0; fi'

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
