#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-logdir.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-crosslang-logdir.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')

t = p.read_text(encoding='utf-8')

needle = '          docker run -d --name rd -p 6379:6379 redis:7-alpine\n'

add = needle + '          sudo mkdir -p /home/ruoyi/logs /home/ruoyi/uploadPath\n          sudo chown -R "$(id -u):$(id -g)" /home/ruoyi\n'

print('sites', t.count(needle))

t = t.replace(needle, add)

p.write_text(t, encoding='utf-8')

print('patched', t.count('sudo mkdir -p /home/ruoyi/logs'))

