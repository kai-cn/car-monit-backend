"""
LEGACY-SCRIPT-ANNOTATION
文件：check_local_scripts.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
import re
for name in ["db_cell.sh", "db_dump.sh"]:
    p = r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/" + name
    s = open(p, encoding="utf-8").read()
    print(name, "if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)),
          "positional", '"$dbname" -Fp' in s, "OG_NEW_IMAGES", "OG_NEW_IMAGES" in s,
          "local_inspect", "docker image inspect" in s)
