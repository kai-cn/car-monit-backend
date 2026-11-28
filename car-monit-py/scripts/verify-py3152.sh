#!/usr/bin/env bash
# @description 用 uv 管理的 Python 3.15.2 建立隔离 venv，安装锁定依赖，执行语法门禁、单测与 wheel/sdist 构建。
#              本机默认 Python 为 3.11，且 3.12 的旧依赖（orjson 3.10 / Pillow 11 / pydantic 2.10）
#              在 3.15 下会触发 PyO3 版本错误或缺失 wheel，因此统一走此脚本复现 CI 的 3.15.2 环境。
# @author Tencent Hunyuan Hy
# @date 2026-11-28 16:13:11
# @usage bash scripts/verify-py3152.sh
# @dependencies uv 0.13.10+（位于 /home/dev/.local/bin）、CPython 3.15.2（uv 管理）、
#               libjpeg-devel（Pillow 源码兜底编译时需要）、系统 gcc/make（orjson 源码构建需要）

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV="/home/dev/.local/bin/uv"
PY="/home/dev/.local/share/uv/python/cpython-3.15.2-linux-x86_64-gnu/bin/python3.15"

cd "$ROOT"

echo "[1/5] 重建 venv（Python 3.15.2）"
# --clear 保证每次都从锁定依赖重建，避免上次失败残留污染验证结果。
"$UV" venv --clear --python "$PY" .venv

echo "[2/5] 安装项目与测试依赖"
"$UV" pip install --python .venv/bin/python -r requirements.txt

echo "[3/5] 语法门禁"
.venv/bin/python -m compileall -q app scripts

echo "[4/5] 单元测试（不含 integration）"
.venv/bin/python -m pytest -v -m "not integration" --tb=short

echo "[5/5] 构建 wheel / sdist"
"$UV" pip install --python .venv/bin/python build
.venv/bin/python -m build

echo "[done] Python 3.15.2 编译/测试/构建全部完成"
