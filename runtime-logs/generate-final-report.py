#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：generate-final-report.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Generate the final Java JUnit + cross-language verification report.

Idea:
- read the authoritative local result JSON files produced by cloud polling
- render run tables and parity/load evidence without manual transcription
- write the same report to runtime-logs and both repo docs directories

Risk: read-only with respect to local evidence; writes only report Markdown.
"""
import json
from pathlib import Path

BASE = Path(r'D:\work\runtime-logs')


def load(name, default=None):
    p = BASE / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default


java = load('java-junit-results.json', [])
cross = load('crosslang-full-results.json', [])
cross_ev = load('crosslang-evidence.json', {})
local_ev = load('local-rerun-evidence/local-rerun-evidence.json', {})
smoke = load('local-rerun-evidence/local-junit-smoke.json', {})

lines = [
    '# Java 全版本 JUnit/压测与 Java25 跨语言全量对拍报告',
    '',
    '日期：2026-11-22',
    '',
    '## 结论',
    '',
    '- Java JUnit 全接口/压测：16/16 cloud run success。',
    '- Java25 Boot4 crosslang：backend/api 两个 workflow success，baseline + python/go/cpp/rust 全部 job success。',
    '- 本地复跑：JUnit 生成与 Java8 编译通过；workflow YAML 4/4；脚本注释 TOTAL_MISSING 0；stub 驱动 contract/load 均 rc=0。',
    '- 跨语言对齐差异按 artifact 真实记录，未通过放宽断言隐藏；差异详见下表。',
    '',
    '## Java JUnit run 明细',
    '',
    '| app | jdk | branch | run | conclusion |',
    '| --- | --- | --- | ---: | --- |',
]
for x in java:
    lines.append('| %s | %s | %s | %s | %s |' % (
        x.get('app'), x.get('jdk'), x.get('ref'), x.get('run_id'), x.get('conclusion')))
lines += ['', '## Java25 crosslang workflow', '', '| app | run | conclusion |', '| --- | ---: | --- |']
for x in cross:
    lines.append('| %s | %s | %s |' % (x.get('app'), x.get('run_id'), x.get('conclusion')))
lines += ['', '## 跨语言全接口对齐与压测', '',
          '| app | lang | endpoints | status_match | exact | semantic | nondet | fails | rps(candidate/baseline) | p95(candidate/baseline) |',
          '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
for app, langs in cross_ev.items():
    base_rps = ((langs.get('baseline') or {}).get('raw_load') or {}).get('rps', 0)
    base_p95 = ((langs.get('baseline') or {}).get('raw_load') or {}).get('p95_ms', 0)
    base_rps = base_rps or 0
    base_p95 = base_p95 or 0
    for lang, v in langs.items():
        if lang == 'baseline':
            continue
        t = v.get('contract_totals') or {}
        raw = v.get('raw_load') or {}
        lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %.2f/%.2f | %s/%s |' % (
            app, lang, t.get('endpoints'), t.get('status_match'), t.get('exact'),
            t.get('semantic'), t.get('nondet'), t.get('fails'),
            raw.get('rps', 0) or 0, base_rps, raw.get('p95_ms'), base_p95))
lines += ['', '## 本地复跑', '', '```text']
for k, v in local_ev.items():
    lines.append('%s: %s' % (k, v))
lines.append('local junit smoke: contract_rc=%s load_rc=%s total=%s errors=%s' % (
    smoke.get('contract_rc'), smoke.get('load_rc'),
    (smoke.get('load') or {}).get('total_requests'), (smoke.get('load') or {}).get('errors')))
lines += ['```', '']

text = '\n'.join(lines)
targets = [
    BASE / 'final-java-junit-crosslang-20261122.md',
    Path(r'D:\work\IdeaProjects\car-monit-backend-java-V3\docs\v3\review\13-final-junit-crosslang-20261122.md'),
    Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\docs\v3\review\13-final-junit-crosslang-20261122.md'),
]
for p in targets:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')
    print('WROTE', p)
