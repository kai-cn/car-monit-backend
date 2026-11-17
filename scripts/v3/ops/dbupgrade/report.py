#!/usr/bin/env python3
# ======================================================================
# 用途：汇总“新老库”业务一致性 + 资源占用 + 性能对比，输出 report.json / report.md。
# 调用：python report.py --app api --db mysql --label <label> --out-dir out
# 说明：只做本地 JSON/Markdown 汇总，不接触凭据。
# ======================================================================
import argparse
import json
from pathlib import Path


def load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:
        return {}


def text(p):
    try:
        return Path(p).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def stat(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals), 2) if vals else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out-dir", default="out")
    a = ap.parse_args()
    o = Path(a.out_dir)

    old = load(o / "old.json")
    new = load(o / "new.json")
    cmp_ = load(o / "compare.json").get("totals", {})

    def summarize(p):
        eps = p.get("endpoints") or []
        return {
            "ready": p.get("ready"),
            "error": p.get("error"),
            "endpoint_count": len(eps),
            "status_fail": sum(1 for e in eps if e.get("status") not in (200, 201, 204, 302)),
            "startup_ms": p.get("startup_ms"),
            "startup_peak_rss_mb": p.get("startup_peak_rss_mb"),
            "steady_rss_mb": p.get("steady_rss_mb"),
            "avg_latency_ms": stat([e.get("latency_ms") for e in eps]),
        }

    data = {
        "label": a.label,
        "app": a.app,
        "db": a.db,
        "old": summarize(old),
        "new": summarize(new),
        "consistency": {
            "status_match": cmp_.get("status_match"),
            "exact": cmp_.get("exact"),
            "semantic": cmp_.get("semantic"),
            "nondet": cmp_.get("nondet"),
            "diff": cmp_.get("diff"),
            "fails": cmp_.get("fails"),
        },
        "db_old_version": text(o / f"{a.db}_old.version.txt"),
        "db_new_version": text(o / f"{a.db}_new.version.txt"),
        "db_old_stats": load(o / f"{a.db}_old.stats.json"),
        "db_new_stats": load(o / f"{a.db}_new.stats.json"),
        "dump_method": text(o / f"{a.db}_dump.method.txt"),
    }
    (o / "report.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def row(name, ov, nv):
        return f"| {name} | {ov} | {nv} |"

    md = [
        f"# DB upgrade verification: {a.app} / {a.db} ({a.label})", "",
        "## 业务一致性（同一 jar、同一端点清单）", "",
        "| 指标 | 结果 |", "|---|---|",
        f"| status_match | {data['consistency']['status_match']} |",
        f"| exact | {data['consistency']['exact']} |",
        f"| semantic | {data['consistency']['semantic']} |",
        f"| nondet | {data['consistency']['nondet']} |",
        f"| diff / fails | {data['consistency']['diff']} / {data['consistency']['fails']} |", "",
        "## 资源占用与性能（old -> new）", "",
        "| 指标 | old | new |", "|---|---|---|",
        row("DB version", data["db_old_version"][:80], data["db_new_version"][:80]),
        row("DB CPU", data["db_old_stats"].get("cpu"), data["db_new_stats"].get("cpu")),
        row("DB memory", data["db_old_stats"].get("mem"), data["db_new_stats"].get("mem")),
        row("app startup_ms", data["old"]["startup_ms"], data["new"]["startup_ms"]),
        row("app startup RSS(MB)", data["old"]["startup_peak_rss_mb"], data["new"]["startup_peak_rss_mb"]),
        row("app steady RSS(MB)", data["old"]["steady_rss_mb"], data["new"]["steady_rss_mb"]),
        row("app avg latency(ms)", data["old"]["avg_latency_ms"], data["new"]["avg_latency_ms"]),
        row("app status_fail", data["old"]["status_fail"], data["new"]["status_fail"]), "",
        f"迁移方式: `{data['dump_method']}`", "",
    ]
    (o / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
