#!/usr/bin/env python3
"""Inspect final six non-200 details from latest WSL logs."""
from pathlib import Path
base=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream')
for name,needles in [
    ('app.log',["请求地址'/tool/gen/batchGenCode'","请求地址'/manager/confimfree/except/1'","请求地址'/manager/bigScreen/export/download/1'"]),
    ('api.log',["vehicleweight/1","fitting/list","operator does not exist: timestamp with time zone - integer"])]:
    p=base/name
    lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
    print('===',name,'===')
    for needle in needles:
        idx=next((i for i,l in enumerate(lines) if needle in l),None)
        print('---',needle,idx+1 if idx is not None else None)
        if idx is None: continue
        for i in range(idx,min(idx+35,len(lines))):
            l=lines[i]
            if any(k in l for k in ['ERROR','Exception','Caused by','at com.ruoyi','at org.springframework','does not exist','status','path']):
                print(i+1,l[:400])
