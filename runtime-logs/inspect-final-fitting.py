#!/usr/bin/env python3
"""Inspect final fitting upstream failure and classify remaining non-200 endpoints."""
from pathlib import Path
base=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name in ['app.log','api.log']:
 p=base/name
 lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 print('===',name,'===')
 for i,l in enumerate(lines):
  if 'fitting' in l.lower() or 'trail' in l.lower() and 'ERROR' in l:
   if any(k in l for k in ['ERROR','Exception','/api/v1','/base/fitting','status 4','status 5','Resource not found']):
    print(i+1,l[:400])
