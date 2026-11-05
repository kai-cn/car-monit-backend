# -*- coding: utf-8 -*-
"""「新增」端点的冒烟对拍（写入路径的两类回归守门）。

1. `select last_insert_id()` 的列元信息是 BIGINT UNSIGNED，早先按 i64 解码会在事务里
   取回自增主键时直接报错 -> 整笔新增回滚 -> 接口恒 500，而 GET 全量对拍看不见这条路径。
2. RuoYi 前端的每个请求体都带 `params`（`BaseEntity.params`），MP 的
   `@TableField(exist = false)` 字段（`applyTime1` 等）也一起送；Java 的 Jackson 忽略它们，
   Rust 原先原样拼进 INSERT -> `1054 Unknown column 'params'`，真实前端请求下只有 Rust 是 500。
   所以每个用例都跑**两遍**：干净请求体，和掺了非列字段的请求体；
   同一端两遍结果必须一致（说明这些字段真的被忽略），两端之间也必须一致。

两端共用一个库，所以探针名带端别标记（-J / -R），比较的也只是「自己那行有没有建出来」，
不比较行数（否则后跑的一端会看到先跑那端的行）。

用法（两端已启动）：
    PARITY_USER=admin PARITY_PASSWORD=xxx python -m tools.endpoint_parity.post_smoke_matrix
"""
from __future__ import annotations

import copy
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client import http, login  # noqa: E402

JAVA = os.environ.get('PARITY_JAVA_BASE', 'http://127.0.0.1:9988')
RUST = os.environ.get('PARITY_RUST_BASE', 'http://127.0.0.1:9990')

SUFFIX = str(int(time.time()))[-6:]

#: 前端真实会带、但都不是数据库列的字段（含一个彻底不存在的键）。
JUNK = {
    'params': {'beginTime': '2025-01-01 00:00:00', 'endTime': ''},
    'pageDomain': {'pageSize': 10, 'pageNum': 1},
    'applyTime1': '2025-01-01',
    'applyTime2': '2025-12-31',
    'unknownFieldZz': 1,
}


def msg_of(raw):
    try:
        return json.loads(raw).get('msg')
    except Exception:
        return 'NON-JSON %s' % raw[:120].decode('utf-8', 'replace')


def call(method, base, token, path, body=None):
    _, _, raw = http(method, base + path, token=token, body=body, timeout=90)
    return msg_of(raw)


def rows_of(base, token, path, params=''):
    _, _, raw = http('GET', base + path + params, token=token, timeout=90)
    try:
        return (json.loads(raw) or {}).get('rows') or []
    except Exception:
        return []


def with_junk(body, extra):
    merged = copy.deepcopy(body)
    merged.update(copy.deepcopy(extra) if extra else {})
    return merged


def smoke_job(base, token, tag, extra=None):
    name = 'parity-smoke-job-%s-%s' % (SUFFIX, tag)
    body = with_junk({
        'jobName': name, 'jobGroup': 'DEFAULT', 'invokeTarget': 'ryTask.ryNoParams',
        'cronExpression': '0 0 3 * * ?', 'misfirePolicy': '3', 'concurrent': '1',
        'status': '1'}, extra)
    out = {'add': call('POST', base, token, '/monitor/job', body)}
    rows = rows_of(base, token, '/monitor/job/list', '?jobName=' + name)
    out['found'] = len(rows)
    if rows:
        # Java 的 insertJob 会强制 status='1'，这里请求体给的是 '0'（下面单独用例校验）。
        out['status'] = rows[0].get('status')
        out['nextValidTime'] = bool(rows[0].get('nextValidTime'))
        call('DELETE', base, token, '/monitor/job/%s' % rows[0]['jobId'])
    return out


def smoke_user(base, token, tag, extra=None, dept_id=25367, marker=''):
    """dept_id 用库里真实存在的部门（25367），Java 才能走完 insertUser。"""
    name = 'paritysmoke%s%s%s' % (SUFFIX, tag, marker)
    body = with_junk({
        'userName': name, 'nickName': 'parity-smoke', 'password': 'Admin@123456',
        'deptId': dept_id, 'status': '0', 'phonenumber': '158000%s' % SUFFIX,
        'roleIds': [2], 'postIds': []}, extra)
    out = {'add': call('POST', base, token, '/system/user', body)}
    rows = rows_of(base, token, '/system/user/list', '?userName=' + name)
    out['found'] = len(rows)
    if rows:
        out['nickName'] = rows[0].get('nickName')
        out['bussName'] = rows[0].get('bussName')
        out['tenantId'] = rows[0].get('tenantId')
        call('DELETE', base, token, '/system/user/%s' % rows[0]['userId'])
    return out


