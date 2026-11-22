#!/usr/bin/env python3
"""
LEGACY-SCRIPT-ANNOTATION
文件：cleanup-rust-diagnostics.py
用途：本地或远端修复/改造。
思路：历史脚本缺少统一说明；本注释用于交代用途、思路与风险，不改变执行逻辑。
风险：会修改文件、索引或远端，执行前确认可回滚。
"""
from pathlib import Path

wf = Path(r'D:\work\runtime-logs\crosslang-rust-debug.yml')
t = wf.read_text(encoding='utf-8')
for line in [
    '          RUST_LOG: "sqlx::pool=trace,car_monit_rust=info"\n',
    "          RUST_BACKTRACE: '1'\n",
]:
    t = t.replace(line, '')
if 'RUST_LOG' not in t:
    marker = '        env:\n'
    t = t.replace(marker, marker + '          # APP_* overrides the embedded YAML: the binary reads config from CWD,\n'
                  '          # so editing config/application.yaml in the repo is not enough.\n', 1)
wf.write_text(t, encoding='utf-8')

rs = Path(r'D:\work\runtime-logs\rust-state-check.rs')
s = rs.read_text(encoding='utf-8')
s = s.replace('use sqlx::ConnectOptions;\n', '')
probe = '''        // Diagnostic: establish one connection outside the pool so the real
        // driver error is reported instead of only "pool timed out".
        let probe = connect_options
            .connect()
            .await
            .map_err(|e| anyhow::anyhow!("MySQL direct connect failed: {}", e))?;
        drop(probe);

'''
s = s.replace(probe, '')
rs.write_text(s, encoding='utf-8')

import yaml
yaml.safe_load(wf.read_text(encoding='utf-8'))
print('cleaned', 'RUST_LOG' not in t, 'direct probe' not in s)
