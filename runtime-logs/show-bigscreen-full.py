#!/usr/bin/env python3
"""Show full BigScreen bean exception context."""
from pathlib import Path
lines=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/app.log').read_text(encoding='utf-8',errors='replace').splitlines()
for i in range(13024,13045):
    print(i+1,lines[i][:1200])
