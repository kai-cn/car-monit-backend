#!/usr/bin/env python3
"""Show current api log startup and backend downstream failures."""
from pathlib import Path
base=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name in ['api.log','app.log']:
 p=base/name
 lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
 print('===',name,len(lines),'===')
 keys=['Application run failed','Started ','ERROR','Caused by','9902','7890','Tomcat started']
 hits=[i for i,l in enumerate(lines) if any(k in l for k in keys)]
 for i in hits[:35]: print(i+1,lines[i][:260])
