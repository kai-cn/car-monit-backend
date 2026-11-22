#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-rust-deps.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Install native build dependencies for Rust/C++ candidates.

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
