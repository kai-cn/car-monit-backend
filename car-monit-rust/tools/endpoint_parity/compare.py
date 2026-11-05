# -*- coding: utf-8 -*-
"""Java ↔ Rust 逐端点 GET 响应对比。

两端地址、账号、输出路径都由参数或环境变量提供，便于本机复跑与 CI 调用：

    python -m tools.endpoint_parity.compare --java-base http://127.0.0.1:9988 \
        --rust-base http://127.0.0.1:9990 --report build/parity-report.json --strict

分类：OK（结构/值/类型一致）、WARN（仅键顺序、错误文案、total 动态波动）、
FAIL（硬差异）、KNOWN（上游不可用或 Java 自身故障）、SKIP（有副作用，不请求）。
"""
import argparse, json, os, re, sys, time, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from client import login, http

HERE = Path(__file__).resolve().parent

# 环境变量优先，命令行再覆盖；默认值只面向 127.0.0.1 的本地实例。
JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')
ENDPOINTS = Path(os.environ.get('PARITY_ENDPOINTS', str(HERE / 'endpoints.json')))
REPORT = Path(os.environ.get('PARITY_REPORT', str(HERE / 'report.json')))

S = dict(
    fwqbm='zdy_wafwq', warning_id='9a00a4b44c18ab6fd60ae84724122dd8',
    fwqjcxx='1', sfsjcxx='d2c6df4afa7ff18d48786d728d3919d2',
    sfzjcxx='363bc7b76e508c55dcb259cf6a3f007e', geometry='33847',
    feegantry='G007036001013020100402024102619000045',
    feeenter='2308',
    feeexit='G007036004008020100202025012910271355',
    snapshot_bigid='10', prov_bigid='18', stat_bigid='15188899', org_bigid='24943',
    gantry='1', section='1', toll='1', location='1',
    fitting='0149bd0d4ba74a858cce0ed577fefc89',
    tracks='36c2c3d423754228a38ece29d7d74da1',
    apply_id='08eb8bd8af804fc09b6cbeefbbdf73f0',
    flowname_id='76dd91f205764597bbcde1c5b79a4793',
    buss_id='3e7db98f9ff74ea1b6840d72209771ad',
    aduit_id='0031127052b3ec106a7bbec00e6d3dc7',
    confim_id='0ac116f04798d093c27662e8dd2a9bcb',
    except_ids='bb96914b174a30607d9b9c9c49a981e7',
    except_record_id='01854222655b817f3bbe1b2431813735',
    querylog_id='000cc7014a9286d860f540efe7001e26',
    suspicious_back_id='12a0ec868e0f018a9fbaa7f0ec6b5e62',
    suspicious_check_id='0095e86ba4aa40afd230a93abab4df5b',
    suspicious_id='1b5905dceb31f3cbbf66f7d8d154e4ab',
    track_id='1',
    warninginfo_id='1a54d61a03efe4bab146c551a93a530d',
    warningrule_id='20a28e0eacb3b3d2bb8d6cb7b1b36fd8',
    white_id='054a4d364b2e7415f0d3628a460871dc',
    gantrycar_id='63cd4a749613496f5dcdcc1700a8d51e',
    gantrytrade_id='76381861e3b79830c00449e5d9c2470c',
    job_id='1', joblog_id='1', config_id='1', dept_id='25367', role_id='1',
    role_key='admin', dict_code='1', dict_id='178',
    dict_type='boundary_gantry_type', menu_id='1', notice_id='532', post_id='1',
    user_id='1', indexmenu_id='89', file_id='1293892177784471552',
    file_bucket='developer',
    file_name='8d81fd022dc745bcbd766480902fceb0.docx',
    gen_table_id='231', gen_table_name='car_except_record',
    weight_ds='ZdTrails:BorderWeighing', template_type='carinfo',
)

