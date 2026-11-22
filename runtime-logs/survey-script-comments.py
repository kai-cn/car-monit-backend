#!/usr/bin/env python3
"""只读盘点 runtime-logs 下缺少思路/用途注释的脚本。

思路：递归扫描 .py/.ps1/.sh，跳过 node_modules/.git/venv；
文件前 30 行若出现 思路/用途/说明/Purpose/LEGACY-SCRIPT-ANNOTATION 则认为已注释。
输出统计与部分文件清单，不修改任何文件。
"""
from pathlib import Path

ROOT=Path(r'D:\work\runtime-logs')
SKIP={'node_modules','.git','venv','__pycache__'}
MARK=('思路','用途','说明','Purpose','purpose','LEGACY-SCRIPT-ANNOTATION')
missing=[]
for p in ROOT.rglob('*'):
    if p.suffix.lower() not in {'.py','.ps1','.sh'}:
        continue
    if any(x in p.parts for x in SKIP):
        continue
    try:
        head='\n'.join(p.read_text(encoding='utf-8',errors='ignore').splitlines()[:35])
    except Exception:
        continue
    if not any(m in head for m in MARK):
        missing.append(p)
print('TOTAL_MISSING',len(missing))
for p in missing[:80]:
    print(p.relative_to(ROOT))
