"""
LEGACY-SCRIPT-ANNOTATION
文件：validate_dbupgrade_scripts.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
"""
import re
paths = [
    r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh",
    r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_dump.sh",
]
for p in paths:
    s = open(p, encoding="utf-8").read()
    name = p.split("/")[-1]
    pos = '"$dbname" -Fp' in s
    print(name, "if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)),
          "positional_gs_dump", pos, "dbname_persist", "_dbname.txt" in s)
