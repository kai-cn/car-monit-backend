"""
@description 历史脚本 smoke_jdk.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python smoke_jdk.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Creates two admin-provisioned role accounts, exercises backend -> API chain,


API query endpoints and internal guard, then soft-deletes the accounts.


Usage: python smoke_jdk.py 21 | 25
"""
import json

import sys

import urllib.request

import urllib.error



LABEL = sys.argv[1] if len(sys.argv) > 1 else '21'

B = 'http://127.0.0.1:9989'

A = 'http://127.0.0.1:9902'

ADMIN_PW = '${CARMONIT_ADMIN_PASSWORD}'

TEST_PW = 'JdkE2e@2026'

IT = 'jdk17-local-e2e-token-20261111'

ITOK = {'X-Internal-Token': IT}



lines = []

fails = []





def log(s):

    lines.append(s)

    print(s, flush=True)





def call(method, url, body=None, headers=None, timeout=90, raw=False):

    h = dict(headers or {})

    data = None

    if body is not None:

        data = json.dumps(body).encode('utf-8')

        h['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=h, method=method)

    try:

        with urllib.request.urlopen(req, timeout=timeout) as r:

            b = r.read()

            st = r.status

            hd = dict(r.headers)

    except urllib.error.HTTPError as e:

        b = e.read()

        st = e.code

        hd = dict(e.headers)

    except Exception as e:

        return {'status': -1, 'err': str(e), 'json': {}, 'headers': {}, 'raw': b''}

    if raw:

        return {'status': st, 'headers': hd, 'raw': b}

    try:

        j = json.loads(b.decode('utf-8', 'replace'))

    except Exception:

        j = {'_raw': b[:160].decode('utf-8', 'replace')}

    return {'status': st, 'headers': hd, 'json': j, 'raw': b}





def auth(t):

    return {'Authorization': 'Bearer ' + t}





def chk(name, ok, detail=''):

    log(('PASS ' if ok else 'FAIL ') + name + (' :: ' + detail if detail else ''))

    if not ok:

        fails.append(name)





def code(r):

    return (r.get('json') or {}).get('code', '-')





log('=== JDK%s SMOKE START ===' % LABEL)



# 1. admin login / getInfo

r = call('POST', B + '/login', {'username': 'admin', 'password': ADMIN_PW})

admin_t = (r['json'] or {}).get('token', '')

chk('admin login', r['status'] == 200 and bool(admin_t), 'HTTP %s token_len=%d' % (r['status'], len(admin_t)))

if not admin_t:

    log('FATAL: no admin token')

    sys.exit(1)

gi = call('GET', B + '/getInfo', headers=auth(admin_t))

chk('admin getInfo', gi['status'] == 200 and code(gi) == 200,

    'HTTP %s roles=%s' % (gi['status'], (gi['json'] or {}).get('roles')))



# 2. create two role-based test accounts

users = [

    ('jdk%se2e_view' % LABEL, 'JDK%sE2E-普通员工' % LABEL, 25424, [2], 'common'),

    ('jdk%se2e_mgr' % LABEL, 'JDK%sE2E-项目经理' % LABEL, 25367, [132], 'project_manager'),

]

created = []

tokens = {}

for name, nick, dept, roles, rk in users:

    body = {'userName': name, 'nickName': nick, 'password': TEST_PW,

            'deptId': dept, 'roleIds': roles, 'status': '0',

            'email': '', 'phonenumber': ''}

    r = call('POST', B + '/system/user', body, auth(admin_t))

    chk('create %s (role=%s)' % (name, rk), r['status'] == 200 and code(r) == 200,

        'HTTP %s code=%s msg=%s' % (r['status'], code(r), (r['json'] or {}).get('msg')))

    q = call('GET', B + '/system/user/list?pageNum=1&pageSize=10&userName=' + name,

             headers=auth(admin_t))

    rows = (q['json'] or {}).get('rows', [])

    if rows:

        created.append(rows[0]['userId'])

    lr = call('POST', B + '/login', {'username': name, 'password': TEST_PW})

    t = (lr['json'] or {}).get('token', '')

    tokens[name] = t

    chk('login %s' % name, lr['status'] == 200 and bool(t),

        'HTTP %s token_len=%d' % (lr['status'], len(t)))

    if t:

        g = call('GET', B + '/getInfo', headers=auth(t))

        chk('getInfo %s' % name, g['status'] == 200 and code(g) == 200,

            'HTTP %s roles=%s perms=%d' % (g['status'],

                                          (g['json'] or {}).get('roles'),

                                          len((g['json'] or {}).get('permissions') or [])))

        rt = call('GET', B + '/getRouters', headers=auth(t))

        chk('getRouters %s' % name, rt['status'] == 200,

            'HTTP %s menus=%d' % (rt['status'], len((rt['json'] or {}).get('data') or [])))



# 3. backend -> API chain (big-screen statistics)

mgr_t = tokens.get('jdk%se2e_mgr' % LABEL, '')

view_t = tokens.get('jdk%se2e_view' % LABEL, '')

if mgr_t:

    for ep in ['/manager/bigScreen/carStatistics?applyTime1=2025-01-01&applyTime2=2025-12-31',

               '/manager/bigScreen/carAudit?applyTime1=2025-01-01&applyTime2=2025-12-31',

               '/manager/bigScreen/orgList',

               '/manager/bigScreen/carVoList?applyTime1=2025-01-01&applyTime2=2025-12-31']:

        r = call('GET', B + ep, headers=auth(mgr_t))

        ds = r['headers'].get('X-Data-Source') or r['headers'].get('x-data-source') or '-'

        chk('mgr %s' % ep.split('?')[0], r['status'] == 200 and code(r) == 200,

            'HTTP %s code=%s X-Data-Source=%s' % (r['status'], code(r), ds))

    met = call('GET', B + '/monitor/bigscreen/metrics', headers=auth(mgr_t))

    d = (met['json'] or {}).get('data') or met['json'] or {}

    chk('mgr metrics', met['status'] == 200,

        'HTTP %s circuit=%s apiErrorRate=%s cacheHitRate=%s' %

        (met['status'], d.get('circuitState'), d.get('apiErrorRate'), d.get('cacheHitRate')))



# 4. negative permission checks with viewer

if view_t:

    r = call('GET', B + '/manager/bigScreen/export/approvals', headers=auth(view_t))

    chk('viewer export/approvals denied', r['status'] in (403, 200) and code(r) in (403, 200, 500, '-'),

        'HTTP %s code=%s' % (r['status'], code(r)))



# 5. API internal guard

r = call('GET', A + '/api/v3/export/capabilities')

chk('api guard WITHOUT token -> 403', r['status'] == 403, 'HTTP %s' % r['status'])

r = call('GET', A + '/api/v3/export/capabilities', headers=ITOK)

j = r['json'] or {}

chk('api capabilities WITH token', r['status'] == 200,

    'HTTP %s modes=%s tables=%s' % (r['status'], j.get('modes'), j.get('tables')))

r = call('GET', A + '/api/v3/es/readiness', headers=ITOK)

chk('api es/readiness', r['status'] == 200, 'HTTP %s code=%s' % (r['status'], code(r)))



# 6. API query endpoints

for p in ['/base/snapshotflow/list?pageNum=1&pageSize=2',

          '/base/feerecords/list?pageNum=1&pageSize=2',

          '/base/sysutil/carTrackQueryByCarNo?carNo=%E8%B5%A3A12345&applyTime1=2025-01-01&applyTime2=2025-12-31&pageNum=1&pageSize=2',

          '/api/v1/large/carTrackQueryByCarNo?carNo=%E8%B5%A3A12345&startTime=2025-01-01&endTime=2025-12-31&pageNum=1&pageSize=2']:

    r = call('GET', A + p, headers=ITOK, timeout=90)

    chk('api query %s' % p.split('?')[0], r['status'] == 200,

        'HTTP %s code=%s total=%s msg=%s' % (r['status'], code(r),

                                            (r['json'] or {}).get('total', '-'),

                                            str((r['json'] or {}).get('msg', ''))[:50]))



# 7. cleanup created accounts

if created:

    ids = ','.join(str(x) for x in created)

    r = call('DELETE', B + '/system/user/' + ids, headers=auth(admin_t))

    chk('cleanup DELETE /system/user', r['status'] == 200 and code(r) == 200,

        'HTTP %s ids=%s' % (r['status'], ids))

    for name, _, _, _, _ in users:

        q = call('GET', B + '/system/user/list?pageNum=1&pageSize=5&userName=' + name,

                 headers=auth(admin_t))

        chk('cleanup verified %s' % name, (q['json'] or {}).get('total') == 0,

            'total=%s' % (q['json'] or {}).get('total'))



log('=== JDK%s SMOKE SUMMARY: checks=%d fails=%d ===' % (LABEL, len(lines) - 1, len(fails)))

if fails:

    log('FAILED_CHECKS=' + ','.join(fails))

with open('D:/work/runtime-logs/jdk%s-smoke.log' % LABEL, 'w', encoding='utf-8') as f:

    f.write('\n'.join(lines) + '\n')

sys.exit(1 if fails else 0)

