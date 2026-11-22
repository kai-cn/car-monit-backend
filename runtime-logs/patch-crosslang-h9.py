#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-h9.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-crosslang-h9.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')

t = p.read_text(encoding='utf-8')



# 1. Java8 baseline uses p6spy driver, so the URL must carry the p6spy scheme.

old = 'SPRING__DATASOURCE__DRUID__MASTER__URL: jdbc:mysql://127.0.0.1:3306/carmonitdb?'

new = 'SPRING__DATASOURCE__DRUID__MASTER__URL: jdbc:p6spy:mysql://127.0.0.1:3306/carmonitdb?'

assert old in t, 'baseline URL not found'

t = t.replace(old, new, 1)



# 2. Pin Python 3.12 for the candidates job (3.14 breaks pydantic-core/PyO3).

marker = '  candidates:\n'

idx = t.index(marker)

head, tail = t[:idx], t[idx:]

needle = '      - uses: actions/checkout@v4\n'

pos = tail.index(needle) + len(needle)

setup = '''      - name: Setup Python 3.12

        if: steps.gate.outputs.run == 'yes' && matrix.lang == 'python'

        uses: actions/setup-python@v5

        with:

          python-version: '3.12'

'''

tail = tail[:pos] + setup + tail[pos:]

t = head + tail



# 3. Print full app-log tails for baseline and candidate on compare.

cmp_marker = '      - name: Compare vs Java8\n'

idx = t.index(cmp_marker)

head, tail = t[:idx], t[idx:]

needle = '          set -uo pipefail\n'

pos = tail.index(needle) + len(needle)

logs = '''          for f in out/java8.json.app.log "out/${{ matrix.lang }}.json.app.log"; do

            if [ -f "$f" ]; then

              echo "::group::tail $f"

              tail -n 120 "$f" || true

              echo "::endgroup::"

            fi

          done

'''

tail = tail[:pos] + logs + tail[pos:]

t = head + tail



p.write_text(t, encoding='utf-8')

print('patched baseline+pythonsetup+logs', 'p6spy:mysql' in t, "python-version: '3.12'" in t, 'json.app.log' in t)

