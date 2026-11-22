#!/usr/bin/env python3

"""
@description 历史脚本 cleanup-rust-diagnostics.py：执行运维或验证流程中的辅助操作；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python cleanup-rust-diagnostics.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
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