def smoke_user_missing_dept(base, token, tag, extra=None):
    """Java: insertUser 里 `sysDept.getDeptName()` 对不存在的部门直接 NPE。"""
    return smoke_user(base, token, tag, extra, dept_id=103, marker='x')


def smoke_role(base, token, tag, extra=None):
    key = 'parity:smoke:%s%s' % (SUFFIX, tag)
    body = with_junk({
        'roleName': 'parity-smoke-%s-%s' % (SUFFIX, tag), 'roleKey': key, 'roleSort': 9,
        'dataScope': '1', 'status': '0', 'menuIds': [], 'deptIds': []}, extra)
    out = {'add': call('POST', base, token, '/system/role', body)}
    rows = rows_of(base, token, '/system/role/list', '?roleKey=' + key)
    out['found'] = len(rows)
    if rows:
        call('DELETE', base, token, '/system/role/%s' % rows[0]['roleId'])
    return out


def smoke_dept(base, token, tag, extra=None):
    name = 'parity-smoke-%s-%s' % (SUFFIX, tag)
    body = with_junk({'parentId': 100, 'deptName': name, 'orderNum': 9, 'status': '0'}, extra)
    out = {'add': call('POST', base, token, '/system/dept', body)}
    rows = rows_of(base, token, '/system/dept/list', '?deptName=' + name)
    out['found'] = len(rows)
    if rows:
        call('DELETE', base, token, '/system/dept/%s' % rows[0]['deptId'])
    return out


def smoke_post(base, token, tag, extra=None):
    code = 'parity_post_%s%s' % (SUFFIX, tag)
    body = with_junk({'postCode': code, 'postName': 'parity-smoke-%s' % tag, 'postSort': 9,
                      'status': '0', 'remark': 'parityW%s' % SUFFIX}, extra)
    out = {'add': call('POST', base, token, '/system/post', body)}
    rows = rows_of(base, token, '/system/post/list', '?postCode=' + code)
    out['found'] = len(rows)
    if rows:
        call('DELETE', base, token, '/system/post/%s' % rows[0]['postId'])
    return out


def smoke_config(base, token, tag, extra=None):
    key = 'parity.config.%s%s' % (SUFFIX, tag)
    body = with_junk({'configName': 'parity-smoke-%s' % tag, 'configKey': key,
                      'configValue': '1', 'configType': 'Y',
                      'remark': 'parityW%s' % SUFFIX}, extra)
    out = {'add': call('POST', base, token, '/system/config', body)}
    rows = rows_of(base, token, '/system/config/list', '?configKey=' + key)
    out['found'] = len(rows)
    if rows:
        call('DELETE', base, token, '/system/config/%s' % rows[0]['configId'])
    return out


def smoke_dict_type(base, token, tag, extra=None):
    name = 'parity_dict_%s%s' % (SUFFIX, tag)
    body = with_junk({'dictName': 'parity-smoke-%s' % tag, 'dictType': name, 'status': '0',
                      'remark': 'parityW%s' % SUFFIX}, extra)
    out = {'add': call('POST', base, token, '/system/dict/type', body)}
    rows = rows_of(base, token, '/system/dict/type/list', '?dictType=' + name)
    out['found'] = len(rows)
    for row in rows:
        out['delete'] = call('DELETE', base, token, '/system/dict/type/%s' % row['dictId'])
    return out


def smoke_dict_data(base, token, tag, extra=None):
    body = with_junk({'dictSort': 9, 'dictLabel': 'parity-smoke-%s' % tag,
                      'dictValue': 'p%s' % tag, 'dictType': 'sys_yes_no', 'status': '0',
                      'remark': 'parityW%s' % SUFFIX}, extra)
    out = {'add': call('POST', base, token, '/system/dict/data', body)}
    rows = rows_of(base, token, '/system/dict/data/list',
                   '?dictType=sys_yes_no&dictLabel=parity-smoke-%s' % tag)
    out['found'] = len(rows)
    for row in rows:
        out['delete'] = call('DELETE', base, token, '/system/dict/data/%s' % row['dictCode'])
    return out


