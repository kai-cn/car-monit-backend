#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
p = Path('/home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/pom.xml')
t = p.read_text(encoding='utf-8')
needle = '                <artifactId>native-maven-plugin</artifactId>\n                <version>1.1.14</version>\n                <configuration>\n'
block_end = t.find('</configuration>', t.find(needle))
block = t[t.find(needle):block_end]
if '<mainClass>' not in block:
    t = t.replace(needle, needle + '                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>\n', 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED')
else:
    print('ALREADY')
PY
