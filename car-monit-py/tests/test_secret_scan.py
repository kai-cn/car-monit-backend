"""仓库明文密钥扫描门禁的回归用例."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_secrets  # noqa: E402


def test_repository_has_no_forbidden_secret_literals() -> None:
    assert check_secrets.scan(PROJECT_ROOT) == []


def test_scanner_flags_a_known_literal(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "leak.yml").write_text(
        'secret: "abcdefghijklmnopqrstuvwxyz"\n', encoding="utf-8"
    )

    assert check_secrets.scan(tmp_path) == [("config/leak.yml", "abcdefghijklmnopqrstuvwxyz")]
