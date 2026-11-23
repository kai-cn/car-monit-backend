#!/usr/bin/env python3
"""Inspect final eight non-200 endpoint exceptions."""
from pathlib import Path
lines=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/app.log').read_text(encoding='utf-8',errors='replace').splitlines()
needles=["请求地址'/base/vehicleweight/1'", "请求地址'/base/fitting/list'", "请求地址'/tool/gen/synchDb/1'", "请求地址'/tool/gen/batchGenCode'", "请求地址'/tool/gen/column/1'"]
for needle in needles:
    idx=next((i for i,l in enumerate(lines) if needle in l),None)
    print('===',needle,idx+1 if idx is not None else None,'===')
    if idx is None: continue
    for i in range(idx,min(idx+40,len(lines))):
        l=lines[i]
        if any(k in l for k in ['ERROR','Exception','Caused by','at com.ruoyi','UPSTREAM','relation','column','does not exist']):
            print(i+1,l[:400])
