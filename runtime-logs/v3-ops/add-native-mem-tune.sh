#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
p = Path('/home/dev/IdeaProjects/car-monit-api-jdk25/pro-business-api/pom.xml')
t = p.read_text(encoding='utf-8')
needle = '                        <buildArg>--no-fallback</buildArg>'
add = (needle + '\n'
       '                        <buildArg>-J-XX:MaxRAMPercentage=85</buildArg>\n'
       '                        <buildArg>-J-XX:ActiveProcessorCount=4</buildArg>')
if 'MaxRAMPercentage' not in t:
    t = t.replace(needle, add, 1)
    p.write_text(t, encoding='utf-8')
print('PATCHED', p)
PY
