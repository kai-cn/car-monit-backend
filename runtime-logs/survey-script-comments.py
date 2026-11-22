#!/usr/bin/env python3
"""
@description 历史脚本 survey-script-comments.py：只读盘点脚本、注释或配置状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python survey-script-comments.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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
