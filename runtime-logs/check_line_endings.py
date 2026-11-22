"""
@description 历史脚本 check_line_endings.py：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python check_line_endings.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
for p in [r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh",

          r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_dump.sh"]:

    b = open(p, "rb").read()

    print(p.split("/")[-1], "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"))

