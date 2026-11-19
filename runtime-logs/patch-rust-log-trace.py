#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')
t = p.read_text(encoding='utf-8')
t = t.replace('RUST_LOG: debug', 'RUST_LOG: "sqlx=trace,car_monit_rust=trace"', 1)
p.write_text(t, encoding='utf-8')
print('trace ready', 'sqlx=trace' in t)
