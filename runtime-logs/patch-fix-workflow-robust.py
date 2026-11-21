#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-fix-workflow-robust.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path
p = Path(r'D:\work\runtime-logs\fix-all-invalid-workflows.py')
t = p.read_text(encoding='utf-8')
t = t.replace("""    for br in branches(repo):
        for p in paths(repo, br):
            text, _ = fetch_put(repo, br, p)
            new, changed = fix(text)
            if changed:
                fetch_put(repo, br, p, new)
                print('FIX', br, p)
                fixed += 1
""", """    for br in branches(repo):
        try:
            wpaths = paths(repo, br)
        except Exception as e:
            print('LIST_FAIL', br, e)
            continue
        for p in wpaths:
            try:
                text, _ = fetch_put(repo, br, p)
            except Exception as e:
                print('FETCH_FAIL', br, p, e)
                continue
            new, changed = fix(text)
            if changed:
                try:
                    fetch_put(repo, br, p, new)
                    print('FIX', br, p)
                    fixed += 1
                except Exception as e:
                    print('PUT_FAIL', br, p, e)
""")
p.write_text(t, encoding='utf-8')
print('patched robust')
