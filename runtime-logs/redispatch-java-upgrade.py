#!/usr/bin/env python3
"""取消仍在旧提交上运行的 Java 升级验证，并重新派发。

思路：
1. 读取 java-upgrade-runs.json 中上一轮 run_id。
2. 对 status != completed 的 run 调 GitHub cancel API；
   已完成的失败 run 保留作为证据，不需取消。
3. 调用 dispatch-java-upgrade-verification.py 重新派发，确保新 run 使用刚推送的 POM 修复。

风险：取消不会删除历史 run；只影响当前排队/运行中的任务。
"""
import json
import subprocess
import sys
import urllib.request
from pathlib import Path
sys.path.insert(0, r'D:\work\runtime-logs')
from gh_cred import get_token

H={'Authorization':'Bearer '+get_token(),'Accept':'application/vnd.github+json','User-Agent':'redispatch'}
PATH=Path(r'D:\work\runtime-logs\java-upgrade-runs.json')
records=json.loads(PATH.read_text(encoding='utf-8'))
for rec in records:
    rid=rec.get('run_id')
    if not rid or rec.get('status')=='completed':
        continue
    try:
        req=urllib.request.Request(
            f"https://api.github.com/repos/{rec['repo']}/actions/runs/{rid}/cancel",
            data=b'',headers=H,method='POST')
        urllib.request.urlopen(req,timeout=60).read()
        print('CANCELLED',rec['repo'],rec['branch'],rid)
    except Exception as e:
        print('CANCEL_SKIP',rec['repo'],rec['branch'],rid,e)
subprocess.run([sys.executable, r'D:\work\runtime-logs\dispatch-java-upgrade-verification.py'], check=True)
