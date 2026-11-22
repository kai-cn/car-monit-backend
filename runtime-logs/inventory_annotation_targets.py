#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Operational helper created during the native/CICD verification session.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""List unique workflow/script files across active branches' REMOTE refs (by content hash)."""
import subprocess, hashlib, collections, os

REPOS = {
    'api': dict(repo=r'D:\work\IdeaProjects\car-monit-api-java-V3',
                branches=['car-monit-api-java-V3','car-monit-api-jdk17','car-monit-api-jdk21','car-monit-api-jdk25','master']),
    'backend': dict(repo=r'D:\work\IdeaProjects\car-monit-backend-java-V3',
                    branches=['car-monit-backend-java-V3','car-monit-backend-jdk17','car-monit-backend-jdk21','car-monit-backend-jdk25','master']),
}

def git(repo, *a):
    return subprocess.run(['git','-C',repo,*a], capture_output=True)

def list_tree(repo, ref, prefix):
    p = git(repo,'ls-tree','-r','--name-only',ref,'--',prefix).stdout.decode('utf-8','replace')
    return [l for l in p.splitlines() if l.strip()]

def blob(repo, ref, path):
    return git(repo,'show',f'{ref}:{path}').stdout

for key, cfg in REPOS.items():
    repo = cfg['repo']
    print(f'################ {key} ################')
    wf_by_hash = collections.defaultdict(list)   # (hash,path) -> [branches]
    sc_by_hash = collections.defaultdict(list)
    for br in cfg['branches']:
        ref = 'refs/remotes/origin/'+br
        for path in list_tree(repo, ref, '.github/workflows'):
            if path.endswith(('.yml','.yaml')):
                h = hashlib.md5(blob(repo,ref,path)).hexdigest()[:8]
                wf_by_hash[(h,path)].append(br)
        for path in list_tree(repo, ref, 'scripts'):
            if path.endswith(('.sh','.py','.ps1')):
                h = hashlib.md5(blob(repo,ref,path)).hexdigest()[:8]
                sc_by_hash[(h,path)].append(br)
    print(f'=== unique workflows: {len(wf_by_hash)}')
    for (h,p),brs in sorted(wf_by_hash.items(), key=lambda x:(x[0][1],x[0][0])):
        print(f'  {p} {h} [{",".join(brs)}]')
    print(f'=== unique scripts: {len(sc_by_hash)}')
    for (h,p),brs in sorted(sc_by_hash.items(), key=lambda x:(x[0][1],x[0][0])):
        print(f'  {p} {h} [{",".join(brs)}]')