def smoke_notice(base, token, tag, extra=None):
    body = with_junk({'noticeTitle': 'parity-smoke-%s' % tag, 'noticeType': '0',
                      'noticeContent': 'parityW%s' % SUFFIX, 'status': '0'}, extra)
    out = {'add': call('POST', base, token, '/system/notice', body)}
    rows = rows_of(base, token, '/system/notice/list', '?noticeTitle=parity-smoke-%s' % tag)
    out['found'] = len(rows)
    for row in rows:
        out['delete'] = call('DELETE', base, token, '/system/notice/%s' % row['noticeId'])
    return out


def smoke_menu(base, token, tag, extra=None):
    body = with_junk({'menuName': 'parity-smoke-%s-%s' % (SUFFIX, tag), 'parentId': 0,
                      'orderNum': 9, 'path': 'parity%s' % tag, 'component': '',
                      'menuType': 'C', 'visible': '0', 'status': '0',
                      'perms': '', 'icon': '#'}, extra)
    out = {'add': call('POST', base, token, '/system/menu', body)}
    rows = rows_of(base, token, '/system/menu/list',
                   '?menuName=parity-smoke-%s-%s' % (SUFFIX, tag))
    out['found'] = len(rows)
    for row in rows:
        out['delete'] = call('DELETE', base, token, '/system/menu/%s' % row['menuId'])
    return out


def smoke_carinfo(base, token, tag, extra=None):
    """`POST /manager/carinfo`：Java 先按车牌判重，再自己 setUUID（IdType.INPUT 的例外）。"""
    plate = 'parityJ%s%s' % (SUFFIX, tag)
    body = with_junk({'carNo': plate, 'carType': '1', 'carVehicle': '1', 'carNum': 1,
                      'escapedAmount': 1.5, 'remark': 'parityW%s' % SUFFIX}, extra)
    out = {'add': call('POST', base, token, '/manager/carinfo', body)}
    rows = rows_of(base, token, '/manager/carinfo/list', '?carNo=' + plate)
    out['found'] = len(rows)
    for row in rows:
        out['delete'] = call('DELETE', base, token, '/manager/carinfo/%s' % row['id'])
    # 同车牌再发一次：Java 的判重分支（“车牌号存在重复，请确定！”）两端也要一致。
    if rows:
        out['again'] = call('POST', base, token, '/manager/carinfo', body)
    return out


def smoke_suspicious_back(base, token, tag, extra=None):
    """Java: `IdType.INPUT` 且 service 不 setUUID —— 不带 id 的新增必然失败（docs/03 §7.8）。"""
    body = with_junk({'carNo': 'parityB%s%s' % (SUFFIX, tag), 'plateColor': '1', 'status': '0',
                      'remark': 'parityW%s' % SUFFIX}, extra)
    return {'add': call('POST', base, token, '/manager/carsuspiciousback', body)}


def smoke_gen_import(base, token, tag, extra=None):
    """POST /tool/gen/importTable：只把库里已有的表登记进 gen_table，删起来干净。"""
    out = {'add': call('POST', base, token, '/tool/gen/importTable?tables=car_confim_free')}
    rows = rows_of(base, token, '/tool/gen/list', '?tableName=car_confim_free')
    mine = [row for row in rows if (row.get('tableId') or 0) == max(
        (r.get('tableId') or 0) for r in rows) and row.get('tableName') == 'car_confim_free']
    out['found'] = len(mine)
    for row in mine:
        out['delete'] = call('DELETE', base, token, '/tool/gen/%s' % row['tableId'])
    return out


