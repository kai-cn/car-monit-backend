# -*- coding: utf-8 -*-
"""从迁移基线 docs/01-baseline/02-endpoints.md 生成端点清单 endpoints.json。

基线由 tools/gen_baseline.py 解析 Java 源码得到，所以这里的端点集合与 Java 一致。
用法：python -m tools.endpoint_parity.endpoints  （或 python endpoints.py）
"""
from __future__ import annotations

import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUST_ROOT = HERE.parents[1]                      # car-monit-rust
BASELINE = RUST_ROOT / "docs" / "01-baseline" / "02-endpoints.md"
OUTPUT = HERE / "endpoints.json"

ROW = re.compile(r"\|\s*(\d+)\s*\|\s*(GET|POST|PUT|DELETE|PATCH)\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|")


def load(path: Path = BASELINE) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            match = ROW.match(line)
            if match:
                rows.append(
                    dict(
                        idx=int(match.group(1)),
                        method=match.group(2),
                        path=match.group(3),
                        handler=match.group(4).strip(),
                    )
                )
    return rows


def main() -> int:
    if not BASELINE.exists():
        print(f"基线文件不存在：{BASELINE}\n先运行 tools/gen_baseline.py", file=sys.stderr)
        return 2
    rows = load()
    counts = collections.Counter(row["method"] for row in rows)
    placeholders = collections.Counter(
        name for row in rows if row["method"] == "GET" for name in re.findall(r"\{([^}/]+)\}", row["path"])
    )
    OUTPUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"endpoints: total={len(rows)} GET={counts['GET']} -> {OUTPUT}")
    print(f"methods: {dict(counts)}")
    print("GET 路径变量（需在 compare.py 的 S/RULES 里给样例值）:")
    print(json.dumps(placeholders.most_common(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
