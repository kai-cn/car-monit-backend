#!/usr/bin/env bash
# @description 历史脚本 wsl-retest-diag.sh：驱动 WSL Docker/数据库完成本机验证；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
# @author Tencent Hunyuan Hy
# @date 2026-11-22
# @usage bash wsl-retest-diag.sh [args]；执行前确认目标环境与本地容器状态。
# @dependencies Java 运行时
# Purpose: diagnose why WSL local load phase recorded transport errors.
# Idea: inspect app log tail, process state, and port state after retest.
# Risk: read-only.
echo "=== app log tail ==="
tail -60 /home/dev/local-retest/app.log 2>/dev/null || true
echo "=== java processes ==="
ps -ef | grep -E 'java -jar' | grep -v grep | head -20 || true
echo "=== port 19903 ==="
ss -ltnp 2>/dev/null | grep 19903 || true
echo "=== contract sample ==="
python3 - <<'PY'
import json
from pathlib import Path
p = Path('/home/dev/local-retest/junit-contract.json')
if p.exists():
    rows = json.loads(p.read_text(encoding='utf-8')).get('endpoints', [])
    from collections import Counter
    print('count', len(rows), Counter(int(r.get('status',0)) for r in rows).most_common(8))
    print('errors', Counter(r.get('error','') for r in rows if r.get('error')).most_common(5))
PY
