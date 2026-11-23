#!/usr/bin/env python3
"""Commit and push staged api master changes."""
import os
import subprocess
from pathlib import Path
A=Path('/home/dev/IdeaProjects/car-monit-api')
env=dict(os.environ); env['GIT_ASKPASS']='/home/dev/tools/git-askpass.sh'; env['GIT_TERMINAL_PROMPT']='0'
r=subprocess.run(['git','-C',str(A),'diff','--cached','--quiet'])
if r.returncode:
    subprocess.run(['git','-C',str(A),'-c','user.name=Tencent Hunyuan Hy','-c','user.email=ai@example.local','commit','-m','fix(parity): keep SQL ES compatibility and final docs'],check=True,env=env)
subprocess.run(['git','-C',str(A),'push','origin','HEAD:master'],check=True,env=env)
print('PUSHED',subprocess.check_output(['git','-C',str(A),'rev-parse','--short','HEAD'],text=True).strip())
