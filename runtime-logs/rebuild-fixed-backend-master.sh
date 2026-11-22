#!/usr/bin/env bash
# @description 重建修复 geometry_copy1 遗留表引用后的 backend master jar，并更新本机打包证据。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:36:07
# @usage bash /mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs/rebuild-fixed-backend-master.sh
# @dependencies WSL ext4 空间、JDK8、Maven、当前 master 工作树。
set -uo pipefail
SRC=/mnt/d/work/IdeaProjects/car-monit-backend-new
DST=/home/dev/local-package/backend-master
OUT=/mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs/local-package-evidence
LOG=$OUT/logs/backend__master-fixed.log
mkdir -p "$OUT/logs" "$DST"

echo "SYNC $(date '+%Y-%m-%d %H:%M:%S')" > "$LOG"
cp -a "$SRC"/. "$DST"/ >> "$LOG" 2>&1

echo "BUILD $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"
JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
cd "$DST" || exit 90
JAVA_HOME="$JAVA_HOME" PATH="$JAVA_HOME/bin:$PATH" \
  mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl ruoyi-admin -am clean package >> "$LOG" 2>&1
rc=$?
JAR="$DST/ruoyi-admin/target/ruoyi-admin.jar"
SIZE=0
[ -f "$JAR" ] && SIZE=$(stat -c %s "$JAR")
printf '%s|%s|%s|%s|%s|%s|%s|%s\n' backend 8 master fixed "$rc" "$JAR" "$SIZE" "$LOG" > "$OUT/backend__master.result"
echo "DONE rc=$rc size=$SIZE $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"

python3 - <<'PY'
import json
from pathlib import Path
base = Path('/mnt/d/work/IdeaProjects/car-monit-backend-new/runtime-logs/local-package-evidence')
rows = []
for p in sorted(base.glob('*.result')):
    parts = p.read_text(encoding='utf-8').strip().split('|')
    if len(parts) != 8:
        continue
    app, jdk, branch, sha, rc, jar, size, log = parts
    rows.append({'app': app, 'jdk': jdk, 'branch': branch, 'sha': sha,
                 'rc': int(rc), 'jar': jar, 'size': int(size), 'log': log})
(base / 'local-package-results.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
print('AGGREGATED', len(rows), 'SUCCESS', sum(1 for r in rows if r['rc'] == 0))
PY
