#!/usr/bin/env python3
"""Push backend master, then reconcile and push api master."""
import os
import subprocess
from pathlib import Path
env=dict(os.environ); env['GIT_ASKPASS']='/home/dev/tools/git-askpass.sh'; env['GIT_TERMINAL_PROMPT']='0'
B=Path('/home/dev/IdeaProjects/car-monit-backend')
A=Path('/home/dev/IdeaProjects/car-monit-api')
subprocess.run(['git','-C',str(B),'push','origin','HEAD:master'],check=True,env=env)
print('PUSHED_BACKEND',subprocess.check_output(['git','-C',str(B),'rev-parse','--short','HEAD'],text=True).strip())

# api: fetch and compare; local work is uncommitted, so reset working files onto remote while preserving final docs via reapply.
subprocess.run(['git','-C',str(A),'fetch','origin','master'],check=True,env=env)
print('API_LOCAL',subprocess.check_output(['git','-C',str(A),'rev-parse','--short','HEAD'],text=True).strip())
print('API_REMOTE',subprocess.check_output(['git','-C',str(A),'rev-parse','--short','origin/master'],text=True).strip())
