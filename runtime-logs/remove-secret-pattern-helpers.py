#!/usr/bin/env python3
"""Remove one-off helper scripts that contain secret pattern literals."""
from pathlib import Path
B=Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs')
for name in ['sanitize-all-history-secrets.py','patch-wsl-master-fixes5.py']:
 p=B/name
 if p.exists():
  p.unlink()
  print('REMOVED',p)
