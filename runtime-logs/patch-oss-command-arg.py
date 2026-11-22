#!/usr/bin/env python3

"""
@description 历史脚本 patch-oss-command-arg.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-oss-command-arg.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\bk-parity-check.yml')

t = p.read_text(encoding='utf-8')

old = '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902"'

new = '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902 --oss.enable=false"'

assert old in t

p.write_text(t.replace(old, new, 1), encoding='utf-8')

import yaml

yaml.safe_load(p.read_text(encoding='utf-8'))

print('command arg added', '--oss.enable=false' in t)

