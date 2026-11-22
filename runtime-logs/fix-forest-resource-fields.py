#!/usr/bin/env python3
"""
@description 历史脚本 fix-forest-resource-fields.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22
@usage python fix-forest-resource-fields.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Python 3 标准库及脚本原有第三方依赖
"""
import base64
import json
import re
import sys
import urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token  # noqa: E402

REPO, BRANCH = 'kai-cn/car-monit-backend', 'car-monit-backend-jdk25'
H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'forest-resource-fix'}
FILES = [
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/base/service/impl/RoadPathImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/base/service/consistency/DataConsistencyService.java',
 'ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java',
 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java',
 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java',
]
FIELD = re.compile(r'\b(?:Http\w+Service|\w+Api)\b')
IMPORT = 'import org.springframework.beans.factory.annotation.Autowired;\n'


def api(uri, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(uri, data=data, headers=H, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

for rel in FILES:
    obj = api(f'https://api.github.com/repos/{REPO}/contents/{rel}?ref={BRANCH}')
    lines = base64.b64decode(obj['content']).decode('utf-8').split('\n')
    changed = 0
    for i, line in enumerate(lines):
        if not FIELD.search(line):
            continue
        for j in range(i - 1, max(-1, i - 7), -1):
            st = lines[j].strip()
            if st.startswith('@Autowired') or st == '@Resource':
                indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
                if st != '@Autowired(required = false)':
                    lines[j] = indent + '@Autowired(required = false)'
                    changed += 1
                break
    text = '\n'.join(lines)
    if IMPORT not in text and '@Autowired(required = false)' in text:
        idx = next((i for i, l in enumerate(lines) if l.startswith('package ')), -1) + 1
        lines.insert(idx, IMPORT)
        text = '\n'.join(lines)
        changed += 1
    if changed == 0:
        continue
    api(f'https://api.github.com/repos/{REPO}/contents/{rel}', 'PUT', {
        'message': 'fix(native): all Forest fields optional with Autowired import',
        'content': base64.b64encode(text.encode()).decode(), 'sha': obj['sha'], 'branch': BRANCH})
    print('FIXED', rel, changed)