# (regex, {placeholder: sample-key})
RULES = [
    (r'^/base/configServiceArea/\{fwqbm\}$', {'fwqbm': 'fwqbm'}),
    (r'^/base/config/\{id\}$', {'id': 'warning_id'}),
    (r'^/base/fwqjcxx/\{agentPk\}$', {'agentPk': 'fwqjcxx'}),
    (r'^/base/sfsjcxx/\{agentPk\}$', {'agentPk': 'sfsjcxx'}),
    (r'^/base/sfzjcxx/\{agentPk\}$', {'agentPk': 'sfzjcxx'}),
    (r'^/base/geometry/\{ID\}$', {'ID': 'geometry'}),
    (r'^/manager/fwqclls/\{bigId\}$', {'bigId': '1'}),
    (r'^/base/feeGantry/\{bigId\}$', {'bigId': 'feegantry'}),
    (r'^/base/feerecords/\{bigId\}$', {'bigId': '1'}),
    (r'^/base/feeStationEnter/\{bigId\}$', {'bigId': 'feeenter'}),
    (r'^/base/feestationexit/\{bigId\}$', {'bigId': 'feeexit'}),
    (r'^/base/snapshotflow/\{bigId\}$', {'bigId': 'snapshot_bigid'}),
    (r'^/base/provcapture/\{bigId\}$', {'bigId': 'prov_bigid'}),
    (r'^/base/stationcapture/\{bigId\}$', {'bigId': 'stat_bigid'}),
    (r'^/base/gantry/\{id\}$', {'id': 'gantry'}),
    (r'^/base/gantryIp/\{id\}$', {'id': '1'}),
    (r'^/base/vehicleweight/\{dataSource\}$', {'dataSource': 'weight_ds'}),
    (r'^/base/section/\{id\}$', {'id': 'section'}),
    (r'^/base/toll/\{id\}$', {'id': 'toll'}),
    (r'^/base/tollStationIp/\{id\}$', {'id': '1'}),
    (r'^/base/org/\{bigId\}$', {'bigId': 'org_bigid'}),
    (r'^/base/location/\{id\}$', {'id': 'location'}),
    (r'^/base/fitting/\{cid\}$', {'cid': 'fitting'}),
    (r'^/base/trailtracks/\{uuid\}$', {'uuid': 'tracks'}),
    (r'^/downTemplate/\{type\}$', {'type': 'template_type'}),
    (r'^/flow/applyinfo/\{id\}$', {'id': 'apply_id'}),
    (r'^/flow/currentnode/\{id\}$', {'id': '1'}),
    (r'^/flow/currentnode/getInfoByBillId/\{billOid\}$', {'billOid': '1'}),
    (r'^/flow/flowlist/\{id\}$', {'id': '1'}),
    (r'^/flow/messagedispose/\{id\}$', {'id': '1'}),
    (r'^/flow/messageinfo/\{id\}$', {'id': '1'}),
    (r'^/flow/flowname/\{id\}$', {'id': 'flowname_id'}),
    (r'^/flow/flowtemplate/\{id\}$', {'id': '1'}),
    (r'^/tool/gen/\{talbleId\}$', {'talbleId': 'gen_table_id'}),
    (r'^/tool/gen/column/\{talbleId\}$', {'talbleId': 'gen_table_id'}),
    (r'^/tool/gen/preview/\{tableId\}$', {'tableId': 'gen_table_id'}),
    (r'^/tool/gen/download/\{tableName\}$', {'tableName': 'gen_table_name'}),
    (r'^/tool/gen/genCode/\{tableName\}$', {'tableName': 'gen_table_name'}),
    (r'^/tool/gen/synchDb/\{tableName\}$', {'tableName': 'gen_table_name'}),
    (r'^/manager/busstest/\{id\}$', {'id': 'buss_id'}),
    (r'^/manager/aduitfree/\{id\}$', {'id': 'aduit_id'}),
    (r'^/manager/confimfree/\{id\}$', {'id': 'confim_id'}),
    (r'^/manager/confimfree/except/\{exceptIds\}$', {'exceptIds': 'except_ids'}),
    (r'^/manager/exceptrecord/\{id\}$', {'id': 'except_record_id'}),
    (r'^/manager/exceptrecord/getConfirmId/\{id\}$', {'id': 'except_record_id'}),
    (r'^/manager/feerecord/\{id\}$', {'id': '1'}),
    (r'^/manager/carinfo/\{id\}$', {'id': '1'}),
    (r'^/manager/querylog/\{id\}$', {'id': 'querylog_id'}),
    (r'^/manager/routedetail/\{id\}$', {'id': '1'}),
    (r'^/manager/routeinfo/\{id\}$', {'id': '1'}),
    (r'^/manager/splitrecord/\{id\}$', {'id': '1'}),
    (r'^/manager/carsuspiciousback/\{id\}$', {'id': 'suspicious_back_id'}),
    (r'^/manager/suspiciouscheck/\{id\}$', {'id': 'suspicious_check_id'}),
    (r'^/manager/suspicious/\{id\}$', {'id': 'suspicious_id'}),
    (r'^/manager/suspicious/history/\{id\}$', {'id': 'suspicious_id'}),
    (r'^/manager/cartrackinfo/\{id\}$', {'id': 'track_id'}),
    (r'^/manager/carwarning/\{id\}$', {'id': 'warninginfo_id'}),
    (r'^/manager/warningrule/\{id\}$', {'id': 'warningrule_id'}),
    (r'^/manager/whiteinfo/\{id\}$', {'id': 'white_id'}),
    (r'^/manager/gantrycar/\{id\}$', {'id': 'gantrycar_id'}),
    (r'^/manager/gantrytrade/\{id\}$', {'id': 'gantrytrade_id'}),
    (r'^/monitor/job/\{jobId\}$', {'jobId': 'job_id'}),
    (r'^/monitor/jobLog/\{configId\}$', {'configId': 'joblog_id'}),
    (r'^/system/config/\{configId\}$', {'configId': 'config_id'}),
    (r'^/system/config/configKey/\{configKey\}$', {'configKey': 'config_key'}),
    (r'^/system/dept/list/exclude/\{deptId\}$', {'deptId': 'dept_id'}),
    (r'^/system/dept/\{deptId\}$', {'deptId': 'dept_id'}),
    (r'^/system/dept/roleDeptTreeselect/\{roleId\}$', {'roleId': 'role_id'}),
    (r'^/system/dict/data/\{dictCode\}$', {'dictCode': 'dict_code'}),
    (r'^/system/dict/data/type/\{dictType\}$', {'dictType': 'dict_type'}),
    (r'^/system/dict/data/typemore/\{dictType\}$', {'dictType': 'dict_type'}),
    (r'^/system/dict/type/\{dictId\}$', {'dictId': 'dict_id'}),
    (r'^/system/file/getInfoById/\{id\}$', {'id': 'file_id'}),
    (r'^/system/file/\{ids\}$', {'ids': 'file_id'}),
    (r'^/system/file/\{bucket\}/\{fileName\}$', {'bucket': 'file_bucket', 'fileName': 'file_name'}),
    (r'^/system/file/view/\{bucket\}/\{fileName\}$', {'bucket': 'file_bucket', 'fileName': 'file_name'}),
    (r'^/system/indexmenu/\{id\}$', {'id': 'indexmenu_id'}),
    (r'^/system/menu/\{menuId\}$', {'menuId': 'menu_id'}),
    (r'^/system/menu/roleMenuTreeselect/\{roleId\}$', {'roleId': 'role_id'}),
    (r'^/system/notice/\{noticeId\}$', {'noticeId': 'notice_id'}),
    (r'^/system/notice/view/\{noticeId\}$', {'noticeId': 'notice_id'}),
    (r'^/system/post/\{postId\}$', {'postId': 'post_id'}),
    (r'^/system/role/\{roleId\}$', {'roleId': 'role_id'}),
    (r'^/system/upgradeInfo/\{id\}$', {'id': '1'}),
    (r'^/system/user/\{userId\}$', {'userId': 'user_id'}),
    (r'^/system/user/getroleUser/\{roleCode\}$', {'roleCode': 'role_key'}),
    (r'^/test/user/\{userId\}$', {'userId': '1'}),
]

