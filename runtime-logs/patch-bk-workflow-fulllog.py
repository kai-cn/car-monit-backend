#!/usr/bin/env python3
from pathlib import Path
p = Path(r'D:\work\runtime-logs\bk-parity-diag.yml')
t = p.read_text(encoding='utf-8')
old = 'grep -E \'ERROR|Caused by|APPLICATION FAILED|Exception|Started .* in|Tomcat started\' "$f" | tail -40 || true'
new = 'tail -n 160 "$f" || true'
print('found', old in t)
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
print('patched', new in t)
