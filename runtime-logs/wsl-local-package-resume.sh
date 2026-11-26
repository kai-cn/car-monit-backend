#!/usr/bin/env bash
# @description 历史脚本 wsl-local-package-resume.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22 23:45:04
# @usage bash wsl-local-package-resume.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Maven 与对应 JDK
# Purpose: resume local Java packaging from an interrupted run.
# Idea:
# - read the same manifest, skip branches that already have a .result file
# - build two branches at a time with the matching JDK
# - aggregate all .result files into JSON/Markdown after remaining builds finish
# Risk: writes under temporary worktrees and local evidence directory only.
set -uo pipefail
ROOT=/mnt/d/work/runtime-logs
MANIFEST=$ROOT/local-package-manifest.tsv
OUT=$ROOT/local-package-evidence
LOGS=$OUT/logs
mkdir -p "$OUT" "$LOGS"

declare -A JVMS=(
  [8]=/usr/lib/jvm/java-1.8.0-openjdk-1.8.0.502.b07-1.oe2403sp4.x86_64
  [17]=/home/dev/tools/mandrel-java17-23.0.6.0-Final
  [21]=/home/dev/tools/mandrel-java21-23.1.13.0-Final
  [25]=/home/dev/tools/mandrel-java25-25.0.4.1-Final
)

pids=()
while IFS='|' read -r path app jdk branch module sha; do
  [ -z "$path" ] && continue
  name="${app}__$(echo "$branch" | tr '/ ' '__')"
  result="$OUT/$name.result"
  [ -f "$result" ] && continue
  (
    log="$LOGS/$name.log"
    {
      echo "RESUME_BUILD branch=$branch app=$app jdk=$jdk module=$module sha=$sha"
      cd "$path" || exit 90
      JAVA_HOME="${JVMS[$jdk]}" PATH="${JVMS[$jdk]}/bin:$PATH" \
        mvn -B -ntp -DskipTests -Dspring-boot.aot.skip=true -pl "$module" -am clean package
    } > "$log" 2>&1
    rc=$?
    jar=$(find "$path/$module/target" -maxdepth 1 -type f -name '*.jar' ! -name 'original-*' 2>/dev/null | head -1)
    size=0
    [ -n "$jar" ] && size=$(stat -c %s "$jar")
    printf '%s|%s|%s|%s|%s|%s|%s|%s\n' "$app" "$jdk" "$branch" "$sha" "$rc" "$jar" "$size" "$log" > "$result"
  ) &
  pids+=($!)
  if [ ${#pids[@]} -ge 2 ]; then
    wait "${pids[0]}" "${pids[1]}" 2>/dev/null || true
    pids=()
  fi
done < "$MANIFEST"
for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null || true; done

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
echo 'LOCAL_PACKAGE_RESUME_DONE'
