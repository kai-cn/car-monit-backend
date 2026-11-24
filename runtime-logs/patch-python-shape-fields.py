#!/usr/bin/env python3
"""
@description 按 Java 基准为 backend Python 的 ODS 列表和详情补齐指定可空字段，撤回全局字段污染。
@author Tencent Hunyuan Hy
@date 2026-11-24 23:40:00
@usage python3 runtime-logs/patch-python-shape-fields.py
@dependencies backend master Python 源码。
"""
from pathlib import Path

B = Path('/home/dev/IdeaProjects/car-monit-backend/car-monit-py')


def replace(path: Path, old: str, new: str, label: str) -> None:
    """精确替换源码片段；未命中时输出诊断。"""
    t = path.read_text(encoding='utf-8')
    if old not in t:
        print('NOT_FOUND', label, path)
        return
    path.write_text(t.replace(old, new, 1), encoding='utf-8')
    print('OK', label, path)


# 只保留所有 ODS 行共有的分页字段；其余字段由各端点显式补齐。
replace(B / 'app/base/service/forest/forest_client.py',
        '''        for row in rows:
            row.setdefault("pageNum", None)
            row.setdefault("pageSize", None)
            # Java ODS 实体声明了一批可空字段，即使为 null 也会出现在 JSON 中。
            for field in (
                "cid", "enaxlecount", "entryoperatorid", "enweight", "obuid", "obusign",
                "plateColorMark", "plateColorName", "directionStr", "chargeStatus", "entimeStr",
            ):
                row.setdefault(field, None)''',
        '''        for row in rows:
            row.setdefault("pageNum", None)
            row.setdefault("pageSize", None)''',
        'remove-global-derived')


def add_null_fields(text: str, anchor: str, fields: tuple, label: str) -> str:
    """在指定 return 前补字段；锚点必须唯一。"""
    if anchor not in text:
        print('ANCHOR_NOT_FOUND', label)
        return text
    lines = '\n'.join(f'            row.setdefault("{f}", None)' for f in fields)
    replacement = f'        # Java 基准声明的可空字段，即使值为 null 也必须出现在 JSON 中。\n{lines}\n' + anchor
    return text.replace(anchor, replacement, 1)


p = B / 'app/api/base/ods_lwzxsfsj_fee_station_exit01_controller.py'
t = p.read_text(encoding='utf-8')
t = add_null_fields(t, '    return to_table_data_info(json_object)',
                    ('cid', 'enaxlecount', 'entryoperatorid', 'enweight', 'obuid', 'obusign',
                     'paycardid', 'provfee', 'specialtype'), 'stationexit')
p.write_text(t, encoding='utf-8')

# 下游代理列表：按 Java 实体补 plateColor 派生字段。
for rel, label in [
    ('app/base/service/forest/http_ods_lwzxsfsj_fee_gantry_fusion01_service.py', 'feeGantry'),
    ('app/base/service/forest/http_ods_lwzxsfsj_fee_records01_service.py', 'feeRecords'),
    ('app/base/service/forest/http_ods_rt_szdn_snapshot_flow_addcode_service.py', 'snapshotFlow'),
    ('app/base/service/forest/http_sys_util_api_service.py', 'sysUtil'),
]:
    p = B / rel
    t = p.read_text(encoding='utf-8')
    old = '        return to_table_data_info(payload)'
    new = '''        info = to_table_data_info(payload)
        # Java 实体声明的派生字段即使为 null 也会序列化。
        for row in info.rows or []:
            if isinstance(row, dict):
                row.setdefault("plateColorMark", None)
                row.setdefault("plateColorName", None)
        return info'''
    t = t.replace(old, new)
    p.write_text(t, encoding='utf-8')
    print('OK plate-fields', label, p)

# 详情：按 Java 基准补可空字段。
p = B / 'app/api/base/ods_lwzxsfsj_fee_records01_controller.py'
t = p.read_text(encoding='utf-8')
old = '    return AjaxResult.success_data(_service().select_by_id(big_id))'
new = '''    row = _service().select_by_id(big_id)
    if isinstance(row, dict):
        for field in ("plateColorMark", "plateColorName", "chargeStatus", "entimeStr", "receivetimeStr", "sectionName"):
            row.setdefault(field, None)
    return AjaxResult.success_data(row)'''
replace(p, old, new, 'feerecords-detail-fields')

p = B / 'app/api/base/ods_rt_szdn_snapshot_flow_addcode_controller.py'
t = p.read_text(encoding='utf-8')
old = '    return AjaxResult.success_data(_service().select_by_id(big_id))'
new = '''    row = _service().select_by_id(big_id)
    if isinstance(row, dict):
        for field in ("plateColorMark", "plateColorName", "directionStr"):
            row.setdefault(field, None)
    return AjaxResult.success_data(row)'''
replace(p, old, new, 'snapshot-detail-fields')

p = B / 'app/api/manager/car_warning_info_controller.py'
t = p.read_text(encoding='utf-8')
for old in ['    return AjaxResult.success_data(_service().select_by_id(id))',
            '    return AjaxResult.success_data(_service().get_by_id(id))']:
    if old in t:
        new = '''    row = _service().select_by_id(id) if hasattr(_service(), "select_by_id") else _service().get_by_id(id)
    if isinstance(row, dict):
        row.setdefault("plateColorMark", None)
        row.setdefault("plateColorName", None)
    return AjaxResult.success_data(row)'''
        t = t.replace(old, new, 1)
        print('OK carwarning-detail-fields', p)
        break
p.write_text(t, encoding='utf-8')
