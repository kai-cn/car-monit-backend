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
