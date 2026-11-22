#!/usr/bin/env python3
"""
@description 历史脚本 patch-crosslang-matrix-quotes.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-crosslang-matrix-quotes.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path
import yaml

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),
    Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),
]
for p in FILES:
    t = p.read_text(encoding='utf-8')
    for lang in ('python', 'go', 'cpp', 'rust'):
        t = t.replace('matrix.lang == ' + lang, "matrix.lang == '" + lang + "'")
    p.write_text(t, encoding='utf-8')
    yaml.safe_load(t)
    print('patched', p)