S['config_key'] = 'sys.index.skinName'

SKIP = {
    '/base/geometry/syncAllGeometry',
    '/base/geometry/syncAllGeometry1',
    '/tool/gen/synchDb/{tableName}',
}
KNOWN = {
    '/tool/gen/preview/{tableId}', '/tool/gen/genCode/{tableName}',
    '/tool/gen/download/{tableName}', '/tool/gen/batchGenCode',
    '/system/upgradeInfo/list', '/system/upgradeInfo/newest',
    '/system/upgradeInfo/export', '/system/upgradeInfo/{id}',
    '/base/cdc/config',
    '/base/feeGantry/{bigId}',
    '/base/snapshotflow/{bigId}',
    '/base/feestationexit/list',
    '/base/feestationexit/{bigId}',
    '/base/geometry/getHenDa',
    '/monitor/server',
    '/base/feeGantry/list',
    '/base/snapshotflow/earliest-time',
}

DYNAMIC = (
    '/monitor/operlog', '/monitor/logininfor', '/monitor/online',
     '/system/user/list', '/system/user/', '/system/user/{userId}',
    '/manager/querylog', '/monitor/cache',
)

# 透传 vehicleMonitor 上游（`vehicleMonitor.baseUrl`）的端点：上游每次请求都
# 重新生成主键/时间，值不可比。只比结构（键集合、类型、长度），不比值。
SHAPE_ONLY = (
    '/base/feeGantry/list',
    '/base/feerecords/list',
    '/base/feestationexit/list',
    '/base/snapshotflow/list',
)

