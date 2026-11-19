import re
for name in ["db_cell.sh", "db_dump.sh"]:
    p = r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/" + name
    s = open(p, encoding="utf-8").read()
    print(name, "if/fi", len(re.findall(r"\bif\b", s)), len(re.findall(r"\bfi\b", s)),
          "positional", '"$dbname" -Fp' in s, "OG_NEW_IMAGES", "OG_NEW_IMAGES" in s,
          "local_inspect", "docker image inspect" in s)
