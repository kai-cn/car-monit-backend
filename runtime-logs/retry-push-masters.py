#!/usr/bin/env python3
"""Retry pushing WSL master commits with askpass."""
import os
import subprocess
from pathlib import Path
env=dict(os.environ); env['GIT_ASKPASS']='/home/dev/tools/git-askpass.sh'; env['GIT_TERMINAL_PROMPT']='0'
for name in ['car-monit-backend','car-monit-api']:
 repo=Path('/home/dev/IdeaProjects')/name
 print('===',name,'===')
 print(subprocess.check_output(['git','-C',str(repo),'log','-2','--oneline'],text=True))
 subprocess.run(['git','-C',str(repo),'push','origin','HEAD:master'],check=True,env=env)
 print('PUSHED',name,subprocess.check_output(['git','-C',str(repo),'rev-parse','--short','HEAD'],text=True).strip())
