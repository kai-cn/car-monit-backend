#!/usr/bin/env python3
# 用途：从云端 job 日志确认真实迁移（dump bytes 非 0）+ 一致性 fails。
import re
import subprocess
import sys
sys.path.insert(0, "D:/work/runtime-logs")
from gh_cred import get_token
import json
import urllib.request

repo = "kai-cn/car-monit-api"
H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}
RUNS = {"feature-dbupgrade": 44268498258, "car-monit-api-jdk21": 44268999597,
        "car-monit-api-jdk17": 44269014488, "car-monit-api-java-V3": 44269030678}

for br, rid in RUNS.items():
    with urllib.request.urlopen(urllib.request.Request(
            "https://api.github.com/repos/%s/actions/runs/%s/jobs?per_page=100" % (repo, rid),
            headers=H), timeout=60) as r:
        jobs = json.loads(r.read())
    jid = next((j["id"] for j in jobs["jobs"] if "opengauss" in j.get("name", "")), None)
    if not jid:
        print(br, "no opengauss job"); continue
    req = urllib.request.Request("https://api.github.com/repos/%s/actions/jobs/%s/logs" % (repo, jid),
                                 headers=H)
    class NR(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return urllib.request.Request(newurl, headers={"User-Agent": "x"})
    try:
        data = urllib.request.build_opener(NR).open(req, timeout=120).read().decode("utf-8", "replace")
    except Exception as e:
        print(br, "log fetch fail", repr(e)); continue
    s = re.sub(r"\x1b\[[0-9;]*m", "", data)
    dump = re.findall(r"dump bytes: (\d+) method: ([^\r\n]+)", s)
    ep = re.findall(r"Endpoints\*\*: (\d+) \| status_match=(\d+).*?fails=(\d+)", s)
    print(br, "dump=", dump[:1], "endpoints=", ep[:1])
