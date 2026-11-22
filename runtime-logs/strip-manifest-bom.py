#!/usr/bin/env python3

"""
@description 历史脚本 strip-manifest-bom.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python strip-manifest-bom.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea: PowerShell wrote the TSV with a BOM, so the first path failed to match.


Risk: rewrites only the generated manifest file.
"""
from pathlib import Path



p = Path(r'D:\work\runtime-logs\local-package-manifest.tsv')

t = p.read_text(encoding='utf-8-sig')

p.write_text(t, encoding='utf-8')

print('STRIPPED_BOM', len(t.splitlines()))

