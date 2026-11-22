"""
@description 历史脚本 validate_ga_changes.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python validate_ga_changes.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Docker CLI 与已启动的守护进程；Python 3 标准库及脚本原有第三方依赖
"""
import re
import yaml
p = r"D:/work/IdeaProjects/car-monit-api-jdk25/.github/workflows/db-upgrade-cloud.yml"
d = yaml.safe_load(open(p, encoding="utf-8"))
print("yaml ok", "og_image_source" in str(d))
s = open(r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh", encoding="utf-8").read()
print("cell if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)), "OG_NEW_IMAGES", "OG_NEW_IMAGES" in s)
w = open(p, encoding="utf-8").read()
print("workflow GA step", "openGauss-Docker-7.0.0-x86_64.tar" in w, "env pass", "OG_NEW_IMAGES" in w)
