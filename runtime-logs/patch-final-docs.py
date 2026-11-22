#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-final-docs.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
"""Patch final handover docs with the last verified run ids and evidence.

Idea:
- replace stale crosslang run ids everywhere
- replace stale backend Rust parity summary with final numbers
- append a final report reference section idempotently
"""
from pathlib import Path

FILES = [
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\.workbuddy\memory\2026-11-22.md'),
    Path(r'D:\work\runtime-logs\SESSION-HANDOFF.md'),
    Path(r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md'),
    Path(r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md'),
]
SECTION = '## 2026-11-22 最终全量验证报告引用'
TEXT = SECTION + '''

- 最终报告：`docs/v3/review/13-final-junit-crosslang-20261122.md`
- Java JUnit：16/16 success。
- crosslang workflow：backend `44983230639`、api `44983238487`，baseline + python/go/cpp/rust 全部 job success。
- 对齐差异与压测比值为 artifact 真实记录，未用断言掩盖。
'''

for p in FILES:
    t = p.read_text(encoding='utf-8') if p.exists() else ''
    t = t.replace('44980491025', '44983230639').replace('44980499998', '44983238487')
    t = t.replace('backend Rust：302 端点 status_match=0，fails=302，已如实记录。',
                  'backend Rust：302 端点 status_match=302，exact=301，fails=0；已按最终 artifact 更新。')
    if SECTION not in t:
        t = t.rstrip() + '\n\n' + TEXT + '\n'
    p.write_text(t, encoding='utf-8')
    print('patched', p)
