"""Java <-> Python **响应信封**一致性审计.

用法::

    python scripts/audit_envelopes.py            # 打印差异报告
    python scripts/audit_envelopes.py --json     # 输出机器可读结果

为什么需要这一层
----------------
``audit_endpoints.py`` 只比“路由存在不存在”，``audit_domains.py`` 只比“域字段有没有”，
两者都**不看每个接口到底返回什么形状**。而 RuoYi 里有三种信封，字段名和字段顺序都不同：

* ``AjaxResult extends HashMap`` -> ``msg, code, data``（桶序，见 ``java_hash_map.py``）
* ``TableDataInfo``（POJO）    -> ``total, rows, code, msg``
* ``R<T>``（POJO）            -> ``code, msg, data``

一个接口本该返回 ``TableDataInfo`` 却被写成 ``AjaxResult``，路由审计和字段审计都发现不了，
前端拿到的却是**没有 ``rows`` 的分页体**。本脚本就是补这一层：

1. 扫 Java 控制器，取每个映射方法的**声明返回类型**（剥掉泛型）；
2. 导入 Python 应用，取每条路由**处理函数的返回注解**；
3. 按 ``(METHOD, 归一化 PATH)`` 配对，输出「Java 信封 x Python 信封」矩阵，
   并只把**未在允许表里登记过**的组合判为差异。

``ALLOWED`` 里每一对都写了为什么可以不同（都是“写入 response 流”这类没有信封的情况）。
新增例外必须同时改本文件的 ``ALLOWED`` 和 ``COMPATIBILITY.md``，否则回归会红。

“导出”这个例外是**规则判定**而不是白名单
----------------------------------------
本项目里有 24 个导出接口在 Java 里声明成 ``AjaxResult export(..., HttpServletResponse response)``：
方法体把 xlsx 写进 ``response.getOutputStream()``，最后那句 ``return AjaxResult.success("导出成功")``
**根本到不了客户端**（响应已提交，Spring 只能把它当已消费的返回值丢掉）。所以线上真正收到的是
文件流，Python 返回 ``Response`` 才是等价行为。
这里不硬编码这 24 条路径，而是看方法形参里**有没有 ``HttpServletResponse`` / ``OutputStream``**——
这样以后新增的 ``AjaxResult`` 接口如果误返回 ``Response``（真 bug），依然会被揪出来。
"""

from __future__ import annotations

import argparse
import inspect
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audit_endpoints as base  # noqa: E402  -- 复用它的注解分组 / 路径归一化实现

#: Java 方法声明。``R<List<UserEntity>>`` 这种嵌套泛型里没有括号，可以一次吃完。
_SIGNATURE = re.compile(
    r"\b(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?"
    r"([\w.]+(?:\s*<[^(){};=]*>)?)\s+(\w+)\s*\("
)

#: 「Java 信封 -> 允许的 Python 信封集合」。值里的 ``None`` / ``?`` 表示“没有返回值注解”。
ALLOWED: Dict[str, Tuple[str, ...]] = {
    "AjaxResult": ("AjaxResult",),
    "TableDataInfo": ("TableDataInfo",),
    "R": ("R",),
    # 直接写 HttpServletResponse / 返回文件流：Java 是 void，Python 必须显式返回 Response
    "void": ("Response", "None", "?"),
    # SysIndexController#index 返回一句欢迎语（Spring 当视图名/纯文本处理）
    "String": ("str", "Response", "?"),
    # 导入模板的表头/规则：Java 返回 List<ImportEntity>，由 Jackson 直接序列化成数组
    "List": ("list", "List", "?"),
}

#: 形参里出现这些类型 = 方法**自己**往响应流里写东西，返回值不是信封。
STREAM_ARGUMENTS = ("HttpServletResponse", "OutputStream")


def normalize_envelope(text: str) -> str:
    """``R<List<UserEntity>>`` -> ``R``；``List[ImportEntity]`` -> ``List``."""

    plain = re.sub(r"\s+", "", str(text))
    plain = re.sub(r"<.*$", "", plain)
    plain = re.sub(r"\[.*$", "", plain)
    return plain


@dataclass
class JavaEnvelope:
    """一条 Java 映射 + 它的声明返回类型."""

    controller: str
    method: str
    path: str
    java_method: str
    envelope: str
    #: 形参里带 ``HttpServletResponse`` / ``OutputStream`` —— 返回值是“写完之后的那句话”，不到客户端
    writes_stream: bool = False

    @property
    def key(self) -> Tuple[str, str]:
        return (self.method, base.normalize_path(self.path))


@dataclass
class Report:
    """审计结果."""

    java: List[JavaEnvelope] = field(default_factory=list)
    python: Dict[Tuple[str, str], str] = field(default_factory=dict)

    @property
    def comparable(self) -> List[JavaEnvelope]:
        return [item for item in self.java if item.key in self.python]

    @property
    def unmatched(self) -> List[JavaEnvelope]:
        return [item for item in self.java if item.key not in self.python]

    @property
    def mismatched(self) -> List[Tuple[JavaEnvelope, str]]:
        found: List[Tuple[JavaEnvelope, str]] = []
        for item in self.comparable:
            if self.is_allowed(item, self.python[item.key]):
                continue
            found.append((item, self.python[item.key]))
        return found

    @staticmethod
    def is_allowed(item: JavaEnvelope, python_envelope: str) -> bool:
        """Java 信封与 Python 信封是否等价（规则判定，见模块 ``ALLOWED``）."""

        allowed = ALLOWED.get(item.envelope, (item.envelope,))
        if python_envelope in allowed:
            return True
        # 导出：Java 声明 AjaxResult，但形参里有 response，产物是文件流 -> Python 返回 Response
        return item.writes_stream and item.envelope == "AjaxResult" and python_envelope == "Response"

    def matrix(self) -> List[Tuple[str, str, int]]:
        counts: Dict[Tuple[str, str], int] = {}
        for item in self.comparable:
            pair = (item.envelope, self.python[item.key])
            counts[pair] = counts.get(pair, 0) + 1
        return sorted(
            ((java, python_envelope, total) for (java, python_envelope), total in counts.items()),
            key=lambda row: (-row[2], row[0], row[1]),
        )