CASES = [
    ('POST /monitor/job', smoke_job),
    ('POST /system/user', smoke_user),
    ('POST /system/user（部门不存在）', smoke_user_missing_dept),
    ('POST /system/role', smoke_role),
    ('POST /system/dept', smoke_dept),
    ('POST /system/post', smoke_post),
    ('POST /system/config', smoke_config),
    ('POST /system/dict/type', smoke_dict_type),
    ('POST /system/dict/data', smoke_dict_data),
    ('POST /system/notice', smoke_notice),
    ('POST /system/menu', smoke_menu),
    ('POST /manager/carinfo', smoke_carinfo),
    ('POST /manager/carsuspiciousback（无 id）', smoke_suspicious_back),
    ('POST /tool/gen/importTable', smoke_gen_import),
]


#: Java 自身整体不可用的用例（docs/03 §7.6：insertUser 在 MyBatis 设置参数阶段就抛
#: `IndexOutOfBoundsException: No group 2`），Rust 按正确行为实现，不算不一致。
KNOWN = {'POST /system/user'}


def comparable(item):
    """自增主键/探针名后缀两端必然不同，只比可比字段。"""
    return {key: value for key, value in item.items() if key != 'add'}


def error_core(text):
    """把数据库报错削到 MySQL 原文：Java 是 MyBatis 整段包装，Rust 是 SQLx 前缀。
    两端 HTTP 码/是否写行一致，只差模板文案（docs/03 §7.8），不该算不一致。"""
    match = re.search(r'### Cause: [^.]+(?:\.[^:.]+)+: (.*?)\n;', text, re.S)
    if match:
        return match.group(1).strip()
    match = re.search(r'error returned from database: \d+ \(\w+\): (.*)', text)
    if match:
        return match.group(1).strip()
    return text


def normalize_add(value):
    """把端别标记与时间戳后缀抹掉、SQL 报错削到原文再比 msg。"""
    return error_core(str(value).replace('-J', '').replace('-R', '').replace(SUFFIX, ''))


def main() -> int:
    tj, sj, _ = login(JAVA)
    tr, sr, _ = login(RUST)
    if not tj or not tr:
        print('登录失败', sj, sr)
        return 2
    bad = 0
    for label, fn in CASES:
        # 每种请求体用自己的探针名：RuoYi 的判重（角色名、车牌、字典键…）不看 del_flag，
        # 上一遍留下的软删行会让这一遍直接报「已存在」，那是探针的问题不是接口的。
        for variant, extra, marker in (('干净体', None, ''), ('掺非列字段', JUNK, 'n')):
            a = fn(JAVA, tj, 'J' + marker, extra)
            b = fn(RUST, tr, 'R' + marker, extra)
            same = (comparable(a) == comparable(b)
                    and normalize_add(a.get('add')) == normalize_add(b.get('add')))
            if not same and label in KNOWN and 'No group 2' in str(a.get('add')):
                print('known %-40s %s  Java 整体不可用（§7.6），Rust 正常：%s'
                      % (label, variant, str(b.get('add'))[:40]))
                continue
            bad += 0 if same else 1
            print(('==' if same else '!=') + '  %-40s %s' % (label, variant))
            if not same:
                print('    java: ' + json.dumps(a, ensure_ascii=False)[:400])
                print('    rust: ' + json.dumps(b, ensure_ascii=False)[:400])
    # 掺字段那遍还要与干净那遍同构（每端各再跑一次），否则「忽略」无从谈起。
    for label, fn in CASES:
        for base, token, tag, side in ((JAVA, tj, 'Jc', 'java'), (RUST, tr, 'Rq', 'rust')):
            clean = comparable(fn(base, token, tag))
            junk = comparable(fn(base, token, tag + 'n', JUNK))
            same = clean == junk
            bad += 0 if same else 1
            print(('==' if same else '!=') + '  %-40s 非列字段被忽略（%s）' % (label, side))
            if not same:
                print('    clean: ' + json.dumps(clean, ensure_ascii=False)[:300])
                print('    junk : ' + json.dumps(junk, ensure_ascii=False)[:300])
    print('\n不一致 %d' % bad)
    print('收尾清理（两端共用一个库和一套 Redis）：')
    print('  1) 按 parity / parityW%s 前缀硬删各表软删行（sys_role/sys_config/car_info…）' % SUFFIX)
    print('  2) redis-cli --scan --pattern "*parity*" | xargs redis-cli del   # sys_config:{key} 会被新增写进缓存')
    print('  3) redis-cli del car_list car_list_jc                            # 车辆缓存整键重写，让它按干净的库重建')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
