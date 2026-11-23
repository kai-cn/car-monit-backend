#!/usr/bin/env python3
"""Repoint api local commit to remote master while preserving worktree.

@description 使用 soft reset 将 api HEAD 对齐 origin/master，保留工作树，然后展示相对远端的真实差异。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/rebase-api-soft.py
@dependencies WSL api master。
"""
import subprocess
from pathlib import Path
A=Path('/home/dev/IdeaProjects/car-monit-api')
subprocess.run(['git','-C',str(A),'reset','--soft','origin/master'],check=True)
subprocess.run(['git','-C',str(A),'reset'],check=True)
print('HEAD',subprocess.check_output(['git','-C',str(A),'rev-parse','--short','HEAD'],text=True).strip())
out=subprocess.run(['git','-C',str(A),'status','--short'],text=True,capture_output=True).stdout
print(out[:5000])
