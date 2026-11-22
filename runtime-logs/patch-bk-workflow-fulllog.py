#!/usr/bin/env python3
"""
@description 历史脚本 patch-bk-workflow-fulllog.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python patch-bk-workflow-fulllog.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk-parity-diag.yml')
t = p.read_text(encoding='utf-8')
old = 'grep -E \'ERROR|Caused by|APPLICATION FAILED|Exception|Started .* in|Tomcat started\' "$f" | tail -40 || true'
new = 'tail -n 160 "$f" || true'
print('found', old in t)
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('patched', new in t)