def iter_java_envelopes(source: str, controller: str) -> Iterable[JavaEnvelope]:
    """一条控制器源码 -> ``(映射, 返回类型)`` 序列（与 ``audit_endpoints`` 同口径）."""

    cleaned = base.strip_comments(source)
    annotations = base.iter_annotations(cleaned)
    prefix, class_index = base._find_class_mapping(cleaned, annotations)

    for index, annotation in enumerate(annotations):
        if annotation.name not in base.MAPPING_METHODS and annotation.name != "RequestMapping":
            continue
        if index == class_index:
            continue

        methods = (
            [base.MAPPING_METHODS[annotation.name]]
            if annotation.name != "RequestMapping"
            else base.parse_request_methods(annotation.args)
        )
        group = base._annotation_group(cleaned, annotations, index)
        after = max(annotations[item].end for item in group)
        match = _SIGNATURE.search(cleaned[after:])
        if not match:
            continue
        envelope = normalize_envelope(match.group(1))
        java_method = match.group(2)
        parameters, _ = base._balanced_paren_args(cleaned, after + match.end() - 1)
        writes_stream = any(name in parameters for name in STREAM_ARGUMENTS)
        for suffix in base.parse_mapping_paths(annotation.args):
            path = f"{prefix}{suffix}" or "/"
            if not path.startswith("/"):
                path = "/" + path
            for method in methods:
                yield JavaEnvelope(
                    controller=controller,
                    method=method,
                    path=path,
                    java_method=java_method,
                    envelope=envelope,
                    writes_stream=writes_stream,
                )


def collect_java() -> List[JavaEnvelope]:
    envelopes: List[JavaEnvelope] = []
    for directory in base.JAVA_SOURCES:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*Controller.java")):
            source = path.read_text(encoding="utf-8", errors="replace")
            envelopes.extend(iter_java_envelopes(source, path.stem))
    return envelopes


def _python_envelope(endpoint: object) -> str:
    """处理函数 ``-> AjaxResult`` 里的那个名字（取不到注解则记 ``?``）."""

    try:
        annotation = inspect.signature(endpoint).return_annotation  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "?"
    if annotation is inspect.Signature.empty:
        return "?"
    if isinstance(annotation, str):
        return normalize_envelope(annotation) or "?"
    return getattr(annotation, "__name__", None) or normalize_envelope(str(annotation)) or "?"


def collect_python() -> Dict[Tuple[str, str], str]:
    sys.path.insert(0, str(base.PY_ROOT))
    from app.main import create_app  # noqa: PLC0415 -- 需要 sys.path 先就位

    application = create_app()
    routes: Dict[Tuple[str, str], str] = {}
    for route in application.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        if not path.startswith("/"):
            continue
        for method in sorted(methods):
            if method in {"HEAD", "OPTIONS"}:
                continue
            routes[(method, base.normalize_path(path))] = _python_envelope(route.endpoint)
    return routes


def build_report() -> Report:
    return Report(java=collect_java(), python=collect_python())


def render(report: Report) -> str:
    lines: List[str] = []
    lines.append(f"Java 端点 : {len(report.java)}")
    lines.append(f"Python 路由: {len(report.python)}")
    lines.append(f"可比（两边都有）: {len(report.comparable)}")
    lines.append(f"无法配对（路由缺失，见 audit_endpoints）: {len(report.unmatched)}")
    lines.append("")

    lines.append("== 信封组合矩阵（Java -> Python 条数） ==")
    for java_envelope, python_envelope, total in report.matrix():
        allowed = any(
            report.is_allowed(item, python_envelope)
            for item in report.comparable
            if item.envelope == java_envelope and report.python[item.key] == python_envelope
        )
        lines.append(
            f"  {'OK ' if allowed else '!! '} {java_envelope:14s} -> {python_envelope:14s} {total:4d}"
        )
    lines.append("")

    if report.mismatched:
        lines.append("== 信封不一致（必须逐条解释） ==")
        for item, python_envelope in report.mismatched:
            lines.append(
                f"  {item.method:6s} {item.path}: Java={item.envelope} "
                f"Python={python_envelope}   ({item.controller}#{item.java_method})"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="输出 JSON 而不是报告文本")
    arguments = parser.parse_args()

    report = build_report()

    if arguments.json:
        payload = {
            "java": len(report.java),
            "python": len(report.python),
            "comparable": len(report.comparable),
            "matrix": [
                {"java": java, "python": python_envelope, "count": total}
                for java, python_envelope, total in report.matrix()
            ],
            "mismatched": [
                {
                    "controller": item.controller,
                    "method": item.method,
                    "path": item.path,
                    "javaMethod": item.java_method,
                    "javaEnvelope": item.envelope,
                    "pythonEnvelope": python_envelope,
                }
                for item, python_envelope in report.mismatched
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(report))

    return 1 if report.mismatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
