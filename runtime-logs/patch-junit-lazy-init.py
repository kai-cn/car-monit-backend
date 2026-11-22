#!/usr/bin/env python3
"""
@description 历史脚本 patch-junit-lazy-init.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-junit-lazy-init.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

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
