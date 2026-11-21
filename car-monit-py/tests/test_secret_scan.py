"""仓库明文密钥扫描门禁的回归用例."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import check_secrets  # noqa: E402

_LEAK = "abcdefghijklmnopqrstuvwxyz"


def test_repository_has_no_forbidden_secret_literals() -> None:
    assert check_secrets.scan(PROJECT_ROOT) == []


def test_scan_targets_match_the_declared_scope() -> None:
    """docstring 声明的范围必须和 ``SCAN_TARGETS`` 一致；删掉任意目标都会变红."""
    assert set(check_secrets.SCAN_TARGETS) == {
        "app",
        "config",
        "scripts",
        "alembic",
        ".env.example",
    }
    for target in check_secrets.SCAN_TARGETS:
        assert (PROJECT_ROOT / target).exists(), f"扫描目标不存在: {target}"


def test_github_directory_resolves_to_the_repository_root() -> None:
    """``car-monit-py/.github`` 不存在，workflow 在仓库根，不能静默跳过."""
    github = check_secrets._github_dir(PROJECT_ROOT)

    assert github is not None and github.is_dir()
    assert github.parent == PROJECT_ROOT.parent


def test_every_declared_target_is_scanned(tmp_path: Path) -> None:
    """每个声明目标放进一个泄漏文件，扫描必须全部命中."""
    for folder in ("app", "config", "scripts", "alembic"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "leak.py").write_text(f'VALUE = "{_LEAK}"\n', encoding="utf-8")
    (tmp_path / ".env.example").write_text(f"TOKEN__SECRET={_LEAK}\n", encoding="utf-8")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "leak.yml").write_text(f"secret: {_LEAK}\n", encoding="utf-8")

    hits = check_secrets.scan(tmp_path)

    assert sorted(path for path, _literal in hits) == sorted(
        [
            "alembic/leak.py",
            "app/leak.py",
            "config/leak.py",
            "scripts/leak.py",
            ".env.example",
            ".github/leak.yml",
        ]
    )


def test_character_set_constants_are_not_false_positives(tmp_path: Path) -> None:
    """字母表常量（前后仍是字母数字）不能被当成密钥字面量."""
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "file_utils.py").write_text(
        'SAFE = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"\n',
        encoding="utf-8",
    )

    assert check_secrets.scan(tmp_path) == []


def test_scanner_flags_a_known_literal(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "leak.yml").write_text(
        f'secret: "{_LEAK}"\n', encoding="utf-8"
    )

    assert check_secrets.scan(tmp_path) == [("config/leak.yml", _LEAK)]
