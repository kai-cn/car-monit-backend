#!/usr/bin/env python3
"""修复 Redis/Lettuce 迁移后不可达的 IOException catch。

背景：部分业务逻辑改用 java.util.Base64 / Lettuce 后，try 块不再声明 IOException，
javac 报 "exception java.io.IOException is never thrown"。

思路：
1. 只处理 api__car-monit-api-java-fix 工作树。
2. 把 catch (IOException e) 改为 catch (Exception e)，保持错误日志语义且可通过编译。
3. 本地 commit + push，然后只需重跑该分支。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade\api__car-monit-api-java-fix')
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

def git(*args,timeout=240):
    r=subprocess.run(['git','-C',str(ROOT),*args],capture_output=True,text=True,
                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)
    if r.returncode!=0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()

changed=[]
for p in ROOT.rglob('*.java'):
    t=p.read_text(encoding='utf-8')
    n=t.replace('catch (IOException e)','catch (Exception e)')
    if n!=t:
        p.write_text(n,encoding='utf-8')
        changed.append(str(p.relative_to(ROOT)))
if not changed:
    print('NOCHANGE'); raise SystemExit
git('add','-A')
git('commit','-m','fix(java): make legacy IOException catches reachable')
git('push','origin','HEAD:car-monit-api-java-fix')
print('PUSHED',','.join(changed))
