#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Add a missing option, resource, or reflection/config entry required by a later build step.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
python3 - <<'PY'
from pathlib import Path
for root in (Path('/home/dev/IdeaProjects'), Path('/mnt/d/work/IdeaProjects')):
    for repo in ('car-monit-backend-jdk25','car-monit-backend-jdk21','car-monit-backend-jdk17'):
        p=root/repo/'ruoyi-admin/pom.xml'
        t=p.read_text(encoding='utf-8')
        if '<goal>process-aot</goal>' in t:
            print('SKIP',p); continue
        needle='''                <executions>
                    <execution>
                        <goals>
                            <goal>repackage</goal>
                        </goals>
                    </execution>
                </executions>'''
        repl='''                <executions>
                    <execution>
                        <goals>
                            <goal>repackage</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>process-aot</id>
                        <goals>
                            <goal>process-aot</goal>
                        </goals>
                    </execution>
                </executions>'''
        if needle in t:
            p.write_text(t.replace(needle,repl,1),encoding='utf-8')
            print('PATCHED',p)
        else:
            print('NOT_FOUND',p)
PY
