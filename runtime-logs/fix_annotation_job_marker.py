#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Repair a concrete failure found in cloud/local logs; see session handoff for the observed error.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""精准修正：删除误把触发器标成 job 的注释行（'  # ── job: workflow_dispatch ──' 等）。
基于远端 ref + git plumbing 写回，不重复加注释、不碰 worktree。支持 --apply。"""
import subprocess, os, tempfile, sys
APPLY = '--apply' in sys.argv
REPOS = {
    'api': dict(repo=r'D:\work\IdeaProjects\car-monit-api-java-V3',
                branches=['car-monit-api-java-V3','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','master']),
    'backend': dict(repo=r'D:\work\IdeaProjects\car-monit-backend-java-V3',
                    branches=['car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','master']),
}
TRIGGERS = ('workflow_dispatch','push','pull_request','workflow_call','schedule','release','workflow_run')

def git(repo,*a,input=None):
    kw=dict(capture_output=True)
    if input is not None: kw['input']=input
    return subprocess.run(['git','-C',repo,*a],**kw)

for key,cfg in REPOS.items():
    repo=cfg['repo']
    for br in cfg['branches']:
        ref='refs/remotes/origin/'+br
        base=git(repo,'rev-parse',ref).stdout.decode().strip()
        files=git(repo,'ls-tree','-r','--name-only',ref,'--','.github/workflows').stdout.decode().split()
        changed=[]
        for f in files:
            if not f.endswith(('.yml','.yaml')): continue
            data=git(repo,'show',f'{ref}:{f}').stdout
            bom=data.startswith(b'\xef\xbb\xbf')
            text=data.decode('utf-8-sig','replace')
            lines=text.split('\n')
            kept=[]
            removed=0
            for line in lines:
                if any(line.strip()==f'# ── job: {t} ──' for t in TRIGGERS) and line.startswith('  # ── job:'):
                    removed+=1; continue
                kept.append(line)
            if removed:
                out='\n'.join(kept)
                new=(b'\xef\xbb\xbf' if bom else b'')+out.encode('utf-8')
                changed.append((f,new,removed))
        print(f'{br}: {len(changed)} files to fix')
        if APPLY and changed:
            idx=os.path.join(tempfile.gettempdir(),f'fixann_{os.getpid()}_{abs(hash(br))}.idx')
            env=os.environ.copy(); env['GIT_INDEX_FILE']=idx
            subprocess.run(['git','-C',repo,'read-tree',base],env=env,capture_output=True,check=True)
            for f,new,n in changed:
                bh=git(repo,'hash-object','-w','--stdin',input=new).stdout.decode().strip()
                old=git(repo,'ls-tree',base,'--',f).stdout.decode().split()
                mode=old[0] if old else '100644'
                subprocess.run(['git','-C',repo,'update-index','--add','--cacheinfo',f'{mode},{bh},{f}'],env=env,capture_output=True,check=True)
            tree=subprocess.run(['git','-C',repo,'write-tree'],env=env,capture_output=True,text=True,check=True).stdout.strip()
            os.remove(idx)
            c=git(repo,'commit-tree',tree,'-p',base,'-m','docs(ci): 修正注释中把触发器误标为 job 的行')
            sha=c.stdout.decode().strip()
            if c.returncode: print('  ERR',c.stderr.decode()); continue
            git(repo,'update-ref',ref,sha)
            print(f'  committed {sha[:7]}')
