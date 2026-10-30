"""Java <-> Python 接口清单一致性审计.

用法::

    python scripts/audit_endpoints.py            # 打印差异报告
    python scripts/audit_endpoints.py --json     # 输出机器可读结果

做的事
------
1. 扫描 Java 侧全部 ``*Controller.java``（``ruoyi-admin`` + ``ruoyi-quartz``），
   剥掉注释后提取：
   * 类级 ``@RequestMapping("<prefix>")``
   * 方法级 ``@GetMapping/@PostMapping/@PutMapping/@DeleteMapping/@PatchMapping``
     以及方法级 ``@RequestMapping`` 的路径与 HTTP 方法
   * 方法上的 ``@PreAuthorize("@ss.hasPermi('x:y:z')")``
2. 导入 ``app.main.create_app()`` 拿到 Python 侧**实际注册**的全部路由。
3. 两边按 ``(METHOD, PATH)`` 求差集，输出：
   * Java 有、Python 没有 —— **缺失**（必须补）
   * Python 有、Java 没有 —— **多余**（多为有意为之，见备注）
   * 权限点对不上 —— **权限差异**

路径归一化
----------
Java 的 ``{jobId}`` 与 Python 的 ``{job_id}`` 只是参数名不同，比较时统一成
``{}``，否则几乎每条都会报差异。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = PROJECT_ROOT / "car-monit-py"
JAVA_SOURCES = (
    PROJECT_ROOT / "ruoyi-admin" / "src" / "main" / "java" / "com" / "ruoyi" / "web" / "controller",
    PROJECT_ROOT / "ruoyi-quartz" / "src" / "main" / "java" / "com" / "ruoyi" / "quartz" / "controller",
    PROJECT_ROOT / "ruoyi-generator" / "src" / "main" / "java" / "com" / "ruoyi" / "generator" / "controller",
)

#: Spring 的映射注解 -> HTTP 方法（``RequestMapping`` 另行解析 ``method =``）。
MAPPING_METHODS = {
    "GetMapping": "GET",
    "PostMapping": "POST",
    "PutMapping": "PUT",
    "DeleteMapping": "DELETE",
    "PatchMapping": "PATCH",
}

ARGUMENT_TYPES = (
    "HttpServletResponse",
    "HttpServletRequest",
    "MultipartFile",
    "OutputStream",
)
_PERMISSION_IN_ARGS = re.compile(r"@ss\.hasPermi\(\s*'([^']+)'\s*\)")
_ANNOTATION_TOKEN = re.compile(r"@(\w+)")

#: 方法声明（用来从注解位置往后找出方法名）
_METHOD_SIGNATURE = re.compile(
    r"\b(?:public|private|protected)\s+(?:static\s+)?[\w<>\[\],.\s]+?\s+(\w+)\s*\("
)


@dataclass
class Annotation:
    """一个 ``@Xxx(args)`` 的出现位置."""

    name: str
    args: str
    start: int
    end: int


@dataclass
class JavaEndpoint:
    """一条 Java 映射."""

    controller: str
    method: str
    path: str
    java_method: str
    permission: Optional[str] = None

    @property
    def key(self) -> Tuple[str, str]:
        return (self.method, normalize_path(self.path))


@dataclass
class AuditReport:
    """审计结果."""

    java: List[JavaEndpoint] = field(default_factory=list)
    python: List[Tuple[str, str]] = field(default_factory=list)
    python_permissions: Dict[Tuple[str, str], Optional[str]] = field(default_factory=dict)

    @property
    def missing(self) -> List[JavaEndpoint]:
        known = set(self.python)
        return sorted(
            (endpoint for endpoint in self.java if endpoint.key not in known),
            key=lambda item: (item.path, item.method),
        )

    @property
    def extra(self) -> List[Tuple[str, str]]:
        declared = {endpoint.key for endpoint in self.java}
        return sorted((item for item in self.python if item not in declared), key=lambda i: (i[1], i[0]))


def normalize_path(path: str) -> str:
    """把 ``{jobId}`` / ``{job_id}`` 统一成 ``{}``，并去掉重复斜杠."""

    collapsed = re.sub(r"\{[^}]*\}", "{}", path)
    collapsed = re.sub(r"/+", "/", collapsed)
    return collapsed.rstrip("/") or "/"


def strip_comments(source: str) -> str:
    """去掉 ``//`` 与 ``/* */`` 注释（字符串 / 字符字面量原样保留）.

    不能"先正则删块注释"：本项目里 ``//** xx *//*`` 这种**行注释末尾带 ``/*``**
    的写法很常见（代码生成器产物）。正则版会把行尾那个 ``/*`` 当成块注释开头，
    一路吃到下一个 ``*/``，把中间整个字段声明当注释删掉——实测
    ``ZdataTrailTracks`` 会莫名少掉 5 个字段。这里改成一次线性扫描，注释内容
    用空格顶替、**保留换行**，使行号与列位置和原文一致。
    """

    pieces: List[str] = []
    index = 0
    length = len(source)
    while index < length:
        char = source[index]
        if char in "\"'":
            end = _skip_string(source, index)
            pieces.append(source[index:end])
            index = end
            continue
        if char == "/" and index + 1 < length:
            following = source[index + 1]
            if following == "/":
                end = source.find("\n", index)
                end = length if end < 0 else end
                pieces.append(" " * (end - index))
                index = end
                continue
            if following == "*":
                end = source.find("*/", index + 2)
                end = length if end < 0 else end + 2
                pieces.append(re.sub(r"[^\n]", " ", source[index:end]))
                index = end
                continue
        pieces.append(char)
        index += 1
    return "".join(pieces)


def _skip_string(source: str, start: int) -> int:
    """``start`` 处是一个引号 -> 返回字符串结束后的下标（处理反斜杠转义）."""

    quote = source[start]
    index = start + 1
    while index < len(source):
        char = source[index]
        if char == "\\":
            index += 2
            continue
        if char == quote:
            return index + 1
        index += 1
    return len(source)


def _balanced_paren_args(source: str, start: int) -> Tuple[str, int]:
    r"""从 ``@Anno`` 之后取出括号内的参数文本，返回 ``(args, end_offset)``.

    正则 ``\([^)]*\)`` 遇到 ``@PreAuthorize("@ss.hasPermi('a:b:c')")`` 会在内层
    ``)`` 处提前断开，导致只能拿到半个参数串；这里按括号配平扫描，并且**跳过
    字符串字面量**（权限串里的 ``')`` 不能参与配平）。
    """

    cursor = start
    while cursor < len(source) and source[cursor] in " \t\r\n":
        cursor += 1
    if cursor >= len(source) or source[cursor] != "(":
        return "", start
    depth = 0
    index = cursor
    while index < len(source):
        char = source[index]
        if char in "\"'":
            index = _skip_string(source, index)
            continue
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[cursor + 1 : index], index + 1
        index += 1
    return source[cursor + 1 :], len(source)


def iter_annotations(source: str) -> List["Annotation"]:
    r"""把源码里所有 ``@Xxx(...)`` 扫成一个列表（位置连续，便于按相邻性分组）.

    必须自己手扫而不只是 ``re.finditer(r"@(\w+)")``：``@PreAuthorize`` 的**参数里**
    就有 ``@ss.hasPermi(...)``，正则扫描会把那个 ``@ss`` 也当成一个注解，夹杂在
    外层注解之间破坏“相邻性”判断（进而再也找不到权限串）。
    """

    annotations: List[Annotation] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char in "\"'":
            index = _skip_string(source, index)
            continue
        if char == "@":
            match = _ANNOTATION_TOKEN.match(source, index)
            if match:
                args, end = _balanced_paren_args(source, match.end())
                annotations.append(
                    Annotation(name=match.group(1), args=args, start=match.start(), end=end)
                )
                index = end
                continue
        index += 1
    return annotations


def _annotation_group(source: str, annotations: List["Annotation"], index: int) -> List[int]:
    """取与第 ``index`` 个注解**紧邻**（中间只有空白）的全部注解下标.

    同一个方法的注解在源码里必定连续，而前一个方法的最后一个注解与它之间隔着
    ``}`` / ``;`` / 方法体，因此“中间只有空白”就是同组的充要条件。向**两个方向**
    都贪心吸收，因为 RuoYi 里 ``@PreAuthorize`` 有时写在 ``@XxxMapping`` 之前、
    有时写在之后。
    """

    group = [index]
    cursor = annotations[index].end
    for other in range(index + 1, len(annotations)):
        item = annotations[other]
        if source[cursor : item.start].strip():
            break
        group.append(other)
        cursor = item.end
    cursor = annotations[index].start
    for other in range(index - 1, -1, -1):
        item = annotations[other]
        if source[item.end : cursor].strip():
            break
        group.append(other)
        cursor = item.start
    return group


def parse_mapping_paths(args: str) -> List[str]:
    """``"/list"`` / ``value = "/{id}"`` / ``value = {"/", "/{userId}"}`` -> 路径列表.

    Spring 允许一个注解挂多条路径（``@GetMapping(value = {"/", "/{userId}"}``），
    ``SysUserController#getInfo`` 就靠这个同时占住两条；只取第一条会凭空报出
    "Python 多余 ``/system/user/{}``"。无参 -> ``[""]``（即类级前缀本身）。

    注意不能直接搜所有引号串：``@GetMapping("/{id}")`` 里的 ``{id}`` 是大括号开头，
    但真正的数组形式是 ``{"``（大括号紧跟引号），两者靠这个区分。
    """

    if not args.strip():
        return [""]
    array_start = re.search(r'\{\s*"', args)
    if array_start:
        depth = 0
        for index in range(array_start.start(), len(args)):
            if args[index] == "{":
                depth += 1
            elif args[index] == "}":
                depth -= 1
                if depth == 0:
                    body = args[array_start.start() : index + 1]
                    return re.findall(r'"([^"]*)"', body) or [""]
    found = re.findall(r'"([^"]*)"', args)
    return found[:1] or [""]


def parse_request_methods(args: str) -> List[str]:
    """``method = RequestMethod.PUT`` -> ``["PUT"]``；未声明 -> 全部方法.

    Java 的 ``@RequestMapping`` 不带 ``method`` 时匹配**所有** HTTP 方法
    （``SysIndexController#index`` 就是如此）；退化成 ``GET`` 会把
    ``POST/PUT/DELETE/PATCH /`` 误判成「Python 多余」。
    """

    found = re.findall(r"RequestMethod\.(\w+)", args)
    if found:
        return found
    # Starlette 会给每条 GET 路由自动附加 HEAD，如果比到 HEAD 会出现 480 条假差异；
    # OPTIONS 则被 CORS 中间件接管。两侧统一不比这两个方法。
    return ["GET", "POST", "PUT", "DELETE", "PATCH"]


def _find_class_mapping(
    source: str, annotations: List["Annotation"]
) -> Tuple[str, Optional[int]]:
    """定位**类级** ``@RequestMapping``，返回 ``(前缀, 该注解下标)``.

    不能简单地用 ``re.search("@RequestMapping")`` 取第一条：``SysIndexController``
    没有类级注解，方法上的 ``@RequestMapping("/")`` 会被误当成类前缀，从而把
    首页 ``/`` 整条丢掉。判定标准是“类声明之前的*最后*一个 ``@RequestMapping``”。
    """

    declaration = re.search(r"\bclass\s+\w+", source)
    if not declaration:
        return "", None
    class_index: Optional[int] = None
    for index, annotation in enumerate(annotations):
        if annotation.start > declaration.start():
            break
        if annotation.name == "RequestMapping":
            class_index = index
    if class_index is None:
        return "", None
    return parse_mapping_paths(annotations[class_index].args)[0], class_index


def iter_java_endpoints(source: str, controller: str) -> Iterable[JavaEndpoint]:
    """一条控制器源码 -> 它的全部映射."""

    cleaned = strip_comments(source)
    annotations = iter_annotations(cleaned)
    prefix, class_index = _find_class_mapping(cleaned, annotations)

    for index, annotation in enumerate(annotations):
        if annotation.name not in MAPPING_METHODS and annotation.name != "RequestMapping":
            continue
        # 类级 @RequestMapping 由 prefix 接管，跳过
        if index == class_index:
            continue

        methods = (
            [MAPPING_METHODS[annotation.name]]
            if annotation.name != "RequestMapping"
            else parse_request_methods(annotation.args)
        )
        group = _annotation_group(cleaned, annotations, index)
        after = max(annotations[item].end for item in group)
        java_method = _enclosing_method(cleaned, after)
        permission = _permission_in_group(annotations, group)
        for suffix in parse_mapping_paths(annotation.args):
            path = f"{prefix}{suffix}" or "/"
            if not path.startswith("/"):
                path = "/" + path
            for method in methods:
                yield JavaEndpoint(
                    controller=controller,
                    method=method,
                    path=path,
                    java_method=java_method,
                    permission=permission,
                )


def _enclosing_method(source: str, offset: int) -> str:
    match = _METHOD_SIGNATURE.search(source[offset:])
    return match.group(1) if match else "?"


def _permission_in_group(annotations: List["Annotation"], group: List[int]) -> Optional[str]:
    """同一方法注解组里 ``@PreAuthorize("@ss.hasPermi('x')")`` 的权限串."""

    for item in group:
        annotation = annotations[item]
        if annotation.name != "PreAuthorize":
            continue
        found = _PERMISSION_IN_ARGS.findall(annotation.args)
        if found:
            return found[0]
    return None


def collect_java() -> List[JavaEndpoint]:
    endpoints: List[JavaEndpoint] = []
    for directory in JAVA_SOURCES:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*Controller.java")):
            source = path.read_text(encoding="utf-8", errors="replace")
            endpoints.extend(iter_java_endpoints(source, path.stem))
    return endpoints


def collect_python() -> "tuple[List[Tuple[str, str]], Dict[Tuple[str, str], Optional[str]]]":
    """导入应用，取实际注册的路由（含权限装饰器里声明的权限点）."""

    sys.path.insert(0, str(PY_ROOT))
    from app.main import create_app  # noqa: PLC0415 -- 需要 sys.path 先就位

    application = create_app()
    routes: List[Tuple[str, str]] = []
    permissions: Dict[Tuple[str, str], Optional[str]] = {}

    for route in application.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", None) or set()
        if not path.startswith("/"):
            continue
        for method in sorted(methods):
            if method in {"HEAD", "OPTIONS"}:
                continue
            key = (method, normalize_path(path))
            routes.append(key)
            permissions[key] = getattr(route.endpoint, "__permi__", None)

    return routes, permissions


def build_report() -> AuditReport:
    java = collect_java()
    python, permissions = collect_python()
    return AuditReport(java=java, python=python, python_permissions=permissions)


def render(report: AuditReport) -> str:
    lines: List[str] = []
    lines.append(f"Java 映射数 : {len(report.java)}")
    lines.append(f"Python 路由数: {len(report.python)}")
    lines.append("")

    declaring = {endpoint.key for endpoint in report.java}
    covered = declaring & set(report.python)
    lines.append(f"两边都有      : {len(covered)}")
    lines.append(f"Java 有/Python 无: {len(report.missing)}")
    lines.append(f"Python 有/Java 无: {len(report.extra)}")
    lines.append("")

    if report.missing:
        lines.append("== 缺失（必须补） ==")
        by_controller: Dict[str, List[JavaEndpoint]] = {}
        for endpoint in report.missing:
            by_controller.setdefault(endpoint.controller, []).append(endpoint)
        for controller in sorted(by_controller):
            lines.append(f"  {controller}")
            for endpoint in by_controller[controller]:
                lines.append(f"    {endpoint.method:6s} {endpoint.path}   ({endpoint.java_method})")
        lines.append("")

    if report.extra:
        lines.append("== 多余（Python 有、Java 没有） ==")
        for method, path in report.extra:
            lines.append(f"  {method:6s} {path}")
        lines.append("")

    mismatched = []
    for endpoint in report.java:
        if endpoint.key not in report.python_permissions:
            continue
        python_permission = report.python_permissions[endpoint.key]
        if endpoint.permission != python_permission:
            mismatched.append((endpoint, python_permission))
    if mismatched:
        lines.append("== 权限点不一致 ==")
        for endpoint, python_permission in mismatched:
            lines.append(
                f"  {endpoint.method:6s} {endpoint.path}: "
                f"Java={endpoint.permission!r} Python={python_permission!r}"
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
            "missing": [
                {
                    "controller": item.controller,
                    "method": item.method,
                    "path": item.path,
                    "javaMethod": item.java_method,
                }
                for item in report.missing
            ],
            "extra": [{"method": method, "path": path} for method, path in report.extra],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(render(report))

    return 1 if report.missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
