#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-h9b.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-crosslang-h9b.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\crosslang-fix.yml')

t = p.read_text(encoding='utf-8')



# Java8 baseline: avoid p6spy driver entirely; use direct MySQL driver.

t = t.replace('SPRING__DATASOURCE__DRUID__MASTER__URL: jdbc:p6spy:mysql://127.0.0.1:3306/carmonitdb?',

              'SPRING__DATASOURCE__DRUID__MASTER__URL: jdbc:mysql://127.0.0.1:3306/carmonitdb?', 1)

needle = '          SPRING__DATASOURCE__DRUID__MASTER__PASSWORD: root\n'

if 'SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME' not in t:

    t = t.replace(needle, needle + '          SPRING__DATASOURCE__DRUID__MASTER__DRIVERCLASSNAME: com.mysql.cj.jdbc.Driver\n', 1)



# Baseline job: dump app log tail right after probe.

marker = '      # 上传产物供后续 job/Release 使用\n'

log_step = '''      - name: Dump baseline app log

        if: always()

        shell: bash

        run: |

          if [ -f out/java8.json.app.log ]; then

            tail -n 160 out/java8.json.app.log || true

          fi

'''

if 'Dump baseline app log' not in t:

    t = t.replace(marker, log_step + marker, 1)



# Rust: smaller pool so the cloud MySQL accepts all connections promptly.

rust_sed = "          sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' car-monit-rust/config/application.yaml\n"

extra_sed = "          sed -i 's/minIdle: 10/minIdle: 0/; s/maxActive: 200/maxActive: 10/; s/maxWait: 60000/maxWait: 30000/' car-monit-rust/config/application.yaml\n"

if extra_sed not in t:

    t = t.replace(rust_sed, rust_sed + extra_sed, 1)



p.write_text(t, encoding='utf-8')

print('patched', 'com.mysql.cj.jdbc.Driver' in t, 'Dump baseline app log' in t, 'minIdle: 0' in t)

