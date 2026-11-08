"""仓库明文密钥扫描（CI 门禁）.

只扫描发布/运行代码与配置（``app/``、``config/``、``scripts/``、``alembic/``、
``.github/``），不扫描 ``tests/`` 里的测试夹具（那里出现的只是用于验证算法的样例）。
命中任一历史内置密钥/口令字面量即失败。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: 只扫描“会进入运行配置/构建产物”的位置；测试夹具与业务 docstring 里出现的
#: 密钥样例不算泄露（测试里的值只用于验证算法/拒绝逻辑）。
SCAN_TARGETS = (
    "config",
    "app/settings.py",
    ".env.example",
    ".github",
    "scripts",
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

_SKIP_EXTENSIONS = {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".xlsx", ".docx", ".jar"}


def _iter_files(root: Path) -> Iterable[Path]:
    for target in SCAN_TARGETS:
        path = root / target
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
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                hits.append((path.relative_to(root).as_posix(), literal))
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
