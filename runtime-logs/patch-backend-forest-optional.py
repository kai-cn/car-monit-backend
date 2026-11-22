#!/usr/bin/env python3

"""
@description 历史脚本 patch-backend-forest-optional.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-backend-forest-optional.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖

Forest dynamic proxies are not generated in native images. JVM behavior stays the same


because the beans exist there; native gets null and only the endpoints using them degrade.
"""
import base64

import json

import re

import sys

import urllib.request

from pathlib import Path



sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token  # noqa: E402



REPO = 'kai-cn/car-monit-backend'

BRANCH = 'car-monit-backend-jdk25'

ROOT = Path(r'D:\work\IdeaProjects\car-monit-backend-jdk25')

H = {'Authorization': 'Bearer ' + get_token(),

     'Accept': 'application/vnd.github+json',

     'X-GitHub-Api-Version': '2022-11-28',

     'User-Agent': 'forest-optional-patch'}



FILES = [

 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java',

 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java',

 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java',

 'ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java',

 'ruoyi-system/src/main/java/com/ruoyi/base/service/impl/HenDaServiceImpl.java',

 'ruoyi-system/src/main/java/com/ruoyi/base/service/consistency/DataConsistencyService.java',

 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java',

 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java',

 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java',

 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java',

 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java',

 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java',

 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java',

]

FIELD = re.compile(r'^\s*private\s+(?:final\s+)?(?:[\w.]+\.)?(?:Http\w+Service|I\w+Api)\s+\w+\s*;')





def api(uri, method='GET', body=None):

    data = json.dumps(body).encode() if body is not None else None

    req = urllib.request.Request(uri, data=data, headers=H, method=method)

    with urllib.request.urlopen(req, timeout=60) as r:

        return json.loads(r.read().decode())





def patch(text):

    lines = text.split('\n')

    changed = 0

    for i, line in enumerate(lines):

        if not FIELD.match(line):

            continue

        for j in range(max(0, i - 5), i):

            s = lines[j].strip()

            if s == '@Autowired':

                lines[j] = lines[j].replace('@Autowired', '@Autowired(required = false)')

                changed += 1

                break

            if s == '@Resource':

                lines[j] = lines[j].replace('@Resource',

                                            '// @Resource replaced for native: Forest proxy unavailable\n' +

                                            lines[j][:len(lines[j]) - len(lines[j].lstrip())] +

                                            '@Autowired(required = false)')

                changed += 1

                break

    return '\n'.join(lines), changed



total = 0

for rel in FILES:

    uri = f'https://api.github.com/repos/{REPO}/contents/{rel}?ref={BRANCH}'

    try:

        obj = api(uri)

    except Exception as e:

        print('FETCH_FAIL', rel, e)

        continue

    text = base64.b64decode(obj['content']).decode('utf-8')

    new, n = patch(text)

    if n == 0:

        continue

    body = {'message': 'fix(native): make Forest proxies optional for native startup',

            'content': base64.b64encode(new.encode()).decode(), 'sha': obj['sha'], 'branch': BRANCH}

    api(f'https://api.github.com/repos/{REPO}/contents/{rel}', 'PUT', body)

    print('PATCHED', rel, n)

    total += n

print('ANNOTATIONS', total)

