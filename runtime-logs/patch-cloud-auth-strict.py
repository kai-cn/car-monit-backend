#!/usr/bin/env python3
"""
@description 为 backend/api 的 JUnit 与跨语言 workflow 增加管理员鉴权、严格对拍门禁，并清理已合并分支的旧 checkout。
@author Tencent Hunyuan Hy
@date 2026-11-22 23:45:04
@usage python runtime-logs/patch-cloud-auth-strict.py
@dependencies 修改两仓库 master 工作树中的 workflow 与 harness 脚本。
"""
from pathlib import Path

BACKEND = Path(r'D:\work\IdeaProjects\car-monit-backend-new')
API = Path(r'D:\work\IdeaProjects\car-monit-api')
SECRETS = '''        env:
          CARMONIT_ADMIN_USER: ${{ secrets.CI_ADMIN_USER }}
          CARMONIT_ADMIN_PASSWORD: ${{ secrets.CI_ADMIN_PASSWORD }}
'''
TOKEN_LINE = '''          TOKEN=$(python3 harness/scripts/v3/ops/junit/junit-auth-token.py --base-url "$BASE_URL")
          export ENDPOINT_HEADERS="Authorization: Bearer ${TOKEN}"
'''


def patch_workflow(p: Path, api_repo: bool) -> None:
    """把鉴权 env、token 导出和严格对拍写入 workflow；保留其他逻辑不变。"""
    t = p.read_text(encoding='utf-8')
    t = t.replace('default: car-monit-api-jdk25', 'default: master')
    t = t.replace('default: car-monit-backend-jdk25', 'default: master')
    t = t.replace('default: java25-vs-crosslang', 'default: java-master-vs-crosslang')
    if api_repo:
        # 多语言和 Java V3 已合并 master，删除单独的 rust/cpp 分支 checkout。
        old = '''      - name: Checkout Rust source
        uses: actions/checkout@v4
        with:
          ref: car-monit-api-rust
          path: src-rust
      - name: Checkout C++ source
        uses: actions/checkout@v4
        with:
          ref: car-monit-api-cpp
          path: src-cpp
'''
        t = t.replace(old, '')
        t = t.replace('cd src-rust/car-monit-api-rust', 'cd src/car-monit-api-rust')
        t = t.replace('cd src-cpp/car-monit-api-cpp', 'cd src/car-monit-api-cpp')
    # Baseline JUnit 执行前导出管理员 token；candidate 同样处理。
    t = t.replace('''      - name: Start baseline and run harness
        shell: bash
''', '''      - name: Start baseline and run harness
        shell: bash
''' + SECRETS, 1)
    t = t.replace('''      - name: Wait candidate and run JUnit
        if: steps.gate.outputs.run == 'yes'
        shell: bash
''', '''      - name: Wait candidate and run JUnit
        if: steps.gate.outputs.run == 'yes'
        shell: bash
''' + SECRETS, 1)
    marker = '          javac -encoding UTF-8 -source 8 -target 8 -cp out/junit.jar -d out/classes out/generated/*.java\n'
    if marker in t and 'junit-auth-token.py' not in t:
        t = t.replace(marker, marker + TOKEN_LINE, 1)
    marker2 = '          javac -encoding UTF-8 -source 8 -target 8 -cp out-junit.jar -d out/classes out/generated/*.java\n'
    if marker2 in t and t.count('junit-auth-token.py') < 2:
        t = t.replace(marker2, marker2 + TOKEN_LINE, 1)
    # 严格对拍：任何 DIFF/NONDET 都使 job 失败；压测仍只作为证据。
    t = t.replace("            --label \"${{ inputs.label }}-${{ matrix.lang }}\" || true\n          python3 harness/scripts/v3/ops/junit/compare_load.py",
                  "            --label \"${{ inputs.label }}-${{ matrix.lang }}\" --strict\n          python3 harness/scripts/v3/ops/junit/compare_load.py", 1)
    p.write_text(t, encoding='utf-8')
    print('PATCHED', p)


for repo, is_api in [(BACKEND, False), (API, True)]:
    patch_workflow(repo / '.github/workflows/crosslang-full-parity-cloud.yml', is_api)
    for src, rel in [
        (BACKEND / 'runtime-logs/generate_junit_suite.py', 'scripts/v3/ops/junit/generate_junit_suite.py'),
        (BACKEND / 'runtime-logs/parity_compare.py', 'scripts/v3/ops/parity/parity_compare.py'),
        (BACKEND / 'runtime-logs/junit-auth-token.py', 'scripts/v3/ops/junit/junit-auth-token.py'),
    ]:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
    print('SYNCED', repo)
