"""
LEGACY-SCRIPT-ANNOTATION
文件：diag_fail.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
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
