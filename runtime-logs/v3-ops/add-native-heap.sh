#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
p = Path('/home/dev/IdeaProjects/car-monit-api-jdk21/pro-business-api/pom.xml')
t = p.read_text(encoding='utf-8')
needle = '                        <buildArg>--no-fallback</buildArg>'
if '-J-Xmx8g' in t:
    print('SKIP')
else:
    t = t.replace(needle, needle + '\n                        <buildArg>-J-Xmx8g</buildArg>', 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
PY
