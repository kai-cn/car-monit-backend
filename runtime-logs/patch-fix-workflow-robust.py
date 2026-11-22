#!/usr/bin/env python3

"""
@description 历史脚本 patch-fix-workflow-robust.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-fix-workflow-robust.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

