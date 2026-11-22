"""
@description 历史脚本 diag_fail.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python diag_fail.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import re



def load(p):

    s = open(p, encoding="utf-8", errors="replace").read()

    return re.sub(r"\x1b\[[0-9;]*m", "", s).splitlines()



def show(p, needle, before=12, after=6, strip=27):

    lines = load(p)

    idx = next((i for i, l in enumerate(lines) if needle in l), None)

    if idx is None:

        print("needle not found:", needle)

        return

    for l in lines[max(0, idx-before):idx+after]:

        print(l[strip:] if len(l) > strip else l)



print("=== jdk17 og failure context ===")

show("D:/work/runtime-logs/fail-api-jdk17-og.log", "failed to connect Unknown")

print()

print("=== V3 build error context ===")

show("D:/work/runtime-logs/fail-api-v3-mysql.log", "systemPath", 8, 12)

