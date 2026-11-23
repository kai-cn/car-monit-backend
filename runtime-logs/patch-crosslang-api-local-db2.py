#!/usr/bin/env python3
"""
@description 修正跨语言 workflow：为 api 候选注入本地 PG 配置并在启动前改写源码配置。
@author Tencent Hunyuan Hy
@date 2026-11-23 09:01:14
@usage python3 runtime-logs/patch-crosslang-api-local-db2.py
@dependencies backend/api 两仓库 master 工作树中的 crosslang-full-parity-cloud.yml。
"""
from pathlib import Path

FILES = [
    Path('/home/dev/IdeaProjects/car-monit-backend/.github/workflows/crosslang-full-parity-cloud.yml'),
    Path('/home/dev/IdeaProjects/car-monit-api/.github/workflows/crosslang-full-parity-cloud.yml'),
]

for p in FILES:
    t = p.read_text(encoding='utf-8')

    py_anchor = '          TOKEN__SECRET: junit-cloud-secret-deterministic-0123456789abcdef\n          VEHICLE_MONITOR_BASE_URL: "http://127.0.0.1:9902"'
    py_new = '''          TOKEN__SECRET: junit-cloud-secret-deterministic-0123456789abcdef
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: "jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false"
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres
          SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: postgres
          VEHICLE_MONITOR_BASE_URL: "http://127.0.0.1:9902"'''
    t = t.replace(py_anchor, py_new, 1)

    go_anchor = '          CARMONIT_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"\n        run: |'
    go_new = '''          CARMONIT_TOKEN_SECRET: "junit-cloud-secret-deterministic-0123456789abcdef"
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_URL: "jdbc:postgresql://127.0.0.1:5432/RuoYi?characterEncoding=UTF-8&useUnicode=true&useSSL=false"
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_USERNAME: postgres
          APP_SPRING_DATASOURCE_DYNAMIC_DATASOURCE_MASTER_PASSWORD: postgres
        run: |'''
    t = t.replace(go_anchor, go_new, 1)

    cpp_anchor = '''          cd "$DIR"
          cmake -S . -B "$BUILD"'''
    cpp_new = '''          cd "$DIR"
          if [ '${{ inputs.app }}' = api ]; then sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g; s#port: 9901#port: 19903#g' configs/config.yaml; fi
          cmake -S . -B "$BUILD"'''
    t = t.replace(cpp_anchor, cpp_new, 1)

    rust_anchor = '''          cd "$DIR"
          cargo build --release'''
    rust_new = '''          cd "$DIR"
          if [ '${{ inputs.app }}' = api ]; then sed -i 's#192\\.168\\.56\\.10#127.0.0.1#g; s#username: gaussdb#username: postgres#g; s#port: 9901#port: 19903#g' config/application.yaml; fi
          cargo build --release'''
    t = t.replace(rust_anchor, rust_new, 1)

    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)
