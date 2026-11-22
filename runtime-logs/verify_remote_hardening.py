#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Read-only verification of a security or build invariant.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
"""Verify security invariants directly against fetched remote-tracking refs."""
import re, subprocess

REPOS = {'api': r'D:\work\IdeaProjects\car-monit-api-java-V3',
         'backend': r'D:\work\IdeaProjects\car-monit-backend-java-V3'}

def git(repo,*a):
    return subprocess.run(['git','-C',repo,*a],capture_output=True,text=True,
                          encoding='utf-8',errors='replace').stdout

problems=[]
for rn,repo in REPOS.items():
    refs=[b.strip() for b in git(repo,'for-each-ref','--format=%(refname)','refs/remotes/origin').splitlines()
          if b.strip().endswith(('/HEAD',)) is False and 'refs/remotes/origin/' in b]
    for ref in refs:
        files=[f.strip() for f in git(repo,'ls-tree','-r','--name-only',ref,'.github/workflows/').splitlines()
               if f.strip().endswith(('.yml','.yaml'))]
        for f in files:
            c=git(repo,'show',f'{ref}:{f}')
            bn=f.split('/')[-1]
            # Invariant 1: no `push` trigger inside self-hosted-ci.yml
            if bn=='self-hosted-ci.yml' and re.search(r'^  push:', c, re.M):
                problems.append((rn,ref,f,'self-hosted-ci still has push trigger'))
            # Invariant 2: no CI_RUNNER_LABELS/JSON dynamic runner switching
            if 'CI_RUNNER_LABELS' in c or 'CI_RUNNER_JSON' in c:
                problems.append((rn,ref,f,'dynamic runner var still present'))
            # Invariant 3: any self-hosted runs-on job must have an owner guard
            has_selfhost_run = re.search(r'runs-on:.*(self-hosted|inputs\.runner_label)', c) is not None
            if has_selfhost_run and "github.repository_owner == 'kai-cn'" not in c:
                problems.append((rn,ref,f,'self-hosted runner without owner guard'))
            # Invariant 4: native-image-cloud must not offer self-hosted option
            if bn=='native-image-cloud.yml' and 'options: [cloud, self-hosted]' in c:
                problems.append((rn,ref,f,'native-cloud still offers self-hosted'))
            # Invariant 5: no pull_request_target
            if 'pull_request_target' in c:
                problems.append((rn,ref,f,'pull_request_target present'))

if problems:
    print('FAIL - %d problems:'%len(problems))
    for p in problems: print('  ',p[0],p[1].replace('refs/remotes/origin/',''),p[2],'::',p[3])
else:
    print('PASS - all security invariants hold across all branches/workflows')
