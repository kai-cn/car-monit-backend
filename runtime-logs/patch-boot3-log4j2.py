#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\api-boot3-module-pom.xml')
t = p.read_text(encoding='utf-8')
needle = '                        <buildArg>--initialize-at-build-time=ch.qos.logback</buildArg>'
add = needle + '\n                        <buildArg>--initialize-at-build-time=org.springframework.boot.logging.log4j2.SpringBootPropertySource</buildArg>'
if 'SpringBootPropertySource' not in t:
    t = t.replace(needle, add, 1)
p.write_text(t, encoding='utf-8')
print('patched', 'SpringBootPropertySource' in t)
