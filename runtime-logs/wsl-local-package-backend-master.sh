#!/usr/bin/env bash
# @description 历史脚本 wsl-local-package-backend-master.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22
# @usage bash wsl-local-package-backend-master.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: build and package backend master locally with JDK8.
# Idea: targeted fallback after the batch script skipped the BOM-prefixed first manifest row.
# Risk: writes only the clean temporary worktree and local package evidence files.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
OUT=$ROOT/local-package-evidence
LOG=$OUT/logs/backend__master.log
PATH_ROOT=/mnt/d/work/IdeaProjects/_local-package-20261122-130307/backend__master
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
echo "START backend master $(date -Is)" > "$LOG"
cd "$PATH_ROOT" || exit 90
JAVA_HOME="$JAVA_HOME" PATH="$JAVA_HOME/bin:$PATH" \
  mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl ruoyi-admin -am clean package >> "$LOG" 2>&1
rc=$?
JAR=$(find "$PATH_ROOT/ruoyi-admin/target" -maxdepth 1 -type f -name '*.jar' ! -name 'original-*' 2>/dev/null | head -1)
SIZE=0
[ -n "$JAR" ] && SIZE=$(stat -c %s "$JAR")
printf '%s|%s|%s|%s|%s|%s|%s|%s\n' backend 8 master 394ab03f "$rc" "$JAR" "$SIZE" "$LOG" > "$OUT/backend__master.result"
echo "DONE rc=$rc size=$SIZE $(date -Is)" >> "$LOG"
python3 - <<'PY'
import json
from pathlib import Path
base = Path('/mnt/d/work/runtime-logs/local-package-evidence')
rows = []
for p in sorted(base.glob('*.result')):
    parts = p.read_text(encoding='utf-8').strip().split('|')
    if len(parts) != 8:
        continue
    app, jdk, branch, sha, rc, jar, size, log = parts
    rows.append({'app': app, 'jdk': jdk, 'branch': branch, 'sha': sha,
                 'rc': int(rc), 'jar': jar, 'size': int(size), 'log': log})
(base / 'local-package-results.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
lines = ['# Local package results', '', '| app | jdk | branch | sha | rc | size | jar |', '| --- | ---: | --- | --- | ---: | ---: | --- |']
for r in rows:
    lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
        r['app'], r['jdk'], r['branch'], r['sha'], r['rc'], r['size'], r['jar']))
(base / 'local-package-results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('AGGREGATED', len(rows))
PY
