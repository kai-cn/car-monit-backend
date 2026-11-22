#!/usr/bin/env python3

"""
@description 历史脚本 patch-oss-native-only.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-oss-native-only.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\bk-parity-oss.yml')

t = p.read_text(encoding='utf-8')

t = t.replace("  # OSS/S3 is not needed by the 2 parity endpoints; native AWS SDK v1 init is unsupported.\n", '')

t = t.replace("  OSS_ENABLE: 'false'\n", '')

t = t.replace('--cmd "\\"$NATIVE\\" --server.port=19902"',

              '--cmd "env OSS_ENABLE=false \\"$NATIVE\\" --server.port=19902"')

p.write_text(t, encoding='utf-8')

import yaml

yaml.safe_load(t)

print('native-only', 'env OSS_ENABLE=false' in t, 'global OSS' not in t)

