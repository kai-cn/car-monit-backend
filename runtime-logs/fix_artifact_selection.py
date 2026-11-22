#!/usr/bin/env python3

"""
@description 历史脚本 fix_artifact_selection.py：修复本地或云端验证中暴露的问题；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python fix_artifact_selection.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
# Operational helper — native/CICD verification session (2026-11-16~17).

# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.

# Risk: may call GitHub API or modify local/remote files; inspect before running.

"""Fix native-image-cloud.yml binary selection: pick the real native executable by module name, not first -perm -u+x file."""

import sys

sys.path.insert(0, r'D:\work\runtime-logs')

exec(open(r'D:\work\runtime-logs\harden_workflows.py', encoding='utf-8').read().split('def main()')[0])

import os



import re

OLD_LINUX_RE = re.compile(r'(?P<i>^[ ]+)bin=\$\(find "\$mod/target" -maxdepth 1 -type f -perm -u\+x ![ ]-name \'\*\.jar\' ![ ]-name \'\*\.exe\' -print -quit\)\n(?P=i)ext=bin', re.M)

NEW_LINUX_TPL = '''{i}# native-image 产物名 = artifactId（pro-business-api / ruoyi-admin），不要用

{i}# -perm -u+x -print -quit（会先命中 target 下的 libjvm.so 等 9KB shim）。

{i}bin="$mod/target/$mod"

{i}if [ ! -f "$bin" ] || [ ! -x "$bin" ]; then

{i}  echo "NATIVE BINARY NOT FOUND at $bin"

{i}  find "$mod/target" -maxdepth 1 -type f -printf '%f %s bytes\\n' | sort

{i}  exit 1

{i}fi

{i}ext=bin'''



OLD_WIN_RE = re.compile(r'(?P<i>^[ ]+)bin=\$\(find "\$mod/target" -maxdepth 1 -type f -name \'\*\.exe\' -print -quit\)\n(?P=i)ext=exe', re.M)

NEW_WIN_TPL = '''{i}bin="$mod/target/$mod.exe"

{i}if [ ! -f "$bin" ]; then

{i}  echo "NATIVE EXE NOT FOUND at $bin"

{i}  find "$mod/target" -maxdepth 1 -type f -name '*.exe' -printf '%f %s bytes\\n'

{i}  exit 1

{i}fi

{i}ext=exe'''



def fix(text):

    changed = False

    m = OLD_LINUX_RE.search(text)

    if m:

        text = OLD_LINUX_RE.sub(lambda mm: NEW_LINUX_TPL.format(i=mm.group('i')), text, count=1); changed = True

    m = OLD_WIN_RE.search(text)

    if m:

        text = OLD_WIN_RE.sub(lambda mm: NEW_WIN_TPL.format(i=mm.group('i')), text, count=1); changed = True

    # add a size sanity gate after binary_bytes echo

    if 'binary_bytes=$bytes sha256=$sha' in text and 'MIN_NATIVE_BYTES' not in text:

        text = text.replace(

            'echo "binary_bytes=$bytes sha256=$sha"',

            'echo "binary_bytes=$bytes sha256=$sha"\n'

            '          MIN_NATIVE_BYTES=10000000  # 真 native 二进制应 >10MB；9KB 必为误选\n'

            '          if [ "$bytes" -lt "$MIN_NATIVE_BYTES" ]; then\n'

            '            echo "::error::native binary too small ($bytes bytes) - wrong file selected"\n'

            '            exit 1\n'

            '          fi')

        changed = True

    return text, changed



# dry-run then apply

apply = '--apply' in sys.argv

for rn, repo in REPOS.items():

    print('====', rn)

    for br in branches(repo):

        f = '.github/workflows/native-image-cloud.yml'

        c = show(repo, br, f)

        if c is None:

            continue

        new, ch = fix(c)

        if not ch:

            continue

        short = br.replace('refs/remotes/origin/','')

        print('  ', short, 'changed')

        if apply:

            import yaml

            yaml.safe_load(new)

            base = git(repo,'rev-parse',br).stdout.strip()

            h = git(repo,'hash-object','-w','--stdin',input=new).stdout.strip()

            ti = os.path.join(os.environ.get('TEMP','/tmp'), f'fixart_{os.getpid()}_{abs(hash(br))}.idx')

            env = __import__('os').environ.copy(); env['GIT_INDEX_FILE']=ti

            __import__('subprocess').run(['git','-C',repo,'read-tree',base],env=env,capture_output=True,check=True)

            mode = git(repo,'ls-tree',base,'--',f).stdout.split()[0]

            __import__('subprocess').run(['git','-C',repo,'update-index','--add','--cacheinfo',f'{mode},{h},{f}'],env=env,capture_output=True,check=True)

            tree = __import__('subprocess').run(['git','-C',repo,'write-tree'],env=env,capture_output=True,text=True,check=True).stdout.strip()

            os.remove(ti)

            cm = git(repo,'commit-tree',tree,'-p',base,'-m','ci(native): select real native binary by module name + size gate')

            if cm.returncode: print('    COMMIT ERR',cm.stderr); continue

            sha=cm.stdout.strip()

            git(repo,'update-ref',br,sha)

            print('    COMMITTED',sha[:7])

