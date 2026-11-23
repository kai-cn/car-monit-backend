#!/usr/bin/env python3
"""Inspect WSL merge conflict state."""
from pathlib import Path
import subprocess
for name in ['car-monit-backend','car-monit-api']:
 repo=Path('/home/dev/IdeaProjects')/name
 print('===',name,'===')
 print(subprocess.run(['git','-C',str(repo),'status','--short'],text=True,capture_output=True).stdout[:4000])
 print('MERGE_HEAD',subprocess.run(['git','-C',str(repo),'rev-parse','--verify','MERGE_HEAD'],text=True,capture_output=True).stdout.strip())
