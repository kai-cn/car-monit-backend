#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
p = Path('/home/dev/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml')
t = p.read_text(encoding='utf-8')
t = t.replace('                        <buildArg>-J-Xmx8g</buildArg>\n', '')
p.write_text(t, encoding='utf-8')
print('REVERTED', p)
PY
