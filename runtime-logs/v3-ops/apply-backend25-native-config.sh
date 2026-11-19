#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a generated configuration to local or remote branches.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
L = Path('/home/dev/IdeaProjects')
# root pom: proc=full for javac25
p = L/'car-monit-backend-jdk25/pom.xml'
t = p.read_text(encoding='utf-8')
needle = '                    <parameters>true</parameters>'
if '<proc>full</proc>' not in t and needle in t:
    t = t.replace(needle, needle + '\n                    <proc>full</proc>', 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED root', p)

p = L/'car-monit-backend-jdk25/ruoyi-admin/pom.xml'
t = p.read_text(encoding='utf-8')
needle = '                <artifactId>native-maven-plugin</artifactId>\n                <configuration>'
if '<mainClass>com.ruoyi.RuoYiApplication</mainClass>' not in t:
    t = t.replace(needle, needle + '\n                    <mainClass>com.ruoyi.RuoYiApplication</mainClass>', 1)
needle2 = '                        <buildArg>--no-fallback</buildArg>'
if 'SLF4JServiceProvider' not in t:
    t = t.replace(needle2, needle2 + '\n                        <buildArg>-H:IncludeResources=META-INF/services/org.slf4j.spi.SLF4JServiceProvider</buildArg>', 1)
if 'initialize-at-run-time=org.slf4j' not in t:
    t = t.replace(needle2, needle2 + '\n                        <buildArg>--initialize-at-run-time=org.slf4j,org.apache.commons.logging,org.apache.logging.slf4j,org.apache.logging.log4j</buildArg>', 1)
if '<version>1.1.14</version>' not in t:
    t = t.replace('                <artifactId>native-maven-plugin</artifactId>\n',
                  '                <artifactId>native-maven-plugin</artifactId>\n                <version>1.1.14</version>\n', 1)
p.write_text(t, encoding='utf-8')
print('PATCHED module', p)
PY
mkdir -p /home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints
cp -f /home/dev/IdeaProjects/car-monit-backend-jdk21/ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json \
      /home/dev/IdeaProjects/car-monit-backend-jdk25/ruoyi-admin/src/main/resources/META-INF/native-image/com.ruoyi/v3-native-hints/reflect-config.json
echo BACKEND25_CONFIG_OK
