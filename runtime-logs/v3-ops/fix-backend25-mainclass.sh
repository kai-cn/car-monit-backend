#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
p = Path('/home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/pom.xml')
t = p.read_text(encoding='utf-8')
if '<mainClass>com.ruoyi.RuoYiApplication</mainClass>' not in t:
    t = t.replace('                <configuration>\n                    <buildArgs>',
                  '                <configuration>\n                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>\n                    <buildArgs>', 1)
if 'SLF4JServiceProvider' not in t:
    t = t.replace('                    <buildArgs>\n',
                  '                    <buildArgs>\n                        <buildArg>-H:IncludeResources=META-INF/services/org.slf4j.spi.SLF4JServiceProvider</buildArg>\n', 1)
if 'initialize-at-run-time=org.slf4j' not in t:
    t = t.replace('                    <buildArgs>\n',
                  '                    <buildArgs>\n                        <buildArg>--initialize-at-run-time=org.slf4j,org.apache.commons.logging,org.apache.logging.slf4j,org.apache.logging.log4j</buildArg>\n', 1)
p.write_text(t, encoding='utf-8')
print('FIXED', p)
PY
