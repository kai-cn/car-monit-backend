import re
import yaml
p = r"D:/work/IdeaProjects/car-monit-api-jdk25/.github/workflows/db-upgrade-cloud.yml"
d = yaml.safe_load(open(p, encoding="utf-8"))
print("yaml ok", "og_image_source" in str(d))
s = open(r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh", encoding="utf-8").read()
print("cell if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)), "OG_NEW_IMAGES", "OG_NEW_IMAGES" in s)
w = open(p, encoding="utf-8").read()
print("workflow GA step", "openGauss-Docker-7.0.0-x86_64.tar" in w, "env pass", "OG_NEW_IMAGES" in w)
