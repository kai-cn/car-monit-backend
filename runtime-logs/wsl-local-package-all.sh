#!/usr/bin/env bash
# @description 历史脚本 wsl-local-package-all.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash wsl-local-package-all.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: recompile and package all Java branches locally from clean worktrees.
# Idea:
# - read the generated manifest (worktree|app|jdk|branch|module|sha)
# - use the matching local JDK (8/17/21/25) and Maven cache
# - skip tests and AOT for JVM packaging, matching cloud JUnit workflow
# - collect package status, jar path, size, and logs as evidence
# Risk: writes only under the temporary worktree root and local runtime-logs evidence dir.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
MANIFEST=$ROOT/local-package-manifest.tsv
OUT=$ROOT/local-package-evidence
LOGS=$OUT/logs
JARS=$OUT/jars
mkdir -p "$OUT" "$LOGS" "$JARS"

declare -A JVMS=(
  [8]=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
  [17]=/home/dev/tools/mandrel-java17-23.0.6.0-Final
  [21]=/home/dev/tools/mandrel-java21-23.1.13.0-Final
  [25]=/home/dev/tools/mandrel-java25-25.0.4.1-Final
)

declare -a PIDS=()
declare -a NAMES=()
while IFS='|' read -r path app jdk branch module sha; do
  [ -z "$path" ] && continue
  name="${app}__$(echo "$branch" | tr '/ ' '__')"
  (
    log="$LOGS/$name.log"
    {
      echo "BRANCH=$branch APP=$app JDK=$jdk MODULE=$module SHA=$sha"
      echo "JAVA_HOME=${JVMS[$jdk]}"
      cd "$path" || exit 90
      JAVA_HOME="${JVMS[$jdk]}" PATH="${JVMS[$jdk]}/bin:$PATH" \
        mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl "$module" -am clean package
    } > "$log" 2>&1
    rc=$?
    jar=$(find "$path/$module/target" -maxdepth 1 -type f -name '*.jar' ! -name 'original-*' 2>/dev/null | head -1)
    size=0
    [ -n "$jar" ] && size=$(stat -c %s "$jar")
    printf '%s|%s|%s|%s|%s|%s|%s|%s\n' "$app" "$jdk" "$branch" "$sha" "$rc" "$jar" "$size" "$log" > "$OUT/$name.result"
  ) &
  PIDS+=($!)
  NAMES+=("$name")
  if [ ${#PIDS[@]} -ge 2 ]; then
    wait "${PIDS[0]}" "${PIDS[1]}" 2>/dev/null || true
    PIDS=()
  fi
done < "$MANIFEST"
for pid in "${PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done

python3 - <<'PY'
import json
from pathlib import Path
base = Path('/mnt/d/work/runtime-logs/local-package-evidence')
rows = []
for p in sorted(base.glob('*.result')):
    app, jdk, branch, sha, rc, jar, size, log = p.read_text(encoding='utf-8').strip().split('|')
    rows.append({'app': app, 'jdk': jdk, 'branch': branch, 'sha': sha,
                 'rc': int(rc), 'jar': jar, 'size': int(size), 'log': log})
(base / 'local-package-results.json').write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding='utf-8')
lines = ['# Local package results', '', '| app | jdk | branch | sha | rc | size | jar |', '| --- | ---: | --- | --- | ---: | ---: | --- |']
for r in rows:
    lines.append('| %s | %s | %s | %s | %s | %s | %s |' % (
        r['app'], r['jdk'], r['branch'], r['sha'], r['rc'], r['size'], r['jar']))
(base / 'local-package-results.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('\n'.join(lines))
PY
