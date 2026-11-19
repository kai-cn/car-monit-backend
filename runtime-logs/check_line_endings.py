for p in [r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_cell.sh",
          r"D:/work/IdeaProjects/car-monit-api-jdk25/scripts/v3/ops/dbupgrade/db_dump.sh"]:
    b = open(p, "rb").read()
    print(p.split("/")[-1], "CRLF", b.count(b"\r\n"), "LF", b.count(b"\n"))
