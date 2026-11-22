#!/usr/bin/env bash
# @description 历史脚本 wsl-rebuild-backend-master-ext4.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-rebuild-backend-master-ext4.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: rebuild backend master in WSL ext4 because D drive reached 100% capacity.
# Idea:
# - copy the clean detached source tree from the Windows mount into /home/dev
# - run the same JDK8 Maven package command there
# - overwrite backend__master.result and aggregate all 16 local package results
# Risk: writes only /home/dev/local-package and local evidence files; no user source tree is modified.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
OUT=$ROOT/local-package-evidence
SRC=/mnt/d/work/IdeaProjects/_local-package-20261122-130307/backend__master
DST=/home/dev/local-package/backend-master
LOG=$OUT/logs/backend__master-ext4.log

echo "COPY $(date -Is)" > "$LOG"
rm -rf "$DST"
mkdir -p "$DST"
cp -a "$SRC"/. "$DST"/ >> "$LOG" 2>&1

echo "BUILD $(date -Is)" >> "$LOG"
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
cd "$DST" || exit 90
JAVA_HOME="$JAVA_HOME" PATH="$JAVA_HOME/bin:$PATH" \
  mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl ruoyi-admin -am clean package >> "$LOG" 2>&1
rc=$?
JAR="$DST/ruoyi-admin/target/ruoyi-admin.jar"
SIZE=0
[ -f "$JAR" ] && SIZE=$(stat -c %s "$JAR")
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
