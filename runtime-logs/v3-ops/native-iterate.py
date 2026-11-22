#!/usr/bin/env python3
"""
@description 历史脚本 native-iterate.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python native-iterate.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Iteratively converge native-image --initialize-at-* args from real errors.

Reuses one @argfile (produced by native:compile) so each round skips the
~3-minute Spring AOT phase. Each round runs native-image, parses the exact
classes GraalVM asks for, appends them to the argfile, and retries.

  python native-iterate.py <base-args> [max-rounds]

Output:
  evidence/native-iterate-roundNN.log   per-round native-image output
  evidence/native-iterate-final.args    the argfile that succeeded
  evidence/native-iterate-summary.txt   class list + timings
"""
import os
import re
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else r"D:\work\IdeaProjects\car-monit-api-jdk25\target\tmp\native-image-fast-retry6.args"
MAX_ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
ROOT = r"D:\work\runtime-logs\v3-ops"
BAT = os.path.join(ROOT, "native-retry-from-args.bat")
EV = os.path.join(ROOT, "evidence")
EXE = r"D:\work\IdeaProjects\car-monit-api-jdk25\pro-business-api\target\pro-business-api.exe"
CMD = r"C:\Windows\System32\cmd.exe"

RE_BUILD = re.compile(r"An object of type '([^']+)' was found in the image heap")
RE_FIX_BUILD = re.compile(r"--initialize-at-build-time=([A-Za-z0-9_.$]+)")
RE_FIX_RUN = re.compile(r"Class initialization of ([A-Za-z0-9_.$]+) failed")

os.makedirs(EV, exist_ok=True)
lines = open(BASE, encoding="utf-8").read().splitlines()
summary = ["base_args=%s" % BASE, "started=%s" % datetime.now().isoformat()]


def build_classes(text):
    out = set(RE_BUILD.findall(text))
    out |= set(x for x in RE_FIX_BUILD.findall(text) if x)
    return out


def run_classes(text):
    return set(RE_FIX_RUN.findall(text))


for rnd in range(1, MAX_ROUNDS + 1):
    args_path = os.path.join(os.path.dirname(BASE), "native-image-iterate-r%02d.args" % rnd)
    open(args_path, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    log = os.path.join(EV, "native-iterate-round%02d.log" % rnd)
    label = "iterate-r%02d" % rnd
    print("=== ROUND %d args=%s lines=%d ===" % (rnd, args_path, len(lines)), flush=True)
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run([CMD, "/c", BAT, args_path, label], stdout=f,
                              stderr=subprocess.STDOUT, cwd=ROOT, timeout=1800)
    elapsed = time.time() - t0
    text = open(log, encoding="utf-8", errors="replace").read()
    ok = proc.returncode == 0 and os.path.isfile(EXE)
    print("  rc=%d elapsed=%.0fs exe=%s" % (proc.returncode, elapsed, os.path.isfile(EXE)), flush=True)
    summary.append("round=%d rc=%d elapsed_s=%.0f exe=%s" % (rnd, proc.returncode, elapsed, ok))

    if ok:
        final = os.path.join(EV, "native-iterate-final.args")
        open(final, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        summary.append("RESULT=SUCCESS final_args=%s" % final)
        break

    new_build = build_classes(text) - {l.split("=", 1)[1] for l in lines
                                       if l.startswith("--initialize-at-build-time=")}
    new_run = run_classes(text) - {l.split("=", 1)[1] for l in lines
                                   if l.startswith("--initialize-at-run-time=")}
    if not new_build and not new_run:
        tail = "\n".join(text.splitlines()[-25:])
        summary.append("RESULT=STALLED (no new classes parsed)")
        summary.append(tail)
        print("  STALLED, last lines:\n" + tail, flush=True)
        break
    for c in sorted(new_build):
        lines.append("--initialize-at-build-time=" + c)
        print("  + build-time %s" % c, flush=True)
        summary.append("  build-time %s" % c)
    for c in sorted(new_run):
        lines.append("--initialize-at-run-time=" + c)
        print("  + run-time %s" % c, flush=True)
        summary.append("  run-time %s" % c)
else:
    summary.append("RESULT=MAX_ROUNDS_REACHED")

open(os.path.join(EV, "native-iterate-summary.txt"), "w", encoding="utf-8", newline="\n").write(
    "\n".join(summary) + "\n")
print("\n".join(summary[-15:]), flush=True)
