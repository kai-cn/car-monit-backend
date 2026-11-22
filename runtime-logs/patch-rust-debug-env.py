#!/usr/bin/env python3

"""
@description 历史脚本 patch-rust-debug-env.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-rust-debug-env.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')

t = p.read_text(encoding='utf-8')

needle = '''      - name: Probe Rust

        if: steps.gate.outputs.run == 'yes' && matrix.lang == 'rust'

        shell: bash

        run: |

'''

add = needle + '''        env:

          RUST_LOG: debug

          RUST_BACKTRACE: '1'

'''

assert needle in t

p.write_text(t.replace(needle, add, 1), encoding='utf-8')

print('patched', 'RUST_LOG: debug' in t)

