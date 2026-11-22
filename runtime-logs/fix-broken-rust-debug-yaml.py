#!/usr/bin/env python3

"""
@description 历史脚本 fix-broken-rust-debug-yaml.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python fix-broken-rust-debug-yaml.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')

t = p.read_text(encoding='utf-8')

broken = '''        shell: bash

        run: |

        env:

          RUST_LOG: debug

          RUST_BACKTRACE: '1'

          set -uo pipefail

'''

fixed = '''        shell: bash

        env:

          RUST_LOG: debug

          RUST_BACKTRACE: '1'

        run: |

          set -uo pipefail

'''

assert broken in t

p.write_text(t.replace(broken, fixed, 1), encoding='utf-8')

print('fixed', fixed in p.read_text(encoding='utf-8'))

