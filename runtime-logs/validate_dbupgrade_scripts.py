"""
@description 历史脚本 validate_dbupgrade_scripts.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python validate_dbupgrade_scripts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

