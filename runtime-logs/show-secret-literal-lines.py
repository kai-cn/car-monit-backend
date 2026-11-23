#!/usr/bin/env python3
"""Show matched lines with sensitive literals masked."""
import re
from pathlib import Path
pat=re.compile('wKla|Admin@20'+r'\d\d-')
for name in ['sanitize-all-history-secrets.py','patch-wsl-master-fixes5.py']:
 p=Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs')/name
 print('===',name,'===')
 for i,l in enumerate(p.read_text(encoding='utf-8',errors='replace').splitlines(),1):
  if pat.search(l):
   m=pat.search(l); print(i,l[:m.start()]+'<PATTERN>'+l[m.end():])
