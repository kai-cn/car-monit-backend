#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-lazy-init.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Add lazy initialization to JUnit JVM startup.

Idea:
- Several api branches start Kafka retry threads from @PostConstruct and touch
  Redis before the context is refreshed, causing false readiness failures.
- spring.main.lazy-initialization defers those beans until endpoints use them.
- This keeps production defaults unchanged; it is scoped to test workflows.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD = '--spring.main.allow-circular-references=true '
NEW = '--spring.main.allow-circular-references=true --spring.main.lazy-initialization=true '

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
