#!/usr/bin/env python3
"""Show remaining endpoint exceptions from WSL app log."""
from pathlib import Path
lines=Path('/mnt/d/work/runtime-logs/wsl-final-retest-with-downstream/app.log').read_text(encoding='utf-8',errors='replace').splitlines()
for needle in ["请求地址'/flow/messageinfo/exportShrz'", "请求地址'/manager/suspicious/exportAbnormalPassage'", "请求地址'/tool/gen/preview/1'", "请求地址'/tool/gen/download/1'", "请求地址'/manager/confimfree/except/1'"]:
    idx=next((i for i,l in enumerate(lines) if needle in l),None)
    print('===',needle,idx+1 if idx is not None else None,'===')
    if idx is None: continue
    for i in range(idx,min(idx+45,len(lines))):
        l=lines[i]
        if any(k in l for k in ['NullPointerException','at com.ruoyi','Caused by','IllegalArgumentException','ERROR']): print(i+1,l[:400])
