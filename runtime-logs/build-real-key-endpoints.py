#!/usr/bin/env python3
"""
@description 从本地 MySQL/PostgreSQL 取真实主键，生成 backend/api 读取类端点的对比基准。
@author Tencent Hunyuan Hy
@date 2026-11-24 11:45:00
@usage python3 runtime-logs/build-real-key-endpoints.py
@dependencies Docker 新别名 mysql8.0/pg16，兼容旧别名；输出 runtime-logs/real-key-endpoints。
"""
import json
import subprocess
from pathlib import Path

OUT = Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs/real-key-endpoints')
OUT.mkdir(parents=True, exist_ok=True)

# endpoint -> (db, table, key column)
BACKEND = {
    '/manager/carsuspiciousback/1': ('mysql', 'car_suspicious_back', 'id'),
    '/base/configServiceArea/1': ('mysql', 'base_config_service_area', 'fwqbm'),
    '/base/config/1': ('pg', 'sys_config', 'config_id'),
    '/base/fwqjcxx/1': ('pg', 'dwd_lczt_fwqjcxx', 'agent_pk'),
    '/base/sfsjcxx/1': ('pg', 'dwd_lczt_sfsjcxx', 'agent_pk'),
    '/base/sfzjcxx/1': ('pg', 'dwd_lczt_sfzjcxx', 'agent_pk'),
    '/base/geometry/1': ('mysql', 'geometry', 'id'),
    '/manager/fwqclls/1': ('pg', 'ods_cxzt_fwqclls', 'big_id'),
    '/base/feeGantry/1': ('pg', 'ods_lwzxsfsj_fee_gantry_fusion_01', 'big_id'),
    '/base/feerecords/1': ('pg', 'ods_lwzxsfsj_fee_records_01', 'big_id'),
    '/base/feeStationEnter/1': ('pg', 'ods_lwzxsfsj_fee_station_enter_01', 'big_id'),
    '/base/feestationexit/1': ('pg', 'ods_lwzxsfsj_fee_station_exit_01', 'big_id'),
    '/base/snapshotflow/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/provcapture/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/stationcapture/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/gantry/1': ('pg', 'ods_szdn_gantry', 'id'),
    '/base/gantryIp/1': ('pg', 'ods_szdn_gantry_ip', 'id'),
    '/base/vehicleweight/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/section/1': ('pg', 'ods_szdn_section', 'id'),
    '/base/toll/1': ('pg', 'ods_szdn_toll', 'id'),
    '/base/tollStationIp/1': ('pg', 'ods_szdn_toll_station_ip', 'id'),
    '/base/org/1': ('pg', 'ods_yhgl_v_base_org', 'big_id'),
    '/base/location/1': ('pg', 'zdata_location_dict', 'id'),
    '/base/fitting/1': ('pg', 'zdata_trail_fitting', 'cid'),
    '/base/trailtracks/1': ('pg', 'zdata_trail_tracks', 'uuid'),
    '/flow/applyinfo/1': ('mysql', 'flow_apply_info', 'ID'),
    '/flow/currentnode/1': ('mysql', 'flow_apply_info', 'ID'),
    '/flow/flowlist/1': ('mysql', 'flow_apply_info', 'ID'),
    '/flow/messagedispose/1': ('mysql', 'flow_apply_info', 'ID'),
    '/flow/messageinfo/1': ('mysql', 'flow_apply_info', 'ID'),
    '/flow/flowname/1': ('mysql', 'flow_name', 'ID'),
    '/flow/flowtemplate/1': ('mysql', 'flow_apply_info', 'ID'),
    '/manager/busstest/1': ('mysql', 'buss_test', 'id'),
    '/manager/aduitfree/1': ('mysql', 'car_aduit_free', 'id'),
    '/manager/confimfree/1': ('mysql', 'car_confim_free', 'id'),
    '/manager/confimfree/except/1': ('mysql', 'car_except_record', 'id'),
    '/manager/exceptrecord/1': ('mysql', 'car_except_record', 'id'),
    '/manager/feerecord/1': ('mysql', 'car_info', 'id'),
    '/manager/carinfo/1': ('mysql', 'car_info', 'id'),
    '/manager/querylog/1': ('mysql', 'car_query_log', 'id'),
    '/manager/routedetail/1': ('mysql', 'car_info', 'id'),
    '/manager/routeinfo/1': ('mysql', 'car_info', 'id'),
    '/manager/splitrecord/1': ('mysql', 'car_split_record', 'id'),
    '/manager/suspiciouscheck/1': ('mysql', 'car_suspicious_check', 'id'),
    '/manager/suspicious/1': ('mysql', 'car_suspicious', 'id'),
    '/manager/cartrackinfo/1': ('mysql', 'car_track_info', 'id'),
    '/manager/carwarning/1': ('mysql', 'car_warning_info', 'id'),
    '/manager/warningrule/1': ('mysql', 'car_warning_rule', 'id'),
    '/manager/whiteinfo/1': ('mysql', 'car_white_info', 'id'),
    '/manager/gantrycar/1': ('mysql', 'gantry_car', 'id'),
    '/manager/gantrytrade/1': ('mysql', 'gantry_trade_info', 'id'),
    '/system/config/1': ('mysql', 'sys_config', 'config_id'),
    '/system/dept/1': ('mysql', 'sys_dept', 'dept_id'),
    '/system/dict/data/1': ('mysql', 'sys_dict_data', 'dict_code'),
    '/system/dict/type/1': ('mysql', 'sys_dict_type', 'dict_id'),
    '/system/file/getInfoById/1': ('mysql', 'sys_file', 'id'),
    '/system/file/1': ('mysql', 'sys_file', 'id'),
    '/system/indexmenu/1': ('mysql', 'sys_index_menu', 'ID'),
    '/system/menu/1': ('mysql', 'sys_menu', 'menu_id'),
    '/system/notice/1': ('mysql', 'sys_notice', 'notice_id'),
    '/system/post/1': ('mysql', 'sys_post', 'post_id'),
    '/system/role/1': ('mysql', 'sys_role', 'role_id'),
    '/system/upgradeInfo/1': ('mysql', 'sys_notice', 'notice_id'),
    '/system/user/getroleUser/1': ('mysql', 'sys_user', 'user_id'),
    '/test/user/1': ('mysql', 'sys_user', 'user_id'),
    '/tool/gen/1': ('mysql', 'gen_table', 'table_id'),
    '/tool/gen/column/1': ('mysql', 'gen_table_column', 'column_id'),
    '/tool/gen/preview/1': ('mysql', 'gen_table', 'table_id'),
    '/tool/gen/download/1': ('mysql', 'gen_table', 'table_id'),
    '/tool/gen/genCode/1': ('mysql', 'gen_table', 'table_name'),
    '/tool/gen/synchDb/1': ('mysql', 'gen_table', 'table_name'),
    '/monitor/job/1': ('mysql', 'sys_job', 'job_id'),
    '/monitor/jobLog/1': ('mysql', 'sys_job_log', 'job_log_id'),
}
API = {
    '/base/fwqjcxx/1': ('pg', 'dwd_lczt_fwqjcxx', 'agent_pk'),
    '/base/sfsjcxx/1': ('pg', 'dwd_lczt_sfsjcxx', 'agent_pk'),
    '/base/sfzjcxx/1': ('pg', 'dwd_lczt_sfzjcxx', 'agent_pk'),
    '/manager/fwqclls/1': ('pg', 'ods_cxzt_fwqclls', 'big_id'),
    '/base/feeGantry/1': ('pg', 'ods_lwzxsfsj_fee_gantry_fusion_01', 'big_id'),
    '/base/feerecords/1': ('pg', 'ods_lwzxsfsj_fee_records_01', 'big_id'),
    '/base/feeStationEnter/1': ('pg', 'ods_lwzxsfsj_fee_station_enter_01', 'big_id'),
    '/base/feestationexit/1': ('pg', 'ods_lwzxsfsj_fee_station_exit_01', 'big_id'),
    '/base/snapshotflow/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/provcapture/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/stationcapture/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/gantry/1': ('pg', 'ods_szdn_gantry', 'id'),
    '/base/gantryIp/1': ('pg', 'ods_szdn_gantry_ip', 'id'),
    '/base/vehicleweight/1': ('pg', 'ods_rt_szdn_snapshot_flow_addcode', 'big_id'),
    '/base/section/1': ('pg', 'ods_szdn_section', 'id'),
    '/base/toll/1': ('pg', 'ods_szdn_toll', 'id'),
    '/base/tollStationIp/1': ('pg', 'ods_szdn_toll_station_ip', 'id'),
    '/base/org/1': ('pg', 'ods_yhgl_v_base_org', 'big_id'),
    '/base/trailtracks/1': ('pg', 'zdata_trail_tracks', 'uuid'),
}


