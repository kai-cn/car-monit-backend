#!/usr/bin/env python3
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
