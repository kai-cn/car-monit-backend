"""
LEGACY-SCRIPT-ANNOTATION
文件：diag_fail2.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
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
