#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：dedupe-handoff.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md')
t = p.read_text(encoding='utf-8')
block = '''## 2026-11-19 最后增补
- runtime-logs 已清理凭据后入库 backend 源分支，最终提交 `a38f49a1`（先前 `f9cbd8cb` 被安全审核否决）。
- H9 已收口（Java8/Go/Python/Rust 全 fails=0）。
- H8 仍在迭代：`44544743332` native build 中；OSS 仅 native 禁用，AWS SDK 资源 include 已撤销。
'''
print('count before', t.count(block))
if t.count(block) == 2:
    first = t.index(block)
    second = t.index(block, first + len(block))
    t = t[:second] + t[second + len(block):]
p.write_text(t, encoding='utf-8')
print('count after', t.count(block))
