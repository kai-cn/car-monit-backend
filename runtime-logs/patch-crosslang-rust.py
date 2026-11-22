#!/usr/bin/env python3

"""
@description 历史脚本 patch-crosslang-rust.py：修改 workflow、脚本或测试口径；保留原有执行逻辑，仅补充交接所需背景、用法和依赖，避免脚本意图随会话丢失。
@author AI Assistant
@date 2026-11-22 23:45:04
@usage python patch-crosslang-rust.py [args]；具体参数以脚本 argparse 或源码说明为准。
@dependencies Python 3 标准库及脚本原有第三方依赖

Idea:


- baseline job already runs Java25 Boot4 and uploads contract/load reports


- candidate matrix originally covered python/go/cpp only


- add rust with the existing Rust config pattern (3307 -> 3306, port 19903)


- apply to backend (src/car-monit-rust) and api (src-rust) layouts
"""
from pathlib import Path

import yaml



FILES = [

    (Path(r'D:\work\IdeaProjects\car-monit-backend-new\.github\workflows\crosslang-full-parity-cloud.yml'),

     'src/car-monit-rust', 'src/car-monit-rust'),

    (Path(r'D:\work\IdeaProjects\car-monit-api\.github\workflows\crosslang-full-parity-cloud.yml'),

     'src-rust', 'src-rust'),

]



for p, rust_dir, cfg_dir in FILES:

    t = p.read_text(encoding='utf-8')

    t = t.replace('lang: [python, go, cpp]', 'lang: [python, go, cpp, rust]', 1)

    anchor = '''      - name: Wait candidate and run JUnit

'''

    rust_step = f'''      - name: Build and start Rust

        if: steps.gate.outputs.run == yes && matrix.lang == rust

        shell: bash

        env:

          APP_DATABASE__URL: "mysql://root:root@127.0.0.1:3306/carmonitdb"

          APP_REDIS__URL: "redis://127.0.0.1:6379"

          APP_SERVER__PORT: "19903"

        run: |

          set -euo pipefail

          cd {rust_dir}

          cargo build --release

          sed -i 's#127\\.0\\.0\\.1:3307#127.0.0.1:3306#g; s#useSSL=true#useSSL=false#g' {cfg_dir}/config/application.* 2>/dev/null || true

          ./target/release/car-monit-rust > "$GITHUB_WORKSPACE/app.log" 2>&1 &

          echo $! > "$GITHUB_WORKSPACE/app.pid"



'''

    assert anchor in t, p

    t = t.replace(anchor, rust_step + anchor, 1)

    p.write_text(t, encoding='utf-8')

    yaml.safe_load(t)

    print('patched', p)

