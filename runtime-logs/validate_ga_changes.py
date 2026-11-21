"""
LEGACY-SCRIPT-ANNOTATION
文件：validate_ga_changes.py
用途：运维辅助脚本。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：执行前确认目标环境、凭据与影响范围。
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
