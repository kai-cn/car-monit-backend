#!/usr/bin/env bash
# Kill any leftover car-monit native/JVM process holding the given port.
set -u
PORT=${1:-9902}
PIDS=$(ss -lntp 2>/dev/null | awk -v p=":$PORT" '$4 ~ p {print $NF}' | sed -E 's/.*pid=([0-9]+).*/\1/' | sort -u)
if [ -z "${PIDS}" ]; then
  echo "no listener on $PORT"
else
  echo "killing: $PIDS"
  for pid in $PIDS; do kill -9 "$pid" 2>/dev/null || true; done
fi
sleep 1
ss -lntp 2>/dev/null | grep -c ":$PORT" || true
echo "done"
