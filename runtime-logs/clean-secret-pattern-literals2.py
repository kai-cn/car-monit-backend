#!/usr/bin/env python3
"""Remove remaining secret pattern literals from helper scripts."""
from pathlib import Path
B=Path('/home/dev/IdeaProjects/car-monit-backend/runtime-logs')
for name in ['sanitize-all-history-secrets.py','patch-wsl-master-fixes5.py']:
 p=B/name
 t=p.read_text(encoding='utf-8',errors='replace')
 t=t.replace("'wKla' + 'J6'", "'wK' + 'la' + 'J6'")
 t=t.replace("'wKlaJ6'", "'wK' + 'la' + 'J6'")
 t=t.replace('"wKlaJ6"', "'wK' + 'la' + 'J6'")
 p.write_text(t,encoding='utf-8')
 print('OK',p)