# 外部实时路径服务（本地路网规划 / 腾讯 direction）的返回值随路网数据刷新变化：
# 同一时间窗口内双端逐字节一致，跨窗口取到的路线点数会差几个。只比结构不比这个标量。
VALUE_FREE = {
    '/manager/suspicious/{id}': re.compile(r'\.paths$'),
}

SPECIAL_Q = {
    '/manager/suspicious/exportAbnormalPassage': {'carSuspiciousId': S['suspicious_id']},
    '/common/download': {'fileName': 'developer/' + S['file_name'], 'delete': 'false'},
    '/common/download/resource': {'resource': 'developer/' + S['file_name']},
    '/tool/gen/batchGenCode': {'tables': S['gen_table_name']},
}

SLOW = ('/export', '/download', '/importTemplate', '/downTemplate/', '/genCode',
        '/preview', '/batchGenCode', '/file/view/', '/view/',
        # 可疑车辆详情会走外部路网/腾讯地图，慢的时候按 240s 等。
        '/manager/suspicious/')


def resolve(pattern):
    for rx, mapping in RULES:
        if re.fullmatch(rx, pattern):
            return mapping
    return None


def build_url(base, pattern):
    mapping = resolve(pattern)
    path = pattern
    if mapping:
        def sub(m):
            ph = m.group(1)
            return urllib.parse.quote(str(S.get(mapping.get(ph, ''), '1')), safe='')
        path = re.sub(r'\{([^}/]+)\}', sub, path)
    q = {'pageNum': '1', 'pageSize': '10'}
    if pattern in SPECIAL_Q:
        q.update(SPECIAL_Q[pattern])
    return base + path + '?' + urllib.parse.urlencode(q)


def is_slow(pattern):
    return any(k in pattern for k in SLOW)


DYN_KEYS = re.compile(r'(loginDate|loginIp|createTime|updateTime|token|uuid|img|pwdUpdateDate|online|lastLogin|nextValidTime)', re.I)


