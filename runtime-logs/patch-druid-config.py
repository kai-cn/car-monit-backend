#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\DruidConfig.java')
t = p.read_text(encoding='utf-8')
old = 'DruidDataSource dataSource = DruidDataSourceBuilder.create().build();'
new = 'DruidDataSource dataSource = new DruidDataSource();  // native: avoid DruidDataSourceWrapper (basicProperties null)'
print('replacements', t.count(old))
t = t.replace(old, new)
p.write_text(t, encoding='utf-8')
