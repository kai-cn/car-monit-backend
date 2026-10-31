"""Generate the Phase-1 migration baseline appendices for the Java -> Rust migration.

Reads the sibling Java project (../ruoyi-*) and writes:
  docs/01-baseline/01-file-map.md
  docs/01-baseline/02-endpoints.md
  docs/01-baseline/03-data-layer.md
  docs/01-baseline/inventory.json

The endpoint parser is shared with ../car-monit-py/scripts/audit_endpoints.py so that
the Java-side endpoint count stays identical to the already-verified Python migration.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict, OrderedDict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

RUST_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = RUST_ROOT.parent
OUT = RUST_ROOT / "docs" / "01-baseline"

MODULES = ["ruoyi-admin", "ruoyi-common", "ruoyi-framework", "ruoyi-system", "ruoyi-quartz", "ruoyi-generator"]

SNACK_RE = re.compile(r"([A-Z]+)([A-Z][a-z])")
SNACK_RE2 = re.compile(r"([a-z0-9])([A-Z])")


def snake(name: str) -> str:
    s = SNACK_RE.sub(r"\1_\2", name)
    s = SNACK_RE2.sub(r"\1_\2", s)
    return s.lower()


def classify(rel: str, name: str) -> Tuple[str, str]:
    """(role, translation kind)."""
    p = rel.replace("\\", "/")
    if name.endswith("Controller.java"):
        return "Controller（HTTP 路由）", "框架契约"
    if "/kafka/consumer/" in p:
        return "Kafka 消费者", "混合"
    if "/elasticsearch/" in p:
        return "Elasticsearch 接入", "混合"
    if "/sharding/" in p:
        return "分表算法/配置", "混合"
    if "/service/cdc/" in p:
        return "CDC 同步服务", "混合"
    if "/service/enhanced/" in p:
        return "分表增强查询", "纯逻辑"
    if "/service/consistency/" in p:
        return "数据一致性任务", "纯逻辑"
    if "/service/query/" in p:
        return "分区并行查询", "纯逻辑"
    if "/service/forest/" in p or "/service/forest" in p:
        return "外部 HTTP 客户端（Forest）", "框架契约"
    if "/task/" in p:
        return "定时/后台任务", "混合"
    if "/mapper/" in p:
        return "Mapper 接口", "框架契约"
    if "/domain/" in p or "/bean/" in p or "/model/" in p:
        return "Domain/DTO/VO", "纯逻辑"
    if "/enums/" in p:
        return "枚举", "纯逻辑"
    if "/constant/" in p:
        return "常量", "纯逻辑"
    if "/exception/" in p:
        return "异常类型", "纯逻辑"
    if "/annotation/" in p:
        return "注解（编译期标记）", "框架契约"
    if "/aspect/" in p or "/aspectj/" in p:
        return "AOP 切面", "框架契约"
    if "/filter/" in p:
        return "Servlet 过滤器", "框架契约"
    if "/interceptor/" in p:
        return "拦截器", "框架契约"
    if "/config/" in p or name.endswith("Config.java") or name.endswith("Configuration.java"):
        return "配置装配", "框架契约"
    if "/util/" in p or name.endswith("Utils.java") or name.endswith("Util.java"):
        return "工具类", "纯逻辑"
    if "/core/domain/" in p or name.endswith("Entity.java"):
        return "核心领域对象", "纯逻辑"
    if "/core/" in p:
        return "框架核心", "混合"
    if "/service/impl/" in p:
        return "Service 实现", "混合"
    if "/service/" in p:
        return "Service 接口/服务", "框架契约"
    if name.endswith("Application.java"):
        return "启动类", "框架契约"
    if name.endswith("Initializer.java"):
        return "WAR 部署入口", "框架契约"
    if "/manager/" in p:
        return "后台管理器", "混合"
    return "其他", "混合"


def rust_target(module: str, rel: str, name: str) -> str:
    """Map a Java source path (relative to module/src/main/java) to its Rust target."""
    p = rel.replace("\\", "/")
    stem = name[:-5]  # drop .java
    if p.startswith("com/ruoyi/") and "/web/controller/" in p:
        slice_path = p.split("/web/controller/", 1)[1].rsplit("/", 1)[0]
        parts = [x for x in slice_path.split("/") if x]
        return "src/api/" + "/".join(parts + [snake(stem) + ".rs"])
    if p == "com/ruoyi/RuoYiApplication.java":
        return "src/main.rs"
    if p.endswith("RuoYiServletInitializer.java"):
        return "（不迁移：WAR 部署入口）"
    if "/admin/config/" in p or "/web/core/config/" in p:
        special = {
            "ShardingSphereConfig": "src/app/sharding_config.rs（由自研分表路由替代）",
            "SwaggerConfig": "src/app/openapi.rs（utoipa）",
        }
        return special.get(stem, "src/app/" + snake(stem) + ".rs")
    if "/web/util/" in p:
        return "src/api/util/" + snake(stem) + ".rs"
    if p.startswith("com/ruoyi/common/"):
        rest = p[len("com/ruoyi/common/"):]
        parts = rest.split("/")
        fname = snake(stem) + ".rs"
        if len(parts) == 1:
            return "src/common/" + fname
        return "src/common/" + "/".join(parts[:-1] + [fname])
    if p.startswith("com/ruoyi/framework/"):
        rest = p[len("com/ruoyi/framework/"):]
        parts = rest.split("/")
        return "src/framework/" + "/".join(parts[:-1] + [snake(stem) + ".rs"])
    if module == "ruoyi-quartz" and "/controller/" in p:
        return "src/api/quartz/" + snake(stem) + ".rs"
    if module == "ruoyi-generator" and "/controller/" in p:
        return "src/api/generator/" + snake(stem) + ".rs"
    if p.startswith("com/ruoyi/"):
        rest = p[len("com/ruoyi/"):]
        parts = rest.split("/")
        # merge I*Service interface with *ServiceImpl into one Rust module
        if len(parts) >= 3 and parts[-2] == "impl" and stem.endswith("ServiceImpl"):
            service = stem[: -len("Impl")]
            return "src/" + "/".join(parts[:-2] + ["service", snake(service) + ".rs"])
        if len(parts) >= 2 and parts[-2] == "service" and stem.startswith("I") and stem.endswith("Service"):
            merged = stem[1:]
            return "src/" + "/".join(parts[:-2] + ["service", snake(merged) + ".rs"]) + "（与实现合并）"
        if len(parts) >= 2 and parts[-2] == "service" and stem.endswith("ServiceImpl"):
            return "src/" + "/".join(parts[:-2] + ["service", snake(stem[:-4]) + ".rs"])
        return "src/" + "/".join(parts[:-1] + [snake(stem) + ".rs"])
    return "(unmapped)"


# ---------------------------------------------------------------------------
# Java endpoint parsing (reuse the verified parser from car-monit-py)
# ---------------------------------------------------------------------------

def load_audit_module():
    p = PROJECT_ROOT / "car-monit-py" / "scripts" / "audit_endpoints.py"
    spec = importlib.util.spec_from_file_location("audit_endpoints", p)
    m = importlib.util.module_from_spec(spec)
    sys.modules["audit_endpoints"] = m
    spec.loader.exec_module(m)
    return m


AUDIT = load_audit_module()


def split_top_level(text: str) -> List[str]:
    out, buf, depth = [], [], 0
    for ch in text:
        if ch in "(<[{":
            depth += 1
        elif ch in ")>]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(buf))
            buf = []
            continue
        buf.append(ch)
    if "".join(buf).strip():
        out.append("".join(buf))
    return [x.strip() for x in out if x.strip()]


def strip_param_annotations(param: str) -> Tuple[str, Dict[str, str]]:
    """Remove leading annotations; return remaining declaration + annotation args."""
    anns: Dict[str, str] = {}
    s = param.strip()
    while s.startswith("@"):
        m = re.match(r"@(\w+)", s)
        if not m:
            break
        name = m.group(1)
        rest = s[m.end():]
        args = ""
        if rest.lstrip().startswith("("):
            body = rest.lstrip()[1:]
            depth, i = 1, 0
            while i < len(body):
                if body[i] in "\"'":
                    q = body[i]
                    i += 1
                    while i < len(body) and body[i] != q:
                        if body[i] == "\\":
                            i += 1
                        i += 1
                elif body[i] == "(":
                    depth += 1
                elif body[i] == ")":
                    depth -= 1
                    if depth == 0:
                        args = body[:i]
                        rest = body[i + 1:]
                        break
                i += 1
            else:
                rest = ""
        else:
            rest = rest
        anns[name] = args
        s = rest.strip()
    s = re.sub(r"^\bfinal\b\s*", "", s).strip()
    return s, anns


def param_kind(anns: Dict[str, str], typ: str) -> str:
    if "PathVariable" in anns:
        return "path"
    if "RequestBody" in anns:
        return "body"
    if "RequestHeader" in anns:
        return "header"
    if "RequestParam" in anns:
        return "query"
    if typ.endswith("MultipartFile"):
        return "multipart"
    if typ in {"HttpServletRequest", "HttpServletResponse", "HttpSession", "Model", "ModelMap",
               "BindingResult", "Errors", "OutputStream", "Writer"}:
        return "framework"
    return "query"


def required_and_default(anns: Dict[str, str]) -> str:
    args = anns.get("RequestParam") or anns.get("PathVariable") or anns.get("RequestHeader") or ""
    req = re.search(r"required\s*=\s*(true|false)", args)
    dv = re.search(r'defaultValue\s*=\s*"([^"]*)"', args)
    bits = []
    if req:
        bits.append("required=" + req.group(1))
    if dv:
        bits.append('default="' + dv.group(1) + '"')
    return " ".join(bits)


def parse_method_details(source: str, anns, group: List[int]) -> Optional[dict]:
    after = max(anns[i].end for i in group)
    paren = source.find("(", after)
    if paren < 0:
        return None
    # The annotation group ends right before the declaration. Scanning backwards for
    # ';' / '}' would land inside annotation strings (e.g. @PreAuthorize("...('a:b:c')")),
    # so the declaration starts exactly at the end of the annotation group.
    decl = source[after:paren].strip()
    m = re.search(r"([A-Za-z_$][\w$]*)\s*$", decl)
    if not m:
        return None
    name = m.group(1)
    ret = decl[: m.start()].strip()
    ret = re.sub(r"\b(public|private|protected|static|final|synchronized|abstract|default|native)\b", "", ret)
    ret = re.sub(r"@\w+(\([^)]*\))?", "", ret).strip()
    depth, end = 0, None
    for i in range(paren, len(source)):
        c = source[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                end = i
                break
    params = []
    for raw in split_top_level(source[paren + 1:end if end is not None else len(source)]):
        s, anns_map = strip_param_annotations(raw)
        s = re.sub(r"@\w+(\([^)]*\))?", "", s).strip()
        pm = re.match(r"(.+?)\s+([A-Za-z_$][\w$]*)$", s, re.S)
        if not pm:
            continue
        typ = re.sub(r"\s+", " ", pm.group(1)).strip()
        params.append({
            "name": pm.group(2),
            "type": typ,
            "kind": param_kind(anns_map, typ),
            "meta": required_and_default(anns_map),
        })
    return {"name": name, "return": re.sub(r"\s+", " ", ret), "params": params}


def log_annotation(anns, group: List[int]) -> str:
    for i in group:
        a = anns[i]
        if a.name != "Log":
            continue
        title = re.search(r'title\s*=\s*"([^"]*)"', a.args)
        bt = re.search(r"businessType\s*=\s*(?:BusinessType\.)?(\w+)", a.args)
        return "%s / %s" % (title.group(1) if title else "?", bt.group(1) if bt else "?")
    return "—"


def extract_endpoints() -> List[dict]:
    rows = []
    for controller_file in sorted((PROJECT_ROOT / "ruoyi-admin" / "src" / "main" / "java" / "com" / "ruoyi" / "web" / "controller").rglob("*Controller.java")):
        rows.extend(_extract_from(controller_file))
    for base in [PROJECT_ROOT / "ruoyi-quartz" / "src" / "main" / "java" / "com" / "ruoyi" / "quartz" / "controller",
                 PROJECT_ROOT / "ruoyi-generator" / "src" / "main" / "java" / "com" / "ruoyi" / "generator" / "controller"]:
        for controller_file in sorted(base.rglob("*Controller.java")):
            rows.extend(_extract_from(controller_file))
    return rows


def _extract_from(path: Path) -> List[dict]:
    source = AUDIT.strip_comments(path.read_text(encoding="utf-8", errors="replace"))
    anns = AUDIT.iter_annotations(source)
    prefix, class_index = AUDIT._find_class_mapping(source, anns)
    controller = path.stem
    rel = str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    rows = []
    for index, a in enumerate(anns):
        if a.name not in AUDIT.MAPPING_METHODS and a.name != "RequestMapping":
            continue
        if index == class_index:
            continue
        methods = [AUDIT.MAPPING_METHODS[a.name]] if a.name != "RequestMapping" else AUDIT.parse_request_methods(a.args)
        group = AUDIT._annotation_group(source, anns, index)
        details = parse_method_details(source, anns, group)
        if details is None:
            continue
        perm = AUDIT._permission_in_group(anns, group)
        for suffix in AUDIT.parse_mapping_paths(a.args):
            p = f"{prefix}{suffix}" or "/"
            if not p.startswith("/"):
                p = "/" + p
            for method in methods:
                rows.append({
                    "controller": controller,
                    "java_file": rel,
                    "http_method": method,
                    "path": p,
                    "java_method": details["name"],
                    "rust_handler": snake(details["name"]),
                    "permission": perm or "—",
                    "log": log_annotation(anns, group),
                    "return": details["return"],
                    "params": details["params"],
                })
    return rows


# ---------------------------------------------------------------------------
# Mapper XML parsing
# ---------------------------------------------------------------------------

KNOWN_TABLE_WORDS = {"select", "from", "where", "join", "into", "update", "set", "values", "dual", "as", "on"}


def parse_mapper_xml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    ns = re.search(r'namespace\s*=\s*"([^"]+)"', text)
    statements = re.findall(r"<(select|insert|update|delete)\b[^>]*\bid=\"([^\"]+)\"", text)
    tables = set()
    for m in re.finditer(r"\b(?:from|join|into|update)\s+([A-Za-z_][\w]*)", text, re.I):
        t = m.group(1).lower()
        if t not in KNOWN_TABLE_WORDS and not t.startswith("${"):
            tables.add(t)
    dynamics = {tag: len(re.findall(r"<%s\b" % tag, text)) for tag in ["if", "foreach", "choose", "when", "where", "set", "trim"]}
    return {
        "path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "namespace": ns.group(1) if ns else "",
        "statements": statements,
        "tables": sorted(tables),
        "dynamics": {k: v for k, v in dynamics.items() if v},
        "result_maps": len(re.findall(r"<resultMap\b", text)),
        "sql_fragments": len(re.findall(r"<sql\b", text)),
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def collect_files() -> List[dict]:
    rows = []
    for module in MODULES:
        root = PROJECT_ROOT / module / "src" / "main" / "java"
        for path in sorted(root.rglob("*.java")):
            rel = str(path.relative_to(root)).replace("\\", "/")
            name = path.name
            role, kind = classify(rel, name)
            rows.append({
                "module": module,
                "java": "%s/src/main/java/%s" % (module, rel),
                "role": role,
                "kind": kind,
                "rust": rust_target(module, rel, name),
            })
    return rows


def md_escape(s: str) -> str:
    return s.replace("|", "\\|")


def write_file_map(files: List[dict]) -> None:
    lines = ["# 附录 A：Java → Rust 文件映射清单", "",
             "> 由 `tools/gen_baseline.py` 生成。Rust 侧遵循 snake_case，模块按原包镜像；",
             "> `（与实现合并）` 表示该 Java 接口与唯一实现合并为一个 Rust 模块（原项目没有多实现，不为测试强造 trait）。", ""]
    by_module = OrderedDict((m, [f for f in files if f["module"] == m]) for m in MODULES)
    lines.append("## 统计")
    lines.append("")
    lines.append("| 模块 | Java 文件数 | 纯逻辑 | 框架契约 | 混合 |")
    lines.append("|---|---:|---:|---:|---:|")
    for m, rows in by_module.items():
        c = Counter(r["kind"] for r in rows)
        lines.append("| %s | %d | %d | %d | %d |" % (m, len(rows), c["纯逻辑"], c["框架契约"], c["混合"]))
    lines.append("| **合计** | **%d** | | | |" % len(files))
    lines.append("")
    for m, rows in by_module.items():
        lines.append("## %s（%d）" % (m, len(rows)))
        lines.append("")
        lines.append("| Java | 职责 | 类型 | Rust 目标 |")
        lines.append("|---|---|---|---|")
        for r in rows:
            lines.append("| `%s` | %s | %s | `%s` |" % (md_escape(r["java"]), r["role"], r["kind"], md_escape(r["rust"])))
        lines.append("")
    (OUT / "01-file-map.md").write_text("\n".join(lines), encoding="utf-8")


def write_endpoints(endpoints: List[dict]) -> None:
    lines = ["# 附录 B：HTTP 接口清单（%d 条）" % len(endpoints), "",
             "> 由 `tools/gen_baseline.py` 复用 `car-monit-py/scripts/audit_endpoints.py` 的 Java 解析器生成。",
             "> 与 Python 迁移的审计口径一致：类级前缀 + 方法级映射 + 权限点。",
             "> `参数` 列只列非框架参数；`framework` 参数（HttpServletResponse 等）在说明中统一处理。",
             "> 返回 `Rust handler` 为计划的 handler 函数名（snake_case），实际路由注册名以 `src/api/**` 为准。", ""]
    by_slice = defaultdict(list)
    for e in endpoints:
        parts = e["java_file"].split("/web/controller/")
        if len(parts) == 2:
            slice_name = parts[1].rsplit("/", 1)[0].split("/")[0]
        elif "/quartz/controller/" in e["java_file"]:
            slice_name = "quartz"
        elif "/generator/controller/" in e["java_file"]:
            slice_name = "generator"
        else:
            slice_name = "other"
        by_slice[slice_name].append(e)
    lines.append("## 切片统计")
    lines.append("")
    lines.append("| 切片 | 控制器 | 端点 |")
    lines.append("|---|---:|---:|")
    for s in sorted(by_slice):
        lines.append("| %s | %d | %d |" % (s, len({e["controller"] for e in by_slice[s]}), len(by_slice[s])))
    lines.append("| **合计** | **%d** | **%d** |" % (len({e["controller"] for e in endpoints}), len(endpoints)))
    lines.append("")
    for s in sorted(by_slice):
        lines.append("## %s" % s)
        lines.append("")
        for controller in sorted({e["controller"] for e in by_slice[s]}):
            rows = [e for e in by_slice[s] if e["controller"] == controller]
            lines.append("### %s（%d）" % (controller, len(rows)))
            lines.append("")
            lines.append("`%s`" % rows[0]["java_file"])
            lines.append("")
            lines.append("| # | Method | Path | Java 方法 → Rust handler | 权限点 | @Log | 参数 | 返回 |")
            lines.append("|---:|---|---|---|---|---|---|---|")
            for i, e in enumerate(rows, 1):
                ps = []
                for p in e["params"]:
                    if p["kind"] == "framework":
                        continue
                    tag = {"path": "path", "body": "body", "query": "query", "header": "header", "multipart": "file"}[p["kind"]]
                    meta = (" " + p["meta"]) if p["meta"] else ""
                    ps.append("`%s:%s (%s%s)`" % (p["name"], p["type"], tag, meta))
                lines.append("| %d | %s | `%s` | %s → `%s` | %s | %s | %s | `%s` |" % (
                    i, e["http_method"], md_escape(e["path"]), e["java_method"], e["rust_handler"],
                    e["permission"] if e["permission"] == "—" else "`%s`" % e["permission"],
                    e["log"], md_escape("; ".join(ps)) or "—", md_escape(e["return"])))
            lines.append("")
    (OUT / "02-endpoints.md").write_text("\n".join(lines), encoding="utf-8")


def write_data_layer(files: List[dict], mappers: List[dict]) -> None:
    stmt_total = sum(len(m["statements"]) for m in mappers)
    tables = set()
    for m in mappers:
        tables.update(m["tables"])
    table_annotations = set()
    for f in files:
        if f["role"] == "Domain/DTO/VO":
            path = PROJECT_ROOT / f["java"]
            text = path.read_text(encoding="utf-8", errors="replace")
            for t in re.findall(r'@TableName\(\s*"([^"]+)"', text):
                table_annotations.add(t.lower())
    lines = ["# 附录 C：数据层清单", "",
             "> 数据库：MySQL 8.x（JDBC URL 指向 `carmonitdb`，`serverTimezone=GMT+8`）。",
             "> 注意：仓库内**没有完整 DDL**；生产 schema 为既有库。Rust 侧 `migrations/` 仅作为**只读快照/校验**，默认不执行。", "",
             "## 统计", "",
             "| 项 | 值 |", "|---|---:|",
             "| Mapper XML | %d |" % len(mappers),
             "| SQL 语句（select/insert/update/delete） | %d |" % stmt_total,
             "| 出现过的表名（XML 引用） | %d |" % len(tables),
             "| `@TableName` 声明的表 | %d |" % len(table_annotations), ""]
    lines.append("## 表清单")
    lines.append("")
    lines.append("| 表 | 来源 |")
    lines.append("|---|---|")
    for t in sorted(tables | table_annotations):
        src = []
        if t in table_annotations:
            src.append("@TableName")
        if t in tables:
            src.append("Mapper XML")
        lines.append("| `%s` | %s |" % (t, " + ".join(src)))
    lines.append("")
    lines.append("## Mapper 语句明细")
    lines.append("")
    for m in mappers:
        lines.append("### `%s`" % m["path"])
        lines.append("")
        lines.append("- namespace：`%s`" % m["namespace"])
        lines.append("- 语句（%d）：%s" % (len(m["statements"]), ", ".join("`%s:%s`" % (k, i) for k, i in m["statements"]) or "—"))
        lines.append("- 表：%s" % (", ".join("`%s`" % t for t in m["tables"]) or "—"))
        lines.append("- 动态标签：%s" % (", ".join("%s×%d" % (k, v) for k, v in m["dynamics"].items()) or "—"))
        lines.append("- resultMap：%d；`<sql>` 片段：%d" % (m["result_maps"], m["sql_fragments"]))
        lines.append("")
    (OUT / "03-data-layer.md").write_text("\n".join(lines), encoding="utf-8")
    return {"statements": stmt_total, "tables": len(tables | table_annotations)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    files = collect_files()
    endpoints = extract_endpoints()
    mapper_paths = []
    for module in MODULES:
        root = PROJECT_ROOT / module / "src" / "main" / "resources"
        if root.exists():
            mapper_paths.extend(sorted(root.rglob("*Mapper.xml")))
    mappers = [parse_mapper_xml(p) for p in mapper_paths]
    write_file_map(files)
    write_endpoints(endpoints)
    stats = write_data_layer(files, mappers)

    inventory = {
        "java_files": len(files),
        "java_file_roles": dict(Counter(f["role"] for f in files)),
        "java_file_kinds": dict(Counter(f["kind"] for f in files)),
        "endpoints": len(endpoints),
        "endpoints_by_controller": dict(Counter(e["controller"] for e in endpoints)),
        "endpoints_by_slice": dict(Counter(
            (e["java_file"].split("/web/controller/")[1].split("/")[0] if "/web/controller/" in e["java_file"]
             else ("quartz" if "/quartz/" in e["java_file"] else "generator"))
            for e in endpoints)),
        "mapper_xml": len(mappers),
        "mapper_statements": stats["statements"],
        "tables": stats["tables"],
        "test_annotations_or_tests": 0,
    }
    (OUT / "inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(inventory, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
