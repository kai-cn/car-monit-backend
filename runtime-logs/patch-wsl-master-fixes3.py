#!/usr/bin/env python3
"""Finish remaining master fixes in WSL clones.

@description 补全 api Python 数据库口令测试默认值与 backend schema fixture 插入位置。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python runtime-logs/patch-wsl-master-fixes3.py
@dependencies WSL master clones。
"""
from pathlib import Path

WSL = Path(r'\\wsl$\openEuler-24.03-LTS-SP4\home\dev\IdeaProjects')
changes = []

# api Python: check actual key and add controlled CI default only when env is absent.
py_cfg = WSL / 'car-monit-api/car-monit-api-python/pro-business-api/src/main/resources/application.yml'
t = py_cfg.read_text(encoding='utf-8', errors='replace')
old = 'password: ${SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD:}'
new = 'password: ${SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD:postgres}'
if old in t:
    py_cfg.write_text(t.replace(old, new), encoding='utf-8')
    changes.append(('OK', str(py_cfg)))
elif 'password: ${POSTGRES_PASSWORD:}' in t:
    py_cfg.write_text(t.replace('password: ${POSTGRES_PASSWORD:}', 'password: ${POSTGRES_PASSWORD:postgres}'), encoding='utf-8')
    changes.append(('OK', str(py_cfg)))
else:
    changes.append(('CHECK', str(py_cfg)))
    for i, line in enumerate(t.splitlines(), 1):
        if 'password' in line.lower():
            print('PASSWORD_LINE', i, line.strip())

# backend schema: prepend fixture after first SET NAMES line.
schema = WSL / 'car-monit-backend/scripts/v3/ops/parity/sql/schema_carmonitdb.sql'
t = schema.read_text(encoding='utf-8', errors='replace')
if 'CREATE TABLE IF NOT EXISTS `sys_upgrade_info`' not in t:
    marker = 'SET NAMES utf8mb4;\n'
    block = '''
-- CI/test fixture: Java /system/upgradeInfo endpoints expect this table.
CREATE TABLE IF NOT EXISTS `sys_upgrade_info` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `version` varchar(64) DEFAULT NULL,
  `content` text,
  `create_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

'''
    if marker in t:
        idx = t.find(marker) + len(marker)
        schema.write_text(t[:idx] + block + t[idx:], encoding='utf-8')
        changes.append(('OK', str(schema)))
    else:
        changes.append(('MARKER_NOT_FOUND', str(schema)))
else:
    changes.append(('EXISTS', str(schema)))

for status, path in changes:
    print(status, path)
