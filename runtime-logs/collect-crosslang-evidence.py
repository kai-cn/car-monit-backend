#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：collect-crosslang-evidence.py
用途：收集云端 run 状态。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：只读远端状态，不修改分支。
"""
"""Download and summarize crosslang full-parity reports.

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
        ('baseline', 14738278073), ('python', 14738563135), ('go', 14738941310),
        ('cpp', 14738946809), ('rust', 14738697426),
    ],
    'api': [
        ('baseline', 14738981778), ('python', 14739031179), ('go', 14739410655),
        ('cpp', 14738343353), ('rust', 14738759637),
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
