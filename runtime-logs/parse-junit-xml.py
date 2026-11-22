#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：parse-junit-xml.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Summarize JUnit XML failures for generated endpoint suites.

Idea:
- parse TEST-junit-jupiter.xml from an artifact
- print failure/error test names and messages
- count skipped/passed/failed and status distribution from junit-contract.json
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path(sys.argv[1])
xml = base / 'junit-contract-reports' / 'TEST-junit-jupiter.xml'
root = ET.parse(xml).getroot()
print('suite', root.attrib.get('tests'), 'failures', root.attrib.get('failures'),
      'errors', root.attrib.get('errors'), 'skipped', root.attrib.get('skipped'))
for tc in root.iter('testcase'):
    bad = tc.find('failure') or tc.find('error')
    if bad is not None:
        print('FAIL', tc.attrib.get('name'), (bad.attrib.get('message') or '')[:180])
        break
p = base / 'junit-contract.json'
if p.exists():
    rows = json.loads(p.read_text(encoding='utf-8')).get('endpoints', [])
    from collections import Counter
    print('status_counts', Counter(int(r.get('status', 0)) for r in rows).most_common(12))
    print('unstable', sum(1 for r in rows if not r.get('stable')))
