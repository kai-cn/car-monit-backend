#!/usr/bin/env python3

"""
@description 历史脚本 parity_compare.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python parity_compare.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.



from __future__ import annotations

import argparse, json, statistics, sys

from pathlib import Path



VOLATILE = {'timestamp', 'time', 'requestId', 'traceId', 'token', 'expireTime',

            'serverTime', 'now', 'cost', 'duration', 'date', 'createTime', 'updateTime'}





def norm(x: object) -> object:

    if isinstance(x, dict):

        return {k: norm(v) for k, v in x.items() if k not in VOLATILE}

    if isinstance(x, list):

        return [norm(v) for v in x]

    return x





def classify(body: str) -> tuple[str, object]:

    if not body:

        return 'empty', None

    try:

        return 'json', norm(json.loads(body))

    except Exception:

        return 'text', body





def main() -> None:

    ap = argparse.ArgumentParser()

    ap.add_argument('--baseline', required=True)

    ap.add_argument('--candidate', required=True)

    ap.add_argument('--out', required=True)

    ap.add_argument('--md', required=True)

    ap.add_argument('--label', default='parity')

    ap.add_argument('--allow-diff-status', default='', help='comma-separated statuses that may differ')
    ap.add_argument('--strict', action='store_true', help='require every endpoint exact/semantic match; NONDET is not a pass')

    a = ap.parse_args()



    b = json.loads(Path(a.baseline).read_text(encoding='utf-8'))

    c = json.loads(Path(a.candidate).read_text(encoding='utf-8'))

    allow = {int(x) for x in a.allow_diff_status.split(',') if x.strip().isdigit()}



    be = {e['endpoint']: e for e in b.get('endpoints', [])}

    ce = {e['endpoint']: e for e in c.get('endpoints', [])}

    keys = sorted(set(be) | set(ce))



    rows = []

    fails = 0

    exact_n = sem_n = status_n = nondet_n = 0

    for k in keys:

        rr = {'endpoint': k}

        x, y = be.get(k), ce.get(k)

        if not x or not y:

            rr['verdict'] = 'MISSING'

            rr['note'] = 'missing on ' + ('baseline' if not x else 'candidate')

            fails += 1

            rows.append(rr)

            continue

        rr['status'] = [x['status'], y['status']]

        rr['bytes'] = [x['bytes'], y['bytes']]

        rr['latency_ms'] = [x['latency_ms'], y['latency_ms']]

        # non-determinism: probe recorded `stable=False` when two calls differed

        unstable = (x.get('stable') is False) or (y.get('stable') is False)

        st_same = x['status'] == y['status']

        if st_same:

            status_n += 1

        same_raw = x.get('body', '') == y.get('body', '') and x['bytes'] == y['bytes']

        _, xb = classify(x.get('body', ''))

        _, yb = classify(y.get('body', ''))

        same_sem = (xb == yb)

        if unstable:

            rr['exact'] = same_raw

            rr['semantic'] = same_sem

            # Non-determinism excuses BODY drift only. A status mismatch is still a real

            # difference (e.g. native 500 vs JVM 200) and must fail unless allowlisted.

            if st_same or (x['status'] in allow and y['status'] in allow):

                nondet_n += 1

                rr['verdict'] = 'NONDET'

                rr['note'] = 'endpoint non-deterministic (data/ordering); body diff not attributable'

            else:

                rr['verdict'] = 'DIFF'

                rr['note'] = 'status mismatch on unstable endpoint (real difference)'

                fails += 1

            rows.append(rr)

            continue

        if same_raw:

            exact_n += 1

        if same_sem:

            sem_n += 1

        rr['exact'] = same_raw

        rr['semantic'] = same_sem

        ok = st_same and (same_raw or same_sem)

        if not st_same and x['status'] in allow and y['status'] in allow:

            ok = True

            rr['note'] = 'status in allowlist'

        rr['verdict'] = 'OK' if ok else 'DIFF'

        if not ok:

            fails += 1

        rows.append(rr)



    def avg(es: list[dict], f: str) -> float | None:

        v = [e[f] for e in es if e.get(f)]

        return round(statistics.mean(v), 2) if v else None



    summary = {

        'label': a.label,

        'baseline': {'variant': b.get('variant'), 'startup_ms': b.get('startup_ms'),

                     'peak_rss_mb': b.get('startup_peak_rss_mb'),

                     'avg_latency_ms': avg(b.get('endpoints', []), 'latency_ms')},

        'candidate': {'variant': c.get('variant'), 'startup_ms': c.get('startup_ms'),

                      'peak_rss_mb': c.get('startup_peak_rss_mb'),

                      'avg_latency_ms': avg(c.get('endpoints', []), 'latency_ms')},

        'totals': {'endpoints': len(keys), 'status_match': status_n, 'exact': exact_n,

                   'semantic': sem_n, 'nondet': nondet_n, 'fails': fails},

        'rows': rows,

    }

    Path(a.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')



    # markdown

    L = []

    L.append('# %s parity report' % a.label)

    L.append('')

    bs, cs = summary['baseline'], summary['candidate']

    L.append('| metric | %s (%s) | %s (%s) |' % (bs['variant'], 'baseline', cs['variant'], 'candidate'))

    L.append('| --- | --- | --- |')

    L.append('| startup_ms | %s | %s |' % (bs['startup_ms'], cs['startup_ms']))

    L.append('| peak_rss_MB | %s | %s |' % (bs['peak_rss_mb'], cs['peak_rss_mb']))

    L.append('| avg_latency_ms | %s | %s |' % (bs['avg_latency_ms'], cs['avg_latency_ms']))

    L.append('')

    t = summary['totals']

    L.append('**Endpoints**: %d | status_match=%d | exact=%d | semantic=%d | nondet=%d | fails=%d' % (

        t['endpoints'], t['status_match'], t['exact'], t['semantic'], t['nondet'], t['fails']))

    L.append('')

    L.append('| endpoint | status(b/c) | bytes(b/c) | exact | semantic | verdict |')

    L.append('| --- | --- | --- | --- | --- | --- |')

    for r in rows:

        if r.get('verdict') == 'MISSING':

            L.append('| %s | - | - | - | - | MISSING |' % r['endpoint'])

            continue

        L.append('| %s | %s/%s | %s/%s | %s | %s | %s |' % (

            r['endpoint'], r['status'][0], r['status'][1], r['bytes'][0], r['bytes'][1],

            r.get('exact'), r.get('semantic'), r['verdict']))

    # list only the real DIFFs with a note

    diffs = [r for r in rows if r.get('verdict') == 'DIFF']

    if diffs:

        L.append('')

        L.append('## Real differences (DIFF)')

        for r in diffs:

            L.append('- `%s`: status %s/%s, bytes %s/%s' % (

                r['endpoint'], r['status'][0], r['status'][1], r['bytes'][0], r['bytes'][1]))

    Path(a.md).write_text('\n'.join(L), encoding='utf-8')



    strict_bad = 0
    if a.strict:
        for row in rows:
            if row.get('verdict') != 'OK':
                strict_bad += 1
    print('COMPARE label=%s endpoints=%d fails=%d strict_bad=%d' % (a.label, len(keys), fails, strict_bad))

    sys.exit(0 if fails == 0 and strict_bad == 0 else 1)





if __name__ == '__main__':

    main()

