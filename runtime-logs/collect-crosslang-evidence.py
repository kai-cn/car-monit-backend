#!/usr/bin/env python3

"""
@description 历史脚本 collect-crosslang-evidence.py：收集云端 run、job 或 artifact 状态；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python collect-crosslang-evidence.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- final cloud runs upload per-language artifacts with contract-report.json and


  load-report.json produced by parity_compare.py / compare_load.py


- download small report artifacts, extract totals and latency/throughput ratios


- write one evidence JSON/MD used by documentation
"""
import json

import subprocess

import sys

from pathlib import Path



BASE = Path(r'D:\work\runtime-logs')

DL = BASE / 'download_artifact.py'

ARTIFACTS = {

    'backend': [

        ('baseline', 14758490185), ('python', 14757931650), ('go', 14758151968),

        ('cpp', 14757719587), ('rust', 14758107206),

    ],

    'api': [

        ('baseline', 14757986323), ('python', 14757848152), ('go', 14757917177),

        ('cpp', 14758546348), ('rust', 14758766387),

    ],

}





def load_json(root, name):

    for p in Path(root).rglob(name):

        try:

            return json.loads(p.read_text(encoding='utf-8'))

        except Exception:

            continue

    return None





def main():

    out = {}

    for app, arts in ARTIFACTS.items():

        out[app] = {}

        for lang, aid in arts:

            d = BASE / 'crosslang-evidence' / app / lang

            subprocess.run([sys.executable, str(DL), f'kai-cn/car-monit-{app}', str(aid), str(d)],

                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

            contract = load_json(d, 'contract-report.json')

            load = load_json(d, 'load-report.json')

            raw_load = load_json(d, 'junit-load.json')

            out[app][lang] = {

                'contract_totals': contract.get('totals') if contract else None,

                'load_rows': load.get('rows') if load else None,

                'load_error_rate': load.get('error_rate') if load else None,

                'raw_load': {k: raw_load.get(k) for k in ('total_requests', 'rps', 'avg_latency_ms', 'p95_ms', 'p99_ms', 'errors', 'business_4xx', 'business_5xx')} if raw_load else None,

            }

    (BASE / 'crosslang-evidence.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = ['# Cross-language full parity evidence', '', '| app | lang | endpoints | status_match | exact | semantic | nondet | fails | rps(c/b) | p95(c/b) |', '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']

    for app, langs in out.items():

        base_rps = (langs['baseline']['raw_load'] or {}).get('rps', 0)

        base_p95 = (langs['baseline']['raw_load'] or {}).get('p95_ms', 0)

        for lang, v in langs.items():

            if lang == 'baseline':

                continue

            t = v['contract_totals'] or {}

            raw = v['raw_load'] or {}

            lines.append('| %s | %s | %s | %s | %s | %s | %s | %s | %.2f/%.2f | %s/%s |' % (

                app, lang, t.get('endpoints'), t.get('status_match'), t.get('exact'), t.get('semantic'),

                t.get('nondet'), t.get('fails'), raw.get('rps', 0), base_rps, raw.get('p95_ms'), base_p95))

    (BASE / 'crosslang-evidence.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('\n'.join(lines))





if __name__ == '__main__':

    main()

