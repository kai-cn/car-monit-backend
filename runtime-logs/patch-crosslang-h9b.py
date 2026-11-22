#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：patch-crosslang-h9b.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
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
