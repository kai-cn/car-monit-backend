#!/usr/bin/env python3
"""Inspect final six non-200 endpoints in backend and api logs."""
from pathlib import Path
base=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name in ['app.log','api.log']:
 p=base/name
 lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 print('===',name,len(lines),'===')
 needles=['batchGenCode','vehicleweight/1','fitting/list','exception','Exception','ERROR']
 hits=[i for i,l in enumerate(lines) if any(n in l for n in needles)]
 for i in hits[-40:]: print(i+1,lines[i][:300])
