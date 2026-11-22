#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：compare_load.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
"""Compare two JUnit load reports and emit JSON/Markdown summaries.

Idea:
- read baseline/candidate JSON produced by EndpointLoadTest
- compare throughput, average/p95/p99 latency, error rate
- keep ratios as ratios (candidate/baseline); lower latency and error are better,
  higher throughput is better
"""
import argparse
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--label', default='load')
    ap.add_argument('--out', required=True)
    ap.add_argument('--md', required=True)
    a = ap.parse_args()
    b = json.loads(Path(a.baseline).read_text(encoding='utf-8'))
    c = json.loads(Path(a.candidate).read_text(encoding='utf-8'))
    keys = ['total_requests', 'rps', 'avg_latency_ms', 'p50_ms', 'p95_ms', 'p99_ms', 'errors']
    rows = []
    for k in keys:
        bv, cv = b.get(k, 0), c.get(k, 0)
        ratio = round(cv / bv, 4) if isinstance(bv, (int, float)) and bv else None
        rows.append({'metric': k, 'baseline': bv, 'candidate': cv, 'candidate_over_baseline': ratio})
    ber = round(b.get('errors', 0) / b.get('total_requests', 1), 6)
    cer = round(c.get('errors', 0) / c.get('total_requests', 1), 6)
    report = {'label': a.label, 'baseline_variant': b.get('variant'),
              'candidate_variant': c.get('variant'), 'rows': rows,
              'error_rate': {'baseline': ber, 'candidate': cer}}
    Path(a.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    lines = ['# %s load report' % a.label, '',
             '| metric | baseline | candidate | candidate/baseline |',
             '| --- | ---: | ---: | ---: |']
    for r in rows:
        lines.append('| %s | %s | %s | %s |' % (
            r['metric'], r['baseline'], r['candidate'], r['candidate_over_baseline']))
    lines += ['', '**error_rate**: baseline=%s candidate=%s' % (ber, cer), '']
    Path(a.md).write_text('\n'.join(lines), encoding='utf-8')
    print('\n'.join(lines[:6]))


if __name__ == '__main__':
    main()
