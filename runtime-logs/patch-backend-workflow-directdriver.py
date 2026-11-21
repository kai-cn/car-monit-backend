#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\remote-parity-bk25.yml')
t = p.read_text(encoding='utf-8')
t = t.replace('jdbc:p6spy:mysql://127.0.0.1:3306/carmonitdb', 'jdbc:mysql://127.0.0.1:3306/carmonitdb')
needle = '          SPRING__DATASOURCE__DRUID__MASTER__PASSWORD: root\n'
add = needle + '          SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME: com.mysql.cj.jdbc.Driver\n'
t = t.replace(needle, add)
p.write_text(t, encoding='utf-8')
print('patched workflow', t.count('com.mysql.cj.jdbc.Driver'))
