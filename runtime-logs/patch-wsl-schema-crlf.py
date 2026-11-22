#!/usr/bin/env python3
"""Insert sys_upgrade_info fixture into CRLF schema file.

@description 在 backend master schema fixture 中加入 sys_upgrade_info 表，修复 /system/upgradeInfo/* 非 200。
@author Tencent Hunyuan Hy
@date 2026-11-23 01:00:50
@usage python runtime-logs/patch-wsl-schema-crlf.py
@dependencies WSL backend master clone。
"""
from pathlib import Path

p = Path(r'\\wsl$\openEuler-24.03-LTS-SP4\home\dev\IdeaProjects\car-monit-backend\scripts\v3\ops\parity\sql\schema_carmonitdb.sql')
t = p.read_text(encoding='utf-8', errors='replace')
if 'CREATE TABLE IF NOT EXISTS `sys_upgrade_info`' in t:
    print('EXISTS')
    raise SystemExit(0)
lines = t.splitlines(keepends=True)
idx = 0
for i, line in enumerate(lines[:20]):
    if 'SET @OLD_CHARACTER_SET_CLIENT' in line:
        idx = i + 1
        break
block = '\r\n'.join([
    '',
    '-- CI/test fixture: Java /system/upgradeInfo endpoints expect this table.',
    'CREATE TABLE IF NOT EXISTS `sys_upgrade_info` (',
    '  `id` bigint NOT NULL AUTO_INCREMENT,',
    '  `version` varchar(64) DEFAULT NULL,',
    '  `content` text,',
    '  `create_time` datetime DEFAULT NULL,',
    '  PRIMARY KEY (`id`)',
    ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;',
    '',
]) + '\r\n'
p.write_text(''.join(lines[:idx]) + block + ''.join(lines[idx:]), encoding='utf-8')
print('INSERTED')
