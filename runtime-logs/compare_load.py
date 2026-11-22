#!/usr/bin/env python3

"""
@description 历史脚本 compare_load.py：对比基线/候选结果并产出报告；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python compare_load.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- read baseline/candidate JSON produced by EndpointLoadTest


- compare throughput, average/p95/p99 latency, error rate


- keep ratios as ratios (candidate/baseline); lower latency and error are better,


  higher throughput is better
"""
import argparse

import json

from pathlib import Path





def main() -> None:

    """

    对比基线与候选的压测报告，并写出 JSON/Markdown 摘要。



    @sideEffect 写入 --out 指定的 JSON 与 --md 指定的 Markdown 文件。

    """

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

