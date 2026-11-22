#!/usr/bin/env python3
"""为 runtime-logs 下的历史脚本批量补充思路与必要注释。

设计思路：
1. 递归扫描 .py/.ps1/.sh，跳过 node_modules/.git/venv/__pycache__。
2. 幂等：文件前 35 行已有"思路/用途/说明/Purpose/LEGACY-SCRIPT-ANNOTATION"则跳过。
3. 根据文件名推断用途：dispatch/sync/patch/fix/collect/survey/probe 等。
4. 根据文件名推断风险：会写本地/远端的脚本提示执行前确认目标；只读脚本提示一般不改远端。
5. Python 插入模块 docstring（放在 shebang/encoding 之后，且用 ast.parse 校验）；
   PowerShell/Shell 插入 # 注释块。语法校验失败则跳过该文件，避免破坏脚本。
"""
import ast
import re
from pathlib import Path

ROOT=Path(r'D:\work\runtime-logs')
SKIP={'node_modules','.git','venv','__pycache__'}
MARK=('思路','用途','说明','Purpose','purpose','LEGACY-SCRIPT-ANNOTATION')
ENCODING=re.compile(r'^\s*#.*coding[:=]')

def kind(name):
    n=name.lower()
    if n.startswith(('dispatch','redispatch')): return ('派发云 runner 任务','会触发 GitHub Actions，执行前确认分支和 workflow')
    if n.startswith('collect'): return ('收集云端 run 状态','只读远端状态，不修改分支')
    if n.startswith(('survey','check','scan','diagnose','probe','show','list')): return ('只读检查/诊断','通常只读；若脚本内有明确写操作以其自身说明为准')
    if n.startswith(('annotate',)): return ('批量补充脚本注释','会修改本地脚本文件，执行前确认目录')
    if n.startswith(('sync','copy','fetch')): return ('同步或拉取本地/远端内容','可能更新本地工作树或读取远端，执行前确认目标分支')
    if n.startswith(('push','put')): return ('推送内容到远端','会修改远端分支，执行前确认凭据与目标')
    if n.startswith(('fix','patch','local','upgrade','dedupe','unstage','migrate','insert','cleanup')): return ('本地或远端修复/改造','会修改文件、索引或远端，执行前确认可回滚')
    return ('运维辅助脚本','执行前确认目标环境、凭据与影响范围')

changed=[]; skipped=[]
for p in sorted(ROOT.rglob('*')):
    if p.suffix.lower() not in {'.py','.ps1','.sh'} or any(x in p.parts for x in SKIP):
        continue
    text=p.read_text(encoding='utf-8',errors='ignore')
    head='\n'.join(text.splitlines()[:35])
    if any(m in head for m in MARK):
        continue
    purpose,risk=kind(p.name)
    header_py=f'''"""
LEGACY-SCRIPT-ANNOTATION
文件：{p.name}
用途：{purpose}。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：{risk}。
"""
'''
    header_sh=f'''# LEGACY-SCRIPT-ANNOTATION
# 文件：{p.name}
# 用途：{purpose}。
# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
# 风险：{risk}。
'''
    lines=text.splitlines(keepends=True)
    idx=0
    if lines and lines[0].startswith('#!'):
        idx=1
    if idx<len(lines) and ENCODING.match(lines[idx]):
        idx+=1
    new_lines=lines[:idx]+[header_py if p.suffix.lower()=='.py' else header_sh]+lines[idx:]
    new=''.join(new_lines)
    if p.suffix.lower()=='.py':
        try:
            ast.parse(new)
        except SyntaxError:
            skipped.append(p.name); continue
    p.write_text(new,encoding='utf-8')
    changed.append(p.name)

print('ANNOTATED',len(changed))
print('SKIPPED_SYNTAX',len(skipped))
for n in skipped[:20]: print(' ',n)
