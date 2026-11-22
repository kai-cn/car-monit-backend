#!/usr/bin/env python3
"""
@description 历史脚本 fix-go-line-endings.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python fix-go-line-endings.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\car-monit-go\internal\modules\quartz\tasks_test.go')
data = p.read_bytes().replace(b'\r\n', b'\n')
p.write_bytes(data)
print('LF_ONLY', b'\r\n' not in p.read_bytes())
