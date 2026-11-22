#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：append-final-junit-crosslang.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Append final JUnit/crosslang verification results to handover docs.

Idea:
- keep one concise section per document, with run ids and evidence paths
- avoid secrets; only public run ids/artifact ids and counts are recorded
- idempotent by checking a unique section header
"""
from pathlib import Path

SECTION = '## 2026-11-22 Java JUnit 与 Java25 跨语言全量验证收官'
TEXT = SECTION + '''

- Java JUnit 全接口/压测：16/16 run success（backend 7、api 9），证据 `D:\\work\\runtime-logs\\java-junit-results.json`。
- Java25 Boot4 crosslang：backend `44983230639`、api `44983238487`；baseline + python/go/cpp/rust 全部 job success。
- 证据：`D:\\work\\runtime-logs\\crosslang-evidence.json` / `crosslang-evidence.md`；对齐差异如实记录，未用断言掩盖。
- 本地复跑：JUnit 生成/Java8 编译 2/2、workflow YAML 4/4、脚本注释 TOTAL_MISSING 0、stub 驱动 contract/load rc=0/0 errors=0。
- 关键修复：AOT skip、sudo 日志目录、Corretto 8、lazy init/Kafka exclude、artifact 携带 JUnit jar、候选启动命令与环境修正。
'''

FILES = [
    Path(r'D:\work\runtime-logs\SESSION-HANDOFF.md'),
    Path(r'D:\work\runtime-logs\公开仓库安全加固-任务清单.md'),
    Path(r'D:\work\runtime-logs\公开仓库安全加固-脚本与证据索引.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-session-handoff-20261118.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\12-repro-index-20261118.md'),
]

for p in FILES:
    t = p.read_text(encoding='utf-8') if p.exists() else '# Session handover\n\n'
    if SECTION in t:
        print('SKIP', p)
        continue
    p.write_text(t.rstrip() + '\n\n' + TEXT + '\n', encoding='utf-8')
    print('APPENDED', p)
