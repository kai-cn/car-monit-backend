#!/usr/bin/env python3
import base64
import json
import sys
import urllib.request

sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token  # noqa: E402

REPO, BRANCH = 'kai-cn/car-monit-backend', 'car-monit-backend-jdk25'
H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'forest-import-fix'}
FILES = [
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarTrackInfoServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarSuspiciousServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/manager/service/impl/CarInfoServiceImpl.java',
 'ruoyi-system/src/main/java/com/ruoyi/base/service/consistency/DataConsistencyService.java',
 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/VehicleMonitoringTask.java',
 'ruoyi-quartz/src/main/java/com/ruoyi/quartz/task/SnapshotFlowSyncTask.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager/CarTrackInfoController.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsRtSzdnSnapshotFlowAddcodeController.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeStationExit01Controller.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeRecords01Controller.java',
 'ruoyi-admin/src/main/java/com/ruoyi/web/controller/base/OdsLwzxsfsjFeeGantryFusion01Controller.java',
]
IMPORT = 'import org.springframework.beans.factory.annotation.Autowired;\n'


def api(uri, method='GET', body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(uri, data=data, headers=H, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

for rel in FILES:
    obj = api(f'https://api.github.com/repos/{REPO}/contents/{rel}?ref={BRANCH}')
    text = base64.b64decode(obj['content']).decode('utf-8')
    if IMPORT in text or '@Autowired' not in text:
        continue
    lines = text.split('\n')
    idx = next((i for i, l in enumerate(lines) if l.startswith('package ')), -1) + 1
    lines.insert(idx, IMPORT)
    new = '\n'.join(lines)
    api(f'https://api.github.com/repos/{REPO}/contents/{rel}', 'PUT', {
        'message': 'fix(native): add Autowired import for optional Forest beans',
        'content': base64.b64encode(new.encode()).decode(), 'sha': obj['sha'], 'branch': BRANCH})
    print('IMPORT_ADDED', rel)
