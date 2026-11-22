#!/usr/bin/env python3

"""
@description 历史脚本 patch-rust-ssl-off.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author Tencent Hunyuan Hy
@date 2026-11-22
@usage python patch-rust-ssl-off.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖
"""
from pathlib import Path

p = Path(r'D:\work\runtime-logs\rust-state.rs')

t = p.read_text(encoding='utf-8')

needle = '''        url.set_password(Some(&settings.database.password))

            .map_err(|_| anyhow::anyhow!("database.password 非法"))?;

'''

add = needle + '''

        // Cloud MySQL uses useSSL=false; sqlx defaults to ssl-mode=PREFERRED,

        // which can hang during TLS negotiation and surface as a pool timeout.

        if settings.database.url.contains("useSSL=false") {

            url.query_pairs_mut().append_pair("ssl-mode", "disabled");

        }

'''

assert needle in t

p.write_text(t.replace(needle, add, 1), encoding='utf-8')

print('patched', 'ssl-mode' in t)

