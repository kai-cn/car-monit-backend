#!/usr/bin/env python3

"""
@description 历史脚本 annotate-v3-scripts.py：批量补充脚本或代码注释；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python annotate-v3-scripts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Operational helper created during the native/CICD verification session.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Annotate v3 native/parity operational scripts in runtime-logs and api-java-V3."""

from pathlib import Path



HEADERS = {

    'v3-native-build-measured.sh': '''# Build a native image in WSL/ext4 with the pinned Linux Maven and record wall/CPU/RSS via /usr/bin/time -v.

# Usage: v3-native-build-measured.sh <api|backend> <jdk> <repo-name> <label> [mandrel-version]

# Precondition: stop mysql_wsl/opengauss first; native-image needs >10 GB RAM in this 12 GB WSL VM.''',

    'v3-native-build-fast.sh': '''# Experimental native build: apply native-flink-exclude in both reactor stages and skip the

# second `clean`. Saves ~2% wall time; only safe when all sources were freshly compiled in stage 1.''',

    'v3-native-build-fast-measured.sh': '''# /usr/bin/time -v wrapper for v3-native-build-fast.sh; writes resource-<label>.txt evidence.''',

    'v3-compare-business.sh': '''# Native vs JVM multi-endpoint business-integrity comparison (cloud/local agnostic).

# Usage: v3-compare-business.sh --app <api|backend> --native <elf> --jar <jar> --java <java> --label <name>

# DB credentials are read from container env at runtime only; volatile JSON keys are normalized

# before semantic comparison, but NONDET never exempts an HTTP status mismatch.''',

    'v3-probe-http.sh': '''# Fast post-build smoke test: start a native ELF or fat jar and probe one business endpoint.

# Usage: v3-probe-http.sh <elf-or-jar> <label> [port]

# For jars set JAVA=/path/to/java; credentials are injected from container env at runtime.''',

    'v3-verify-jdk-matrix.sh': '''# Reproduce startup + business-endpoint checks for every existing JDK artifact in the worktrees.

# Does NOT build artifacts; run build-jvm-jar.sh / v3-native-build-linux.sh first.''',

    'v3-port-jdk25-native-config.py': '''# Port proven JDK25 native-image settings (plugin version, class-init args, resource includes)

# to Boot4 JDK17/21 module poms without touching unrelated configuration.''',

    'v3-run-native-linux.sh': '''# Start a native ELF, sample readiness/RSS/threads/errors for a fixed window, then stop it.

# Injects BOTH openGauss (GS_PASSWORD) and MySQL (CARMONIT_MYSQL_*) credentials from containers;

# defaults to port 19902 and preflights the port to avoid false-positive readiness.''',

    'v3-run-jvm-linux.sh': '''# JVM counterpart of v3-run-native-linux.sh; same credentials/port contract for A/B comparability.''',

    'v3-compare-native-jvm.sh': '''# Long-running native vs JVM A/B: startup, steady RSS/latency, and stability drift.

# Both variants receive identical Spring args and DB credentials; see final doc for measured results.''',

}



ROOTS = [Path(r'D:\work\runtime-logs\v3-ops'), Path(r'D:\work\IdeaProjects\car-monit-api-java-V3\scripts\v3\ops')]



def add(path: Path, header: str):

    text = path.read_text(encoding='utf-8', errors='replace')

    if header.splitlines()[0] in text:

        return False

    if text.startswith('#!'):

        first, _, rest = text.partition('\n')

        path.write_text(first + '\n' + header + '\n' + rest.lstrip('\n'), encoding='utf-8')

    else:

        path.write_text(header + '\n' + text.lstrip('\n'), encoding='utf-8')

    return True



changed=[]

for root in ROOTS:

    for name, header in HEADERS.items():

        p = root / name

        if p.exists() and add(p, header):

            changed.append(str(p))

print('annotated', len(changed))

for c in changed: print(' ', c)

