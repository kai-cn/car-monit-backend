#!/usr/bin/env python3
# Operational helper — native/CICD verification session (2026-11-16~17).
# Purpose: Apply a targeted configuration/source patch produced during the native/CICD investigation.
# Risk: may call GitHub API or modify local/remote files; inspect before running.
from pathlib import Path
p = Path(r'D:\work\runtime-logs\api-boot3-workflow.yml')
t = p.read_text(encoding='utf-8')
needle = '''      - name: Compare + report
        shell: bash
        run: |
          set -uo pipefail
'''
add = needle + '''          for f in out/jar.json.app.log out/native.json.app.log; do
            if [ -f "$f" ]; then
              echo "::group::tail $f"
              tail -n 80 "$f" || true
              echo "::endgroup::"
            fi
          done
'''
if 'tail -n 80 "$f"' not in t:
    t = t.replace(needle, add, 1)
p.write_text(t, encoding='utf-8')
print('patched', 'tail -n 80' in t)
