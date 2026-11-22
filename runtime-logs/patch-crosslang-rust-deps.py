#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-rust-deps.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-crosslang-rust-deps.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- api Rust pulls rdkafka-sys and needs libcurl/openssl/zlib/sasl headers.


- install the same native packages already used by api cd-standalone.
"""
from pathlib import Path

import yaml



p = Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml')

t = p.read_text(encoding='utf-8')

anchor = '''      - name: Setup Python

'''

step = '''      - name: Install native build dependencies

        if: steps.gate.outputs.run == 'yes' && (matrix.lang == 'rust' || matrix.lang == 'cpp')

        shell: bash

        run: |

          sudo apt-get update

          sudo apt-get install -y cmake build-essential pkg-config \\

            libpq-dev libssl-dev zlib1g-dev libcurl4-openssl-dev libsasl2-dev



'''

assert anchor in t

p.write_text(t.replace(anchor, step + anchor, 1), encoding='utf-8')

yaml.safe_load(p.read_text(encoding='utf-8'))

print('patched', p)

