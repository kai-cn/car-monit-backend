#!/usr/bin/env python3

"""
@description 历史脚本 gen_seed.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python gen_seed.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Export limited seed rows (as INSERTs) for key jl_data01 tables from local openGauss."""

import subprocess, os



WSL = ['wsl.exe', '-e', 'bash', '-lc']

PASS = 'docker exec opengauss env 2>/dev/null | sed -n "s/^[^=]*GS_PASSWORD=//p" | tr -d "\\r" | head -1'



TABLES = [

    'ods_lwzxsfsj_fee_records_01', 'ods_szdn_gantry', 'ods_szdn_toll', 'ods_szdn_section',

    'ods_szdn_gantry_ip', 'ods_szdn_toll_station_ip', 'ods_yhgl_v_base_org',

    'ods_rt_szdn_snapshot_flow_addcode', 'zdata_trail_fitting', 'ods_lwzxsfsj_fee_gantry_fusion_01',

    'ods_lwzxsfsj_fee_station_enter_01', 'ods_lwzxsfsj_fee_station_exit_01',

    'ods_szdn_province_border_vehicle_weight_newstructure', 'dwd_lczt_fwqjcxx',

    'dwd_lczt_sfsjcxx', 'dwd_lczt_sfzjcxx', 'ods_cxzt_fwqclls', 'ods_szdn_service',

    'zdata_trail_tracks', 'zdata_trail_unfitting', 'car_info', 'zdata_location_dict',

    'sys_dict_data', 'sys_dict_type', 'sys_config', 'sys_menu', 'sys_dept',

]

LIMIT = 150





def psql(sql):

    cmd = (f'export PGPASSWORD=$({PASS}); '

           f'psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -At -c "{sql}"')

    r = subprocess.run(WSL + [cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')

    return r.stdout, r.stderr





out_lines = ['-- Seed data (limited rows) exported from local openGauss RuoYi',

             'SET search_path TO jl_data01, public;',

             'SET client_encoding TO \'UTF8\';', '']

total = 0

for t in TABLES:

    # check exists

    o, e = psql(f"select count(*) from information_schema.tables where table_schema='jl_data01' and table_name='{t}'")

    if o.strip() != '1':

        print(f'  skip {t} (no table)')

        continue

    # columns

    o, e = psql(f"select column_name from information_schema.columns where table_schema='jl_data01' and table_name='{t}' order by ordinal_position")

    cols = [c.strip() for c in o.splitlines() if c.strip()]

    if not cols:

        print(f'  skip {t} (no cols)')

        continue

    collist = ', '.join('"' + c + '"' for c in cols)

    # export as pipe-delimited csv via COPY ... TO STDOUT

    copy_sql = f"COPY (SELECT {collist} FROM jl_data01.{t} LIMIT {LIMIT}) TO STDOUT WITH (FORMAT csv, HEADER false)"

    cmd = (f'export PGPASSWORD=$({PASS}); '

           f'psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -c "COPY (SELECT {collist} FROM jl_data01.{t} LIMIT {LIMIT}) TO STDOUT WITH (FORMAT csv)"')

    r = subprocess.run(WSL + [cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')

    data = r.stdout

    if not data.strip():

        print(f'  {t}: 0 rows')

        continue

    nrows = data.rstrip('\n').count('\n') + 1

    total += nrows

    out_lines.append(f'-- {t}: {nrows} rows')

    out_lines.append(f'COPY jl_data01.{t} ({collist}) FROM stdin WITH (FORMAT csv);')

    out_lines.append(data.rstrip('\n'))

    out_lines.append('\\.')

    out_lines.append('')

    print(f'  {t}: {nrows} rows')



out = r'D:\work\runtime-logs\ddl\seed_jl_data01.sql'

open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(out_lines))

print(f'TOTAL rows={total} -> {out} size={os.path.getsize(out)}')

