#!/usr/bin/env python3
"""把 sun.misc.BASE64Decoder 替换为 java.util.Base64，兼容 JDK25。

思路：
1. sun.misc.BASE64Decoder 在 JDK25 已移除，编译报 cannot find symbol。
2. java.util.Base64.getDecoder().decode() 是标准替代，行为一致。
3. 原代码 catch IOException；新 decode 抛 IllegalArgumentException，同步调整。
4. 只修改 backend 工作树中的 Base64DecodeMultipartFile.java，本地 commit + push。
"""
import os
import subprocess
from pathlib import Path

ROOT=Path(r'D:\work\IdeaProjects\_pom-upgrade')
REL='ruoyi-admin/src/main/java/com/ruoyi/web/util/Base64DecodeMultipartFile.java'
ENV=dict(os.environ,GIT_TERMINAL_PROMPT='0')

def git(wd,*args,timeout=240):
    r=subprocess.run(['git','-C',str(wd),*args],capture_output=True,text=True,
                     encoding='utf-8',errors='replace',env=ENV,timeout=timeout)
    if r.returncode!=0:
        raise RuntimeError(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.strip()

for wd in sorted(ROOT.iterdir()):
    if not wd.is_dir() or not wd.name.startswith('bk__'):
        continue
    p=wd/REL
    if not p.exists() or 'BASE64Decoder' not in p.read_text(encoding='utf-8'):
        continue
    t=p.read_text(encoding='utf-8')
    n=t.replace('import sun.misc.BASE64Decoder;','import java.util.Base64;')
    n=n.replace('''        BASE64Decoder decoder = new BASE64Decoder();
        byte[] b = new byte[0];
        try {
            b = decoder.decodeBuffer(baseStrs[1]);
        } catch (IOException e) {
            e.printStackTrace();
        }
''','''        byte[] b = new byte[0];
        try {
            b = Base64.getDecoder().decode(baseStrs[1]);
        } catch (IllegalArgumentException e) {
            e.printStackTrace();
        }
''')
    if n==t:
        print('NOCHANGE',wd.name); continue
    p.write_text(n,encoding='utf-8')
    branch=wd.name.split('__',1)[1].replace('_','/')
    git(wd,'add','-A')
    git(wd,'commit','-m','fix(jdk25): replace sun.misc BASE64Decoder')
    git(wd,'push','origin','HEAD:'+branch)
    print('PUSHED',branch)