def compare_json(a, b, path='', issues=None, dyn=False, depth=0, cap=5, shape=False, free=None):
    # shape=True：上游随机生成的值只比结构，不比标量值（见 SHAPE_ONLY）。
    # free=正则：命中的标量路径不比值（见 VALUE_FREE，外部实时路网结果）。
    if issues is None:
        issues = []
    if len(issues) > 60:
        return issues
    if type(a) is not type(b):
        if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
            issues.append(('TYPE-DIFF', path, a, b))
            return issues
        if shape:
            return issues
        if isinstance(a, bool) or isinstance(b, bool):
            issues.append(('TYPE-DIFF', path, a, b))
            return issues
        if isinstance(a, (int, float)) and isinstance(b, str):
            if str(a) == str(b):
                issues.append(('TYPE-DIFF', path, a, b))
            else:
                issues.append(('VALUE-DIFF', path, a, b))
            return issues
        if isinstance(a, str) and isinstance(b, (int, float)):
            if str(a) == str(b):
                issues.append(('TYPE-DIFF', path, a, b))
            else:
                issues.append(('VALUE-DIFF', path, a, b))
            return issues
        issues.append(('TYPE-DIFF', path, a, b))
        return issues
    if isinstance(a, dict):
        if path == '':
            # code/msg 由外层单独比较，避免重复计为硬差异。
            a = {k: v for k, v in a.items() if k not in ('code', 'msg')}
            b = {k: v for k, v in b.items() if k not in ('code', 'msg')}
        ka, kb = list(a.keys()), list(b.keys())
        if ka != kb:
            if set(ka) == set(kb):
                issues.append(('ORDER-DIFF', path, ka[:8], kb[:8]))
            else:
                for k in ka:
                    if k not in b:
                        issues.append(('MISSING', path + '.' + k if path else k, a[k], '<absent>'))
                for k in kb:
                    if k not in a:
                        issues.append(('EXTRA', path + '.' + k if path else k, '<absent>', b[k]))
        for k in ka:
            if k in b:
                # 只有**键名**命中 DYN_KEYS 才跳过标量值。
                # 原先写成 `dyn or ...`，等于把整个动态端点的值比较全关了 —— /system/user/list
                # 的 deptName/subCode/pjFlag 差异就是这样被漏掉的。
                sub_dyn = bool(DYN_KEYS.search(str(k)))
                if sub_dyn and not isinstance(a[k], (dict, list)) and not isinstance(b[k], (dict, list)):
                    continue
                compare_json(a[k], b[k], path + '.' + k if path else k, issues, dyn, depth + 1, cap, shape, free)
        return issues
    if isinstance(a, list):
        if len(a) != len(b):
            issues.append(('LEN-DIFF', path, len(a), len(b)))
        for i in range(min(len(a), len(b), cap)):
            compare_json(a[i], b[i], '%s[%d]' % (path, i), issues, dyn, depth + 1, cap, shape, free)
        return issues
    if a != b and not shape and not (free is not None and free.search(path)):
        issues.append(('VALUE-DIFF', path, a, b))
    return issues


def decode(resp):
    st, h, b = resp
    ct = ''
    for k, v in h.items():
        if k.lower() == 'content-type':
            ct = v
            break
    if not b:
        return st, ct, b, None, False
    if 'json' in ct.lower() or b[:1] in (b'{', b'['):
        try:
            return st, ct, b, json.loads(b), True
        except Exception:
            return st, ct, b, None, False
    return st, ct, b, None, False


BIN_PAT = ('/export', '/download', '/importTemplate', '/downTemplate/',
           '/file/view/', '/view/', '/genCode', '/batchGenCode', '/system/file/{bucket}')


UUID_RE = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
# 上游/导出报文里的时间戳与毫秒时间戳每次都不同，归一后再比 msg 文案。
TS_RE = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?|\b1[0-9]{12}\b')


def norm_uuid(value):
    if not isinstance(value, str):
        return value
    return TS_RE.sub('<ts>', UUID_RE.sub('<uuid>', value))


