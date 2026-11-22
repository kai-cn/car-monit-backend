#!/usr/bin/env python3
"""
@description 从环境变量读取管理员凭据并以 GitHub SealedBox 加密写入两仓库 Secrets，明文不落盘、不回显。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage CARMONIT_ADMIN_USER=admin CARMONIT_ADMIN_PASSWORD=... python runtime-logs/set-admin-secrets.py
@dependencies PyNaCl；本地缓存 GitHub token；两仓库管理员权限。
"""
import base64
import json
import os
import sys
import urllib.request

from nacl.public import PublicKey, SealedBox

sys.path.insert(0, r'D:\work\IdeaProjects\car-monit-backend-new\runtime-logs')
from gh_cred import get_token

H = {'Authorization': 'Bearer ' + get_token(), 'Accept': 'application/vnd.github+json',
     'User-Agent': 'set-admin-secrets'}
REPOS = ['kai-cn/car-monit-backend', 'kai-cn/car-monit-api']


def api(url, method='GET', body=None):
    """调用 GitHub Secrets API；只返回状态码和必要错误摘要。"""
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=H, method=method), timeout=60) as r:
        text = r.read().decode()
        return r.status, (json.loads(text) if text.strip() else {})


def set_secret(repo, name, value):
    """使用仓库 public key 加密单个 secret；成功只打印名称。"""
    status, key = api(f'https://api.github.com/repos/{repo}/actions/secrets/public-key')
    pk = PublicKey(base64.b64decode(key['key']))
    enc = base64.b64encode(SealedBox(pk).encrypt(value.encode())).decode()
    api(f'https://api.github.com/repos/{repo}/actions/secrets/{name}', 'PUT',
        {'encrypted_value': enc, 'key_id': key['key_id']})
    print('SET', repo, name)


def main():
    """校验环境变量后批量写入 CI_ADMIN_USER/CI_ADMIN_PASSWORD。"""
    user = os.environ.get('CARMONIT_ADMIN_USER', '')
    password = os.environ.get('CARMONIT_ADMIN_PASSWORD', '')
    if not user or not password:
        raise SystemExit('Missing CARMONIT_ADMIN_USER/CARMONIT_ADMIN_PASSWORD')
    for repo in REPOS:
        set_secret(repo, 'CI_ADMIN_USER', user)
        set_secret(repo, 'CI_ADMIN_PASSWORD', password)


if __name__ == '__main__':
    main()
