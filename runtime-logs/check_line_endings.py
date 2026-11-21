"""
LEGACY-SCRIPT-ANNOTATION
文件：check_line_endings.py
用途：只读检查/诊断。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：通常只读；若脚本内有明确写操作以其自身说明为准。
"""
for p in [r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh",
          r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_dump.sh"]:
    b = open(p, "rb").read()
    print(p.split("/")[-1], "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"))
