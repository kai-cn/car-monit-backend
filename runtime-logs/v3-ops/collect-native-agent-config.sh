#!/usr/bin/env bash
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Collect run results into a concise report.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
# GraalVM tracing-agent pass: run the JVM fat jar and record dynamic reflection
# (Forest etc.) into reachability metadata for the next native-image build.
set -u
JAVA="/d/jdk/mandrel-25.0.4.1-Final/bin/java.exe"
JAR="D:/work/IdeaProjects/car-monit-api-jdk25/pro-business-api/target/pro-business-api-1.0.jar"
OUT="D:/work/runtime-logs/v3-ops/agent-config"
LOG="D:/work/runtime-logs/v3-ops/evidence/native-agent-jvm.log"
mkdir -p "$OUT"
export MSYS_NO_PATHCONV=1

echo "==== tracing agent JVM run ===="
echo "java=$JAVA"
echo "jar=$JAR"
echo "out=$OUT"
"$JAVA" -agentlib:native-image-agent=config-output-dir="$OUT",config-write-period-secs=10,config-write-initial-delay-secs=5 \
  -jar "$JAR" --server.port=19902 > "$LOG" 2>&1 &
PID=$!
echo "pid=$PID"

UP=0
for i in $(seq 1 75); do
  if curl -s --noproxy '*' -m 2 -o /dev/null "http://127.0.0.1:19902/actuator/health"; then
    UP=1; echo "port_ready after ${i} checks"; break
  fi
  if ! kill -0 "$PID" 2>/dev/null; then echo "JVM exited early"; break; fi
  sleep 2
done
echo "port_ready=$UP"

# Exercise a few common endpoints so the agent sees request-path reflection.
for path in / /actuator/health /prod-api/getInfo /favicon.ico; do
  code=$(curl -s --noproxy '*' -m 5 -o /dev/null -w '%{http_code}' "http://127.0.0.1:19902$path" || echo 000)
  echo "probe $path -> $code"
done

sleep 12
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID" 2>/dev/null || true
  sleep 3
  kill -9 "$PID" 2>/dev/null || true
fi
echo "==== agent config output ===="
ls -la "$OUT" 2>/dev/null
echo "==== JVM log tail ===="
tail -25 "$LOG"
