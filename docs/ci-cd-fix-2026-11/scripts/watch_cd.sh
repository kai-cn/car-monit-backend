#!/usr/bin/env bash
# 轮询 api cd-standalone run 直到完成，打印结论。
TOK="${GH_TOKEN_OVERRIDE:-}"
REPO="${REPO:-car-monit-api}"
RID="${1:-44436940503}"
for i in $(seq 1 60); do
  R=$(curl -sL --retry 3 -u "oauth2:$TOK" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/kai-cn/$REPO/actions/runs/$RID")
  STATUS=$(echo "$R" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('conclusion') or d.get('status'))" 2>/dev/null)
  echo "[$(date +%H:%M:%S)] run $RID => $STATUS"
  if [ "$STATUS" = "success" ] || [ "$STATUS" = "failure" ] || [ "$STATUS" = "cancelled" ]; then
    echo "FINAL=$STATUS"
    # 打印 jobs 结论
    curl -sL --retry 3 -u "oauth2:$TOK" -H "Accept: application/vnd.github+json" \
      "https://api.github.com/repos/kai-cn/$REPO/actions/runs/$RID/jobs" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for j in d.get('jobs',[]): print(j['id'],j['name'],j.get('conclusion') or j['status'])
"
    exit 0
  fi
  sleep 30
done
echo "TIMEOUT waiting $RID"
