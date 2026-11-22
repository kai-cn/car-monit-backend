"""
@description 历史脚本 diag_fail2.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python diag_fail2.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
import re

def load(p):

    s=open(p,encoding="utf-8",errors="replace").read()

    return re.sub(r"\x1b\[[0-9;]*m","",s).splitlines()

def tail(p,n=35):

    ls=load(p)

    for l in ls[-n:]:

        print(l[27:] if len(l)>27 else l)



print("=== api-v3-mysql tail ===")

tail("D:/work/runtime-logs/fail-api-v3-mysql.log",30)

print()

print("=== bk-v3 tail ===")

tail("D:/work/runtime-logs/fail-bk-v3.log",25)

print()

print("=== jdk17 og image lines ===")

for l in load("D:/work/runtime-logs/fail-api-jdk17-og.log"):

    v=l[27:] if len(l)>27 else l

    if any(k in v for k in ["pull","image","Image","opengauss/","enmotech/","status","Exited","restart"]):

        print(v)

