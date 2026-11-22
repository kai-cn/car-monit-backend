#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-junit-runtime.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Relax generated JUnit runtime for full endpoint + load verification.

Idea:
- Full endpoint list contains file download endpoints whose response can exceed
  30 seconds on cold cache; use 60 seconds by default.
- Exclude Kafka auto-configuration in the JVM-under-test to avoid unavailable
  external Kafka topics blocking local/cloud endpoint verification.
- Keep a single source of truth in both repo workflows.
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\java-junit-load-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\java-junit-load-cloud.yml'),
]
OLD = '--spring.main.allow-circular-references=true > out/app.log 2>&1 &'
NEW = ('--spring.main.allow-circular-references=true '
       '--spring.autoconfigure.exclude=org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration '
       '> out/app.log 2>&1 &')

for p in FILES:
    t = p.read_text(encoding='utf-8')
    assert OLD in t, p
    p.write_text(t.replace(OLD, NEW, 1), encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
