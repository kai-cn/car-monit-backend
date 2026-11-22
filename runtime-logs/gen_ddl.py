#!/usr/bin/env python3

"""
@description 历史脚本 gen_ddl.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python gen_ddl.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Generate CREATE TABLE DDL + sample INSERTs for jl_data01 from openGauss via psql."""

import subprocess, os, re



WSL = ['wsl.exe', '-e', 'bash', '-lc']

GS_PASS_CMD = 'docker exec opengauss env 2>/dev/null | sed -n "s/^[^=]*GS_PASSWORD=//p" | tr -d "\\r" | head -1'





def psql(sql, sep='\t'):

    cmd = (f'export PGPASSWORD=$({GS_PASS_CMD}); '

           f'psql -h 127.0.0.1 -p 5432 -U gaussdb -d RuoYi -AtF "{sep}" -c "{sql}"')

    r = subprocess.run(WSL + [cmd], capture_output=True, text=True, encoding='utf-8', errors='replace')

    return r.stdout.strip(), r.stderr.strip()





# 1) columns per table

sql_cols = ("select table_name, column_name, data_type, character_maximum_length, "

            "numeric_precision, numeric_scale, is_nullable, column_default "

            "from information_schema.columns where table_schema='jl_data01' "

            "order by table_name, ordinal_position")

cols, err = psql(sql_cols)

if err:

    print('ERR cols:', err[:300])

rows = [l.split('\t') for l in cols.splitlines() if l.strip()]

tables = {}

for r in rows:

    if len(r) < 8:

        r += [''] * (8 - len(r))

    tn, cn, dt, clen, nprec, nscale, nullable, cdef = r[:8]

    tables.setdefault(tn, []).append(dict(name=cn, type=dt, len=clen, prec=nprec, scale=nscale, nullable=nullable, default=cdef))



print('jl_data01 tables:', len(tables))



# 2) primary keys

sql_pk = ("select tc.table_name, kcu.column_name from information_schema.table_constraints tc "

          "join information_schema.key_column_usage kcu on tc.constraint_name=kcu.constraint_name "

          "and tc.table_schema=kcu.table_schema "

          "where tc.constraint_type='PRIMARY KEY' and tc.table_schema='jl_data01' "

          "order by tc.table_name, kcu.ordinal_position")

pks, err2 = psql(sql_pk)

pk_map = {}

for l in pks.splitlines():

    if '\t' in l:

        t, c = l.split('\t')[:2]

        pk_map.setdefault(t, []).append(c)



SKIP_PREFIX = ('gen_table', 'qrtz_', 'v3_migration')



def sql_type(c):

    dt = c['type'].lower()

    if dt in ('character varying', 'varchar'):

        return f"varchar({c['len']})" if c['len'] else 'varchar'

    if dt == 'character':

        return f"char({c['len']})" if c['len'] else 'char'

    if dt in ('numeric', 'decimal'):

        if c['prec']:

            return f"numeric({c['prec']},{c['scale'] or 0})"

        return 'numeric'

    m = {

        # openGauss/MySQL-ish types -> vanilla postgres equivalents

        'integer': 'int4', 'bigint': 'int8', 'smallint': 'int2', 'int4': 'int4', 'int8': 'int8',

        'tinyint': 'int2', 'mediumint': 'int4', 'integer unsigned': 'int8', 'bigint unsigned': 'numeric(20,0)',

        'double precision': 'float8', 'real': 'float4', 'boolean': 'bool', 'text': 'text',

        'timestamp without time zone': 'timestamp', 'timestamp with time zone': 'timestamptz',

        'date': 'date', 'time without time zone': 'time', 'bytea': 'bytea',

        'json': 'json', 'jsonb': 'jsonb', 'character varying': 'varchar',

        'bit': 'bit varying', 'tsvector': 'text', 'tsquery': 'text',

        'money': 'numeric(19,4)', 'uuid': 'uuid', 'xml': 'text', 'interval': 'interval',

        'point': 'point', 'line': 'line', 'lseg': 'lseg', 'box': 'box', 'path': 'path',

        'polygon': 'polygon', 'circle': 'circle', 'cidr': 'cidr', 'inet': 'inet', 'macaddr': 'macaddr',

        'user-defined': 'text', 'array': 'text', 'ARRAY': 'text',

    }

    return m.get(dt, dt if dt in ('text', 'varchar', 'char', 'bool', 'int4', 'int8', 'int2',

                                  'float4', 'float8', 'numeric', 'date', 'timestamp', 'timestamptz',

                                  'time', 'bytea', 'json', 'jsonb', 'uuid', 'interval') else 'text')



lines = ['-- Auto-generated schema for jl_data01 (from local openGauss RuoYi, schema-only)',

         'CREATE SCHEMA IF NOT EXISTS jl_data01;',

         'SET search_path TO jl_data01, public;', '']

created = []

for tn in sorted(tables):

    if tn.startswith(SKIP_PREFIX):

        continue

    created.append(tn)

    lines.append(f'DROP TABLE IF EXISTS jl_data01.{tn} CASCADE;')

    lines.append(f'CREATE TABLE jl_data01.{tn} (')

    defs = []

    for c in tables[tn]:

        d = f"  {c['name']} {sql_type(c)}"

        if c['nullable'] == 'NO':

            d += ' NOT NULL'

        defs.append(d)

    pk = pk_map.get(tn)

    if pk:

        defs.append('  PRIMARY KEY (' + ', '.join(pk) + ')')

    lines.append(',\n'.join(defs))

    lines.append(');')

    lines.append('')



out = r'D:\work\runtime-logs\ddl\schema_jl_data01.sql'

os.makedirs(os.path.dirname(out), exist_ok=True)

open(out, 'w', encoding='utf-8').write('\n'.join(lines))

print('created tables:', len(created), '->', out)

print('size:', os.path.getsize(out), 'bytes')

