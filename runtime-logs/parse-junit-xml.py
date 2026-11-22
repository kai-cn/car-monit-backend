#!/usr/bin/env python3

"""
@description 历史脚本 parse-junit-xml.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python parse-junit-xml.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

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

