#!/usr/bin/env python3

"""
@description 历史脚本 verify_ga_runs.py：验证配置、构建或安全不变量；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python verify_ga_runs.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
# 用途：确认 GA 分支 run 使用真实 dump + GA 版本串 + fails=0（依据云端 job 日志）。

import json

import re

import sys

import urllib.request

sys.path.insert(0, "D:/work/runtime-logs")

from gh_cred import get_token



H = {"Authorization": "Bearer " + get_token(), "User-Agent": "x"}

RUNS = {

    "car-monit-api-jdk21": 44285673201,

    "car-monit-api-jdk17": 44285699892,

    "car-monit-api-java-V3": 44285716860,

}



class NR(urllib.request.HTTPRedirectHandler):

    def redirect_request(self, req, fp, code, msg, headers, newurl):

        return urllib.request.Request(newurl, headers={"User-Agent": "x"})



opener = urllib.request.build_opener(NR)

for br, rid in RUNS.items():

    with urllib.request.urlopen(urllib.request.Request(

            "https://api.github.com/repos/kai-cn/car-monit-api/actions/runs/%s/jobs?per_page=100" % rid,

            headers=H), timeout=60) as r:

        jobs = json.loads(r.read())

    jid = next((j["id"] for j in jobs["jobs"] if "opengauss" in j.get("name", "")), None)

    if not jid:

        print(br, "no opengauss job"); continue

    req = urllib.request.Request(

        "https://api.github.com/repos/kai-cn/car-monit-api/actions/jobs/%s/logs" % jid, headers=H)

    try:

        data = opener.open(req, timeout=180).read().decode("utf-8", "replace")

    except Exception as e:

        print(br, "log fail", repr(e)); continue

    s = re.sub(r"\x1b\[[0-9;]*m", "", data)

    dump = re.findall(r"dump bytes: (\d+)", s)

    ver = re.findall(r"\(openGauss 7\.0\.0 build [0-9a-f]+\)", s)

    ep = re.findall(r"Endpoints\*\*: (\d+) \| status_match=(\d+).*?fails=(\d+)", s)

    print(br, "run", rid, "dump=", dump[:1], "GA_version=", bool(ver), "endpoints=", ep[:1])