def container(new_name: str, old_name: str) -> str:
    """优先使用新容器别名，缺失时回退旧别名。"""
    names = subprocess.run(['docker', 'ps', '-a', '--format', '{{.Names}}'],
                           text=True, capture_output=True).stdout.splitlines()
    return new_name if new_name in names else old_name


def query(db: str, table: str, col: str) -> str:
    """查询一个真实主键值；失败时输出空串。"""
    if db == 'mysql':
        name = container('mysql8.0', 'mysql_wsl')
        cmd = ['docker', 'exec', name, 'mysql', '-uroot', '-proot', '-N',
               '-e', f'select `{col}` from carmonitdb.`{table}` where `{col}` is not null limit 1']
    else:
        name = container('pg16', 'pg_wsl')
        cmd = ['docker', 'exec', name, 'psql', '-U', 'postgres', '-d', 'RuoYi', '-Atc',
               f'select "{col}" from jl_data01."{table}" where "{col}" is not null limit 1']
    r = subprocess.run(cmd, text=True, capture_output=True)
    return r.stdout.strip() if r.returncode == 0 else ''


def build(name: str, mapping: dict) -> None:
    """按映射替换端点中的占位主键，并保存映射证据。"""
    src = Path(f'/home/dev/IdeaProjects/car-monit-{name}/scripts/v3/ops/parity/endpoints/{name}-full.txt')
    if name == 'api':
        src = Path('/home/dev/IdeaProjects/car-monit-api/scripts/v3/ops/parity/endpoints/api-full.txt')
    rows = []
    used = {}
    query_overrides = {
        '/base/geometry/getHenDa': '/base/geometry/getHenDa?lxbh=G35&lxfx=1&zhStr=940',
    }
    for line in src.read_text(encoding='utf-8').splitlines():
        ep = line.strip()
        if not ep:
            continue
        key = query_overrides.get(ep, ep)
        info = mapping.get(ep)
        if info:
            value = query(*info)
            if value:
                used[ep] = value
                key = (ep[:-1] if '?' not in ep else ep) + (value if '?' not in ep else '')
                rows.append({'endpoint': ep, 'key_endpoint': key, 'db': info[0], 'table': info[1], 'column': info[2], 'value': value})
            else:
                rows.append({'endpoint': ep, 'key_endpoint': ep, 'db': info[0], 'table': info[1], 'column': info[2], 'value': None})
        out.write_text('\n'.join(out_lines) + '\n', encoding='utf-8') if False else None
        globals().setdefault('_OUT', {}).setdefault(name, []).append(key)
    out = OUT / f'{name}-read-realkey.txt'
    out.write_text('\n'.join(globals()['_OUT'][name]) + '\n', encoding='utf-8')
    (OUT / f'{name}-real-key-map.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
    print('WROTE', out, len(globals()['_OUT'][name]))


build('backend', BACKEND)
build('api', API)
