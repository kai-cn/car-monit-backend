#!/usr/bin/env python3
"""
@description 历史脚本 patch-junit-runtime.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-junit-runtime.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

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