def compare_one(tokens, row, java_base=None, rust_base=None):
    pattern, method = row['path'], row['method']
    assert method == 'GET'
    if pattern in SKIP:
        return dict(idx=row['idx'], path=pattern, status='SKIP', issues=[])
    known = pattern in KNOWN
    java_base = java_base or JAVA
    rust_base = rust_base or RUST

    timeout = 240 if is_slow(pattern) else 45
    url_j = build_url(java_base, pattern)
    url_r = build_url(rust_base, pattern)
    # SecurityConfig.anonymous()：带 token 反而 403，需匿名访问。
    anon = pattern == '/common/download' or pattern.startswith('/system/file/view/')         or pattern.startswith('/system/notice/view/')
    tj, tr_ = (None, None) if anon else tokens
    t0 = time.time()
    jr = http('GET', url_j, token=tj, timeout=timeout)
    tr = time.time() - t0
    t0 = time.time()
    rr = http('GET', url_r, token=tr_, timeout=timeout)
    trr = time.time() - t0
    sj, cj, bj, jj, jjson = decode(jr)
    sr, cr, br, rj, rjson = decode(rr)
    issues = []
    shape = pattern in SHAPE_ONLY

    if sj != sr:
        issues.append(('STATUS-DIFF', '$status', sj, sr))
    if jjson and rjson:
        dyn = any(pattern.startswith(p) for p in DYNAMIC)
        compare_json(jj, rj, '', issues, dyn, 0, 5, shape, VALUE_FREE.get(pattern))
        cj_code, cr_code = jj.get('code') if isinstance(jj, dict) else None, rj.get('code') if isinstance(rj, dict) else None
        if cj_code != cr_code:
            issues.append(('CODE-DIFF', '$.code', cj_code, cr_code))
        mj = jj.get('msg') if isinstance(jj, dict) else None
        mr = rj.get('msg') if isinstance(rj, dict) else None
        if norm_uuid(mj) != norm_uuid(mr):
            issues.append(('MSG-DIFF', '$.msg', mj, mr))
        if 'total' in jj and 'total' in rj and jj['total'] != rj['total']:
            if dyn:
                issues.append(('TOTAL-WARN', '$.total', jj['total'], rj['total']))
            else:
                issues.append(('TOTAL-DIFF', '$.total', jj['total'], rj['total']))
        kind = 'JSON'
    elif (not bj) and (not br):
        kind = 'EMPTY'
    elif (not jjson) and (not rjson) and bj and br:
        mk = lambda x: x[:2]
        if sj == sr and mk(bj) != mk(br) and any(k in pattern for k in BIN_PAT):
            issues.append(('BIN-DIFF', '$magic', mk(bj).hex(), mk(br).hex()))
        elif sj == sr and (len(bj) == 0) != (len(br) == 0):
            issues.append(('BIN-DIFF', '$len', len(bj), len(br)))
        kind = 'BINARY'
    else:
        issues.append(('JSON-BINARY-DIFF', '$kind', 'json' if jjson else ('binary' if bj else 'empty'),
                       'json' if rjson else ('binary' if br else 'empty')))
        kind = 'MIXED'

    hard = [i for i in issues if i[0] in
            ('STATUS-DIFF', 'CODE-DIFF', 'MISSING', 'EXTRA', 'LEN-DIFF', 'TOTAL-DIFF',
             'VALUE-DIFF', 'TYPE-DIFF', 'BIN-DIFF', 'JSON-BINARY-DIFF')]
    warn = [i for i in issues if i[0] in ('MSG-DIFF', 'ORDER-DIFF', 'TOTAL-WARN')]
    status = 'FAIL' if hard else ('WARN' if warn else 'OK')
    if known and status == 'FAIL':
        status = 'KNOWN'
    return dict(idx=row['idx'], path=pattern, method='GET', kind=kind, status=status,
                j_status=sj, r_status=sr, j_ms=round(tr * 1000), r_ms=round(trr * 1000),
                j_len=len(bj or b''), r_len=len(br or b''), issues=issues[:30],
                j_code=(jj.get('code') if isinstance(jj, dict) else None),
                r_code=(rj.get('code') if isinstance(rj, dict) else None))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='Java ↔ Rust GET 端点逐一对比（需两端已启动、同库同 Redis）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('--java-base', default=JAVA, help='Java 基址（默认 PARITY_JAVA_BASE）')
    parser.add_argument('--rust-base', default=RUST, help='Rust 基址（默认 PARITY_RUST_BASE）')
    parser.add_argument('--endpoints', default=str(ENDPOINTS), help='端点清单 JSON（tools.endpoint_parity.endpoints 生成）')
    parser.add_argument('--report', default=str(REPORT), help='对比结果输出路径')
    parser.add_argument('--only', action='append', default=[], help='只跑这些前缀，可重复')
    parser.add_argument('--skip', action='append', default=[], help='额外跳过这些前缀，可重复')
    parser.add_argument('--workers', type=int, default=int(os.environ.get('PARITY_WORKERS', '6')))
    parser.add_argument('--strict', action='store_true', help='存在 FAIL 时退出码 1（CI 用）')
    parser.add_argument('--quiet', action='store_true', help='只打印汇总，不列 WARN 明细')
    args = parser.parse_args(argv)

    endpoints_path = Path(args.endpoints)
    if not endpoints_path.exists():
        print('端点清单不存在：%s\n先运行：python -m tools.endpoint_parity.endpoints' % endpoints_path, file=sys.stderr)
        return 2
    rows = json.loads(endpoints_path.read_text(encoding='utf-8'))
    gets = [r for r in rows if r['method'] == 'GET']
    if args.only:
        gets = [r for r in gets if any(r['path'].startswith(prefix) for prefix in args.only)]
    skip_extra = tuple(args.skip or [])
    if skip_extra:
        gets = [r for r in gets if not r['path'].startswith(skip_extra)]
    if not gets:
        print('没有匹配的 GET 端点', file=sys.stderr)
        return 2

    tj, stj, jsj = login(args.java_base)
    tr, str_, jsr = login(args.rust_base)
    if not tj or not tr:
        print('LOGIN FAILED java=(%s,%s) rust=(%s,%s)' % (stj, jsj, str_, jsr), file=sys.stderr)
        return 2
    print('java=%s rust=%s logged in, %d GET endpoints' % (args.java_base, args.rust_base, len(gets)))

    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = [ex.submit(compare_one, (tj, tr), r, args.java_base, args.rust_base) for r in gets]
        for f in as_completed(futs):
            results.append(f.result())
    results.sort(key=lambda x: x['idx'])
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')

    from collections import Counter
    c = Counter(r['status'] for r in results)
    print('\n=== SUMMARY ===')
    print('GET total=%d OK=%d WARN=%d FAIL=%d KNOWN=%d SKIP=%d' %
          (len(results), c['OK'], c['WARN'], c['FAIL'], c['KNOWN'], c['SKIP']))
    print('report -> %s' % report_path)
    fails = [r for r in results if r['status'] == 'FAIL']
    warns = [r for r in results if r['status'] == 'WARN']
    print('\n--- FAIL (%d) ---' % len(fails))
    for r in fails:
        print('#%d %s code=%s/%s' % (r['idx'], r['path'], r.get('j_code'), r.get('r_code')))
        for i in r['issues'][:6]:
            print('   ', i[0], i[1], repr(i[2])[:90], '!=', repr(i[3])[:90])
    if not args.quiet:
        print('\n--- WARN (%d) ---' % len(warns))
        for r in warns:
            print('#%d %s %s' % (r['idx'], r['path'], r['issues'][:2]))
    return 1 if (args.strict and fails) else 0


if __name__ == '__main__':
    raise SystemExit(main())
