#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')
t = p.read_text(encoding='utf-8')
t = t.replace('RUST_LOG: "sqlx=trace,car_monit_rust=trace"',
              'RUST_LOG: "sqlx::pool=trace,car_monit_rust=info"', 1)
p.write_text(t, encoding='utf-8')
print('pool-only', 'sqlx::pool=trace' in t)
