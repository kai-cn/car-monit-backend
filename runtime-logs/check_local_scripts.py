"""
@description 历史脚本 check_local_scripts.py：只读校验环境、语法或结果；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python check_local_scripts.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
import re
for name in ["db_cell.sh", "db_dump.sh"]:
    p = r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/" + name
    s = open(p, encoding="utf-8").read()
    print(name, "if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)),
          "positional", '"$dbname" -Fp' in s, "OG_NEW_IMAGES", "OG_NEW_IMAGES" in s,
          "local_inspect", "docker image inspect" in s)
