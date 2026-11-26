#!/usr/bin/env python3

"""
@description 历史脚本 fix-all-invalid-workflows.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python fix-all-invalid-workflows.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies GitHub API 访问凭据（从本地缓存读取，不落盘）；Maven 与对应 JDK；Python 3 标准库及脚本原有第三方依赖

Pattern found by scan-all-workflows.py:


        uses: actions/setup-java@v4


          # Perf: ...


          cache: maven


        with:


          distribution: temurin





The option must be a child of `with:`, so move it after the `with:` line.
"""
import base64

import json

import sys

import urllib.request

from pathlib import Path



sys.path.insert(0, r'D:\work\runtime-logs')

from gh_cred import get_token  # noqa: E402



TOKEN = get_token()

HEADERS = {'Authorization': 'Bearer ' + TOKEN,

           'Accept': 'application/vnd.github+json',

           'X-GitHub-Api-Version': '2022-11-28',

           'User-Agent': 'workflow-fix'}

REPOS = ('kai-cn/car-monit-api', 'kai-cn/car-monit-backend')





def api(uri):

    req = urllib.request.Request(uri, headers=HEADERS)

    with urllib.request.urlopen(req, timeout=60) as r:

        return json.loads(r.read().decode('utf-8'))





def branches(repo):

    out, page = [], 1

    while True:

        data = api(f'https://api.github.com/repos/{repo}/branches?per_page=100&page={page}')

        if not data:

            break

        out += [b['name'] for b in data]

        if len(data) < 100:

            break

        page += 1

    return out





def paths(repo, br):

    enc = br.replace('/', '%2F')

    return [i['path'] for i in api(f'https://api.github.com/repos/{repo}/contents/.github/workflows?ref={enc}')

            if i['path'].endswith(('.yml', '.yaml'))]





def fetch_put(repo, br, p, new_text=None):

    enc = br.replace('/', '%2F')

    uri = f'https://api.github.com/repos/{repo}/contents/{p}?ref={enc}'

    obj = api(uri)

    if new_text is None:

        return base64.b64decode(obj['content']).decode('utf-8', errors='replace'), obj['sha']

    body = {

        'message': 'ci(fix): move Maven cache option inside with: block',

        'content': base64.b64encode(new_text.encode('utf-8')).decode('ascii'),

        'sha': obj['sha'],

        'branch': br,

    }

    req = urllib.request.Request(f'https://api.github.com/repos/{repo}/contents/{p}',

                                 data=json.dumps(body).encode('utf-8'), headers=HEADERS, method='PUT')

    with urllib.request.urlopen(req, timeout=60) as r:

        return json.loads(r.read().decode('utf-8')), None





def fix(text):

    lines = text.split('\n')

    out = []

    i = 0

    changed = False

    while i < len(lines):

        line = lines[i]

        if line.strip() == 'cache: maven':

            indent = line[:len(line) - len(line.lstrip())]

            # locate a sibling `with:` within the next 3 lines

            j, with_idx = i + 1, -1

            while j < min(i + 4, len(lines)):

                s = lines[j]

                ind = s[:len(s) - len(s.lstrip())]

                if s.strip() == 'with:' and len(ind) == len(indent) - 2:

                    with_idx = j

                    break

                j += 1

            if with_idx >= 0:

                # drop preceding # Perf comment(s) that belong to this cache line

                while out and out[-1].strip().startswith('#') and \
                        len(out[-1]) - len(out[-1].lstrip()) > len(indent) - 2:

                    out.pop()

                # copy lines between i+1 and with_idx unchanged

                for k in range(i + 1, with_idx):

                    out.append(lines[k])

                out.append(lines[with_idx])

                child = ' ' * len(indent) + 'cache: maven'

                out.append(child)

                out.extend(lines[with_idx + 1:])

                return '\n'.join(out), True

        out.append(line)

        i += 1

    return text, False





fixed = 0

for repo in REPOS:

    print('REPO', repo)

    for br in branches(repo):

        try:

            wpaths = paths(repo, br)

        except Exception as e:

            print('LIST_FAIL', br, e)

            continue

        for p in wpaths:

            try:

                text, _ = fetch_put(repo, br, p)

            except Exception as e:

                print('FETCH_FAIL', br, p, e)

                continue

            new, changed = fix(text)

            if changed:

                try:

                    fetch_put(repo, br, p, new)

                    print('FIX', br, p)

                    fixed += 1

                except Exception as e:

                    print('PUT_FAIL', br, p, e)

print('FIXED', fixed)

