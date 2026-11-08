"""``MAPPING_*.md`` 的一致性护栏.

# Migrated from: (no Java equivalent -- 检查本工程自己生成的对照表)

为什么值得测
------------
这 5 份表由 ``scripts/gen_mapping_docs.py`` 生成，内容是「Java 文件 → Python 文件」与
「每个映射的方法/路径/权限点」。它们不进运行期，但**是给接手同事的唯一索引**：表里少一行，
就等于有人会漏改一个端点而没人知道。

这里只测三件**机器能判定**的事，不管文字够不够好看：

* 5 份文件都在、且都有 §1–§5 五个小节；
* §1 里写的「端点 / 控制器」数，与 §4 实际列出的行数、以及
  ``scripts/audit_endpoints.py`` 的 Java 侧计数三者一致；
* 生成器是幂等的（再跑一次，内容完全不变），否则说明生成逻辑读了时间/随机量。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_endpoints as base  # noqa: E402

DOCS: Dict[str, str] = {
    "base": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/base",
    "manager": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/manager",
    "flow": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/flow",
    "tool": "ruoyi-admin/src/main/java/com/ruoyi/web/controller/tool",
    "generator": "ruoyi-generator/src/main/java/com/ruoyi/generator/controller",
}


def _doc(package: str) -> str:
    return (ROOT / f"MAPPING_{package.upper()}.md").read_text(encoding="utf-8")


def _declared(text: str, label: str) -> int:
    """读 ``| 端点 | 106 | ...`` 这种概况行里的数字."""

    match = re.search(rf"^\| {label} \| (\d+) \|", text, re.MULTILINE)
    assert match is not None, f"概况表里找不到 {label} 行"
    return int(match.group(1))


def _endpoint_rows(text: str) -> int:
    """§4 里真正的端点表行数（排除表头与分隔线）."""

    section = text.split("## 4.", 1)[1].split("## 5.", 1)[0]
    return sum(
        1
        for line in section.splitlines()
        if line.startswith("| `") and line.count("|") >= 6
    )


@pytest.mark.parametrize("package", sorted(DOCS))
def test_doc_exists_with_all_sections(package: str) -> None:
    """5 个包各有一份表，且 §1–§5 齐全."""

    text = _doc(package)
    for heading in ("## 1. 切片概况", "## 2. 要点", "## 3. 文件级对照", "## 4. 控制器端点", "## 5. 测试"):
        assert heading in text, f"MAPPING_{package.upper()}.md 缺 {heading}"


@pytest.mark.parametrize("package", sorted(DOCS))
def test_declared_counts_match_the_tables(package: str) -> None:
    """概况里写的端点数 = §4 实际行数 = Java 侧真实映射数（三处必须一致）."""

    text = _doc(package)
    # 与生成器同一口径：路径按 posix 比较，兼容 Windows / Linux
    marker = DOCS[package].replace("\\", "/")
    expected = len(
        [
            item
            for item in base.collect_java()
            if marker in str(_source_of(item.controller)).replace("\\", "/")
        ]
    )

    assert _declared(text, "端点") == expected
    assert _endpoint_rows(text) == expected


@pytest.mark.parametrize("package", sorted(DOCS))
def test_every_controller_is_listed(package: str) -> None:
    """Java 目录下的每个 ``*Controller.java`` 都要在 §4 里有自己的小节."""

    directory = ROOT.parent / DOCS[package]
    controllers = sorted(path.stem for path in directory.rglob("*Controller.java"))
    text = _doc(package)

    assert controllers, "目录里应该至少有一个控制器"
    for controller in controllers:
        assert f"`{controller}`（" in text, f"{controller} 没有出现在 MAPPING_{package.upper()}.md 的 §4"


def test_generator_is_idempotent() -> None:
    """重跑生成器，内容必须逐字节不变（否则说明混进了时间/随机量）."""

    before = {name: _doc(package) for package, name in ((p, p) for p in DOCS)}
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "gen_mapping_docs.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    after = {name: _doc(package) for package, name in ((p, p) for p in DOCS)}
    assert before == after


def _source_of(controller: str) -> Path:
    """控制器类名 -> 它的 Java 文件路径（与生成器同一口径）."""

    for directory in base.JAVA_SOURCES:
        if not directory.exists():
            continue
        for path in directory.rglob("*Controller.java"):
            if path.stem == controller:
                return path
    return Path("")
