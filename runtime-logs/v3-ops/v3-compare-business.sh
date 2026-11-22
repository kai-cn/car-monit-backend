#!/usr/bin/env bash

# @description 历史脚本 v3-compare-business.sh：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author AI Assistant
# @date 2026-11-22 23:45:04
# @usage bash v3-compare-business.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Docker CLI 与已启动的守护进程
# LEGACY-SCRIPT-ANNOTATION

# 文件：v3-compare-business.sh

# 用途：运维辅助脚本。

# 思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。

# 风险：执行前确认目标环境、凭据与影响范围。

# Native vs JVM multi-endpoint business-integrity comparison (cloud/local agnostic).

# Usage: v3-compare-business.sh --app <api|backend> --native <elf> --jar <jar> --java <java> --label <name>

# DB credentials are read from container env at runtime only; volatile JSON keys are normalized

# before semantic comparison, but NONDET never exempts an HTTP status mismatch.

# Native vs JVM business-integrity comparison (multi-endpoint).

#   v3-compare-business.sh --app api --native <elf> --jar <jar> --java <java> --label <label>

set -uo pipefail

APP=api; NATIVE=""; JAR=""; JAVA=""; LABEL="cmp"

PN=19902; PJ=19903

EV=/mnt/d/work/runtime-logs/v3-ops/evidence

while [[ $# -gt 0 ]]; do

  case "$1" in

    --app) APP=$2; shift 2 ;; --native) NATIVE=$2; shift 2 ;; --jar) JAR=$2; shift 2 ;;

    --java) JAVA=$2; shift 2 ;; --label) LABEL=$2; shift 2 ;;

    --port-native) PN=$2; shift 2 ;; --port-jvm) PJ=$2; shift 2 ;; *) shift ;;

  esac

done

mkdir -p "$EV"



GS_PASS=$(docker exec opengauss env 2>/dev/null | sed -n 's/^[^=]*GS_PASSWORD=//p' | tr -d '\r' | head -1)

MYSQL_PASS=$(docker exec mysql_wsl env 2>/dev/null | sed -n 's/^[^=]*MYSQL_ROOT_PASSWORD=//p' | tr -d '\r' | head -1)

[[ -n "$GS_PASS" && -n "$MYSQL_PASS" ]] || { echo "FATAL DB creds"; exit 4; }

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME=gaussdb

export SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD="$GS_PASS"

export CARMONIT_MYSQL_USERNAME=root CARMONIT_MYSQL_PASSWORD="$MYSQL_PASS"

export EXPORT_DOWNLOAD_SECRET="local-verify-${LABEL}-secret-key"



case "$APP" in

  api)

    ENDPOINTS=(

      '/base/feerecords/list?pageNum=1&pageSize=1'

      '/base/gantry/list'

      '/base/gantry/listAll'

      '/base/toll/list'

      '/api/v1/bigscreen/stats/audit'

      '/api/v1/bigscreen/stats/escape'

      '/api/v1/bigscreen/stats/warning-top?topN=10'

    )

    ;;

  backend)

    ENDPOINTS=('/login' '/getInfo' '/captchaImage')

    ;;

esac



port_open(){ (echo > "/dev/tcp/127.0.0.1/$1") >/dev/null 2>&1; }

wait_ready(){

  local p=$1 pid=$2 i

  for i in $(seq 1 300); do

    kill -0 "$pid" 2>/dev/null || return 1

    port_open "$p" && return 0

    sleep 0.5

  done

  return 1

}

collect(){

  local variant=$1 port=$2 i ep code ms out

  for i in "${!ENDPOINTS[@]}"; do

    ep="${ENDPOINTS[$i]}"

    out=$(curl -s -o "$EV/$LABEL-$variant-$i.body" -w '%{http_code} %{time_total}' --max-time 12 \

      "http://127.0.0.1:$port$ep" 2>/dev/null || echo '000 0')

    read -r code ms <<< "$out"

    printf '%s,%s,%s,%s\n' "$variant" "$i" "$code" "$ms" >> "$EV/$LABEL-codes.csv"

  done

}

echo "variant,endpoint,http_code,latency_s" > "$EV/$LABEL-codes.csv"



echo "==== $LABEL: starting JVM on $PJ ===="

"$JAVA" -jar "$JAR" --server.port="$PJ" >"$EV/$LABEL-jvm.log" 2>&1 &

JP=$!

wait_ready "$PJ" "$JP" || { echo "JVM not ready"; tail -20 "$EV/$LABEL-jvm.log"; }

collect jvm "$PJ"

kill "$JP" 2>/dev/null; wait "$JP" 2>/dev/null; sleep 2



echo "==== $LABEL: starting native on $PN ===="

if [[ "$APP" == backend ]]; then

  export JAVA_TOOL_OPTIONS="-Dorg.apache.commons.logging.LogFactory=org.apache.commons.logging.impl.Slf4jLogFactory"

fi

"$NATIVE" --server.port="$PN" >"$EV/$LABEL-native.log" 2>&1 &

NP=$!

wait_ready "$PN" "$NP" || { echo "NATIVE not ready"; tail -20 "$EV/$LABEL-native.log"; }

collect native "$PN"

kill "$NP" 2>/dev/null; wait "$NP" 2>/dev/null



python3 - "$LABEL" "$EV" "${#ENDPOINTS[@]}" <<'PY'

import json, os, sys

from pathlib import Path

label, ev, n = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])

volatile = {'timestamp','time','requestId','traceId','token','expireTime','serverTime','now','cost','duration','date'}

def norm(x):

    if isinstance(x, dict):

        return {k: norm(v) for k,v in x.items() if k not in volatile}

    if isinstance(x, list):

        return [norm(v) for v in x]

    return x

rows=[]

for i in range(n):

    codes={}

    for v in ('jvm','native'):

        p=ev/f'{label}-{v}-{i}.body'

        raw=p.read_bytes() if p.exists() else b''

        try: obj=norm(json.loads(raw.decode('utf-8',errors='replace'))); ok='json'

        except Exception: obj=raw.decode('utf-8',errors='replace')[:2000]; ok='text'

        codes[v]=(raw, obj, ok)

    same = codes['jvm'][0]==codes['native'][0]

    semantic = codes['jvm'][1]==codes['native'][1]

    rows.append({'endpoint':i,'bytes_jvm':len(codes['jvm'][0]),'bytes_native':len(codes['native'][0]),

                 'exact':same,'semantic':semantic,'type':codes['jvm'][2]})

out={'label':label,'app':sys.argv[0],'endpoints':rows}

(ev/f'{label}-business.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')

for r in rows:

    print(f"ep{r['endpoint']}: bytes {r['bytes_jvm']}/{r['bytes_native']} exact={r['exact']} semantic={r['semantic']}")

print('BUSINESS_OK', ev/f'{label}-business.json')

PY

