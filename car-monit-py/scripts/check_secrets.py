"""仓库明文密钥扫描（CI 门禁）.

扫描范围与声明必须一致：发布/运行代码与配置 ``app/``、``config/``、``scripts/``、
``alembic/``、``.env.example``，以及仓库根的 ``.github/``（本目录是子项目，
workflow 在上一级）。不扫描 ``tests/`` 里的测试夹具（那里出现的只是用于验证
算法/拒绝逻辑的样例）。命中任一历史内置密钥/口令字面量即失败。
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: 只扫描“会进入运行配置/构建产物”的位置；测试夹具与业务 docstring 里出现的
#: 密钥样例不算泄露（测试里的值只用于验证算法/拒绝逻辑）。
SCAN_TARGETS = (
    "app",
    "config",
    "scripts",
    "alembic",
    ".env.example",
)
_SELF = Path(__file__).resolve()

#: 曾经写死在仓库里的演示密钥/口令。任何一项再次出现都必须阻断。
FORBIDDEN_LITERALS: Tuple[str, ...] = (
    "abcdefghijklmnopqrstuvwxyz",
    "b48381c4b98311ea90b100155d14fa3b",
    "jtwl_access_key",
    "minio.prod",
    "Sys#2024Test",
)

#: 用"前后不是字母/数字"约束，避免把 ``file_utils`` 里的字符集常量
#: ``...XYZabcdefghijklmnopqrstuvwxyz0123456789...`` 误报成密钥字面量。
_FORBIDDEN_PATTERNS: Tuple[Tuple[str, "re.Pattern[str]"], ...] = tuple(
    (literal, re.compile(rf"(?<![A-Za-z0-9]){re.escape(literal)}(?![A-Za-z0-9])"))
    for literal in FORBIDDEN_LITERALS
)

_SKIP_EXTENSIONS = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".xlsx", ".docx", ".jar"}


def _github_dir(root: Path) -> Optional[Path]:
    """``.github/`` 的位置：子项目目录没有时回退到仓库根（上两级没有就放弃）。"""
    for candidate in (root / ".github", root.parent / ".github"):
        if candidate.is_dir():
            return candidate
    return None


def _scan_paths(root: Path) -> List[Path]:
    """所有扫描目标（解析后的实际路径）；不存在的目标直接跳过。"""
    paths = [root / target for target in SCAN_TARGETS]
    github = _github_dir(root)
    if github is not None:
        paths.append(github)
    return paths


def _iter_files(root: Path) -> Iterable[Path]:
    for path in _scan_paths(root):
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = list(path.rglob("*"))
        else:
            continue
        for candidate in candidates:
            if (
                candidate.is_file()
                and candidate.suffix.lower() not in _SKIP_EXTENSIONS
                and candidate.resolve() != _SELF
            ):
                yield candidate


def scan(root: Path) -> List[Tuple[str, str]]:
    """返回 ``(相对路径, 命中的字面量)`` 列表；空列表表示干净。"""
    hits: List[Tuple[str, str]] = []
    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for literal, pattern in _FORBIDDEN_PATTERNS:
            if pattern.search(text):
                # 仓库根的 .github 不在 root 之下，用相对 root 的路径（可能带 ``..``）
                hits.append((Path(os.path.relpath(path, root)).as_posix(), literal))
    return hits


def main() -> int:
    hits = scan(PROJECT_ROOT)
    if not hits:
        print("secret scan: clean")
        return 0
    for path, literal in hits:
        print(f"secret scan: {path} contains forbidden literal {literal!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
