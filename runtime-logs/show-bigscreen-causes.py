#!/usr/bin/env python3
"""Show nested BigScreen bean causes and GenController source location."""
from pathlib import Path
log=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/app.log').read_text(encoding='utf-8',errors='replace').splitlines()
for i in range(13024,13075):
    line=log[i]
    if any(k in line for k in ['Caused by','Error creating bean','Unsatisfied','NoSuchBean','No qualifying','field','parameter','constructor']):
        print(i+1,line[:500])
B=Path('/home/dev/IdeaProjects/car-monit-backend')
for p in B.rglob('GenController.java'):
    print('FILE',p)
    for i,line in enumerate(p.read_text(encoding='utf-8',errors='replace').splitlines(),1):
        if any(k in line for k in ['getInfo(','preview(','columnList(','download(','genCode(','synchDb(','batchGenCode(']):
            print(i,line.strip()[:220])
