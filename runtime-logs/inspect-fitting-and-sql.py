#!/usr/bin/env python3
"""Inspect fitting route and PostgreSQL SQL compatibility candidates."""
from pathlib import Path
B=Path('/home/dev/IdeaProjects/car-monit-backend')
A=Path('/home/dev/IdeaProjects/car-monit-api')
for root, needles in [(B,['/fitting/list','fitting/list']),(A,['/fitting/list','trailfitting/list'])]:
 print('===',root, '===')
 for p in root.rglob('*.java'):
  try: t=p.read_text(encoding='utf-8',errors='replace')
  except: continue
  if any(n in t for n in needles):
   for i,l in enumerate(t.splitlines(),1):
    if any(n in l for n in needles): print(p.relative_to(root),i,l.strip()[:220])
