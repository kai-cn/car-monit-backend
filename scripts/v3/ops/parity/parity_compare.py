#!/usr/bin/env python3
# ======================================================================
# 文件：scripts/v3/ops/parity/parity_compare.py
# 用途：对比：两份探针 JSON 按 status/exact/semantic/nondet 判定并输出报告
# 说明：仅新增中文注释，不改执行逻辑。
# ======================================================================
"""Compare two probe result JSONs (baseline vs candidate) and emit a verdict + markdown.

Usage:
  python parity_compare.py --baseline out/jar.json --candidate out/native.json \
      --out out/report.json --md out/report.md [--label api-jdk25-linux]

Semantics:
  * exact  : raw body bytes identical
  * semantic: JSON-normalised body identical after dropping volatile keys
  * status  : HTTP status identical
  * latency/startup/RSS deltas are reported, not gated
Exit code: 0 if all endpoints have identical status AND (exact or semantic) body, else 1.
"""
from __future__ import annotations
import argparse, json, statistics, sys
from pathlib import Path

VOLATILE = {'timestamp', 'time', 'requestId', 'traceId', 'token', 'expireTime',
            'serverTime', 'now', 'cost', 'duration', 'date', 'createTime', 'updateTime',
            'loginDate', 'lastLoginTime',
            # 慢变/运行态字段：跨语言/跨实例必然不同，不参与业务等价判定
            'X-Data-Source', 'xDataSources', 'datasource', 'dataSource', 'source',
            'cacheHitRate', 'apiTimeoutRate', 'apiErrorRate', 'exportBacklog',
            'circuitState', 'loginTime', 'sessionId', 'commandStats', 'uptime',
            'lastExecuteTime', 'nextScheduleTime', 'lastDurationMs', 'lastUpdatedTableCount',
            'historySize', 'successRate', 'avgDurationMs'}


def norm(x):
    if isinstance(x, dict):
        out = {k: norm(v) for k, v in x.items() if k not in VOLATILE}
        # RuoYi AjaxResult 空信封等价归一化：
        #   Java 空列表返回 {"code":200,"data":[]}，Go/Rust 有时省略 data 字段
        #   （{"code":200}）。客户端语义一致（都表示"无数据"），视为等价。
        # 仅在典型 AjaxResult 信封（含 code 且无 rows/total 分页字段）时归一。
        if 'code' in x and 'data' not in out and 'rows' not in out and 'total' not in out:
            out['data'] = []
        return out
    if isinstance(x, list):
        return [norm(v) for v in x]
    return x


def classify(body):
    if not body:
        return 'empty', None
    try:
        return 'json', norm(json.loads(body))
    except Exception:
        return 'text', body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', required=True)
    ap.add_argument('--candidate', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--md', required=True)
    ap.add_argument('--label', default='parity')
    ap.add_argument('--allow-diff-status', default='', help='comma-separated statuses that may differ')
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
        # 绝对失败断言：认证态探针记录 auth_fail / biz_code。任一侧出现
        # RuoYi 业务码 401/403/500（HTTP 200 假绿）即直接判 FAIL，不参与相对比较。
        auth_fail = bool(x.get('auth_fail')) or bool(y.get('auth_fail'))
        if auth_fail:
            rr['verdict'] = 'AUTH_FAIL'
            rr['biz_code'] = [x.get('biz_code'), y.get('biz_code')]
            rr['note'] = 'absolute auth/business-code failure (401/403/500)'
            fails += 1
            rows.append(rr)
            continue
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
            # stable=False is the probe's authoritative signal that this endpoint's
            # body changes between two consecutive calls on the SAME variant (e.g.
            # /captchaImage random image, live counters). In that case body drift is
            # not attributable to an implementation difference, so we classify NONDET.
            # A STATUS mismatch is still a real difference and must fail unless allowlisted.
            status_ok = st_same or (x['status'] in allow and y['status'] in allow)
            if status_ok:
                nondet_n += 1
                rr['verdict'] = 'NONDET'
                rr['note'] = ('endpoint non-deterministic (raw body); status equal, '
                              'body drift not attributable')
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

    def avg(es, f):
        v = [e[f] for e in es if e.get(f)]
        return round(statistics.mean(v), 2) if v else None

    summary = {
        'label': a.label,
        'baseline': {'variant': b.get('variant'), 'startup_ms': b.get('startup_ms'),
                     'peak_rss_mb': b.get('startup_peak_rss_mb') or b.get('peak_rss_mb'),
                     'avg_latency_ms': avg(b.get('endpoints', []), 'latency_ms')},
        'candidate': {'variant': c.get('variant'), 'startup_ms': c.get('startup_ms'),
                      'peak_rss_mb': c.get('startup_peak_rss_mb') or c.get('peak_rss_mb'),
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

    print('COMPARE label=%s endpoints=%d fails=%d' % (a.label, len(keys), fails))
    sys.exit(0 if fails == 0 else 1)


if __name__ == '__main__':
    main()
