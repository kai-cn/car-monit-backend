#!/usr/bin/env python3

"""
@description 历史脚本 patch-rust-direct-probe.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python patch-rust-direct-probe.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\rust-state-check.rs')

t = p.read_text(encoding='utf-8')

if 'use sqlx::ConnectOptions;' not in t:

    t = t.replace('use sqlx::mysql::MySqlPoolOptions;\n',

                  'use sqlx::mysql::MySqlPoolOptions;\nuse sqlx::ConnectOptions;\n', 1)

needle = '''        let pool = MySqlPoolOptions::new()

'''

probe = '''        // Diagnostic: establish one connection outside the pool so the real

        // driver error is reported instead of only "pool timed out".

        let probe = connect_options

            .connect()

            .await

            .map_err(|e| anyhow::anyhow!("MySQL direct connect failed: {}", e))?;

        drop(probe);



'''

assert needle in t

t = t.replace(needle, probe + needle, 1)

p.write_text(t, encoding='utf-8')

print('probe added', 'MySQL direct connect failed' in t)

