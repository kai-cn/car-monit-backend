"""Java 域对象 <-> Python 模型的字段一致性审计.

用法::

    python scripts/audit_domains.py            # 打印差异报告
    python scripts/audit_domains.py --json     # 输出机器可读结果

为什么要比"getter"而不是"字段"
------------------------------
Jackson 序列化 bean 靠的是 **getter**（``getFoo()`` -> ``"foo"``，``isFoo()`` ->
``"foo"``），不是字段。两者在本项目里几乎总是一一对应，但差一点也不行：

* ``BaseEntity.getParams()`` 有 ``@JsonInclude(NON_EMPTY)``，空 Map 不输出；
* ``SysJob.getNextValidTime()`` **没有对应字段**，是算出来的，前端靠它显示下次执行时间；
* ``SysUser.isAdmin()`` 会把 ``admin`` 一起吐出去；
* ``BaseEntity.searchValue`` / ``SysUser.password`` 挂着 ``@JsonIgnore``，不输出。

所以这里解析 ``public X getY()`` / ``public boolean isY()``（**无参**、非 static），
再把继承链上的 getter 一并并进来 —— 与 Jackson 的 ``BeanSerializer`` 走法一致。

Excel 列序
----------
``ExcelUtil#getFields()`` 先父类后子类地取 ``getDeclaredFields()``，再按 ``@Excel.sort``
做**稳定**排序。本项目没有任何字段显式声明 ``sort``，因此导出列序 = 声明顺序。
顺序不同会让 xlsx 的列整体错位，比"字段少一个"更隐蔽，所以一并比对。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = PROJECT_ROOT / "car-monit-py"

#: 复用接口审计脚本里已经写好的 Java 注释剥离 / 注解扫描（同一套规则，避免两份实现漂移）。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_endpoints import iter_annotations, strip_comments  # noqa: E402

#: Java 侧参与比对的目录：``domain``（含子包）、``entity``、``model``.
JAVA_DOMAIN_GLOBS = (
    "**/src/main/java/**/domain/**/*.java",
    "**/src/main/java/**/entity/*.java",
    "**/src/main/java/**/model/*.java",
)

#: Python 侧要导入的包（每个包里都可能定义 DomainModel 子类）。
PYTHON_PACKAGES = (
    "app.common.core.domain",
    "app.common.core.domain.entity",
    "app.common.core.domain.model",
    "app.base.domain",
    "app.system.domain",
    "app.manager.domain",
    "app.flow.domain",
    "app.quartz.domain",
    "app.framework.web.domain",
    "app.generator.domain",
)

_CLASS_DECL = re.compile(r"\bclass\s+(\w+)\s*(?:extends\s+([\w.]+))?")
_GETTER = re.compile(
    r"\bpublic\s+(?!static\b)([\w<>\[\],.\s?]+?)\s+(get|is)([A-Z]\w*)\s*\(\s*\)"
)
#: Lombok 自动生成 getter/setter —— 类上有这些注解时，属性 = 字段
_LOMBOK = re.compile(r"@(Data|Getter|Value|Accessors)\b")
_FIELD_DECL = re.compile(
    r"\b(?:private|protected|public)\s+(?!static\b)(?:final\s+)?(?:transient\s+)?"
    r"([\w<>\[\],.\s?]+?)\s+(\w+)\s*(?:=[^;]*)?;"
)
#: **包级私有**字段（``@Data`` 类里很常见：``List<String> sectionCodeList;`` 前面什么修饰符都没有）。
#: 只认行首的 ``类型 名字;``，顺带用关键字黑名单排除 ``return x;`` 这类语句。
_BARE_FIELD_DECL = re.compile(
    r"(?m)^[ \t]*(?!return\b|throw\b|new\b|else\b|case\b|break\b|continue\b)"
    r"((?:[A-Za-z_$][\w$]*)(?:\s*<[^;(){}]*>)?(?:\s*\[\s*\])*)\s+"
    r"([A-Za-z_$]\w*)\s*(?:=[^;]*)?;"
)
_INNER_EXCEL = re.compile(r"@Excel\s*\((.*?)\)\s*[,}]", re.DOTALL)
_EXCEL_NAME = re.compile(r'name\s*=\s*"([^"]*)"')

#: ``new ExcelUtil<X>(X.class)`` —— 真正会把 ``@Excel`` 列导出的地方。
#: 注释掉的导出（本项目有 5 处）先剥注释自然就排除了。
_EXCEL_UTIL = re.compile(r"new\s+ExcelUtil\s*<\s*(\w+)\s*>")

#: ```@Excel`` 里"只导出不导入"的字段在 Python 侧也要带同样的 type，这里不比对。
_BOOLEAN_TYPES = {"boolean", "Boolean"}


@dataclass
class JavaBean:
    """一个 Java 域对象对外暴露的属性（按 Jackson 的规则算出）."""

    name: str
    source: str
    extends: Optional[str] = None
    lombok: bool = False
    properties: List[str] = field(default_factory=list)
    excel: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class PythonModel:
    """一个 Python 模型对外暴露的属性."""

    name: str
    module: str
    properties: List[str] = field(default_factory=list)
    excel: List[Tuple[str, str]] = field(default_factory=list)
    #: ``model_fields`` 的原始键（snake_case），给 ``gen_excel_fields.py`` 换算属性名用
    fields: List[str] = field(default_factory=list)


def camel_to_snake(name: str) -> str:
    """``invokeTarget`` -> ``invoke_target``；``pjFlag`` -> ``pj_flag``."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def snake_to_camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def decapitalize(name: str) -> str:
    """JavaBeans 的 ``Introspector.decapitalize``：``URL`` 保持不变，``Foo`` -> ``foo``."""
    if len(name) > 1 and name[0].isupper() and name[1].isupper():
        return name
    return name[:1].lower() + name[1:]


def parse_java_bean(path: Path) -> Optional[JavaBean]:
    """一个 ``.java`` 文件 -> 它的主类（不是 bean 的返回 ``None``）."""

    raw = path.read_text(encoding="utf-8", errors="replace")
    source = strip_comments(raw)
    declaration = _CLASS_DECL.search(source)
    if not declaration:
        return None

    bean = JavaBean(name=declaration.group(1), source=str(path.relative_to(PROJECT_ROOT)))
    bean.extends = declaration.group(2).split(".")[-1] if declaration.group(2) else None
    # Lombok 在编译期为每个字段生成 getter，源码里看不到，所以类上有 @Data 等注解时
    # 只能按**字段**还原属性（本项目大量 manager/base 域对象是 ``@Data`` 风格）。
    bean.lombok = bool(_LOMBOK.search(source[: declaration.start()]))

    annotations = iter_annotations(source)

    # ---- 字段级 @JsonIgnore：整个属性都不输出（BaseEntity.searchValue 就是这种写法）
    ignored_fields: Set[str] = set()
    for index, annotation in enumerate(annotations):
        if annotation.name != "JsonIgnore":
            continue
        following = _FIELD_DECL.search(source, annotation.end)
        if following:
            ignored_fields.add(following.group(2))

    if bean.lombok:
        # 字段顺序 = 源码顺序；有修饰符的与包级私有的各扫一遍再按位置合并。
        declarations = [
            (match.start(), match.group(2)) for match in _FIELD_DECL.finditer(source)
        ] + [
            (match.start(), match.group(2)) for match in _BARE_FIELD_DECL.finditer(source)
        ]
        for _, field_name in sorted(declarations):
            if field_name == "serialVersionUID" or field_name in ignored_fields:
                continue
            if field_name in {item for item in bean.properties}:
                continue
            # Lombok 为 ``TrailDevList`` 生成 ``getTrailDevList()``，Jackson 的
            # ``Introspector.decapitalize`` 再降成 ``trailDevList``——这里保持一致。
            bean.properties.append(decapitalize(field_name))

    # ---- getter（无参、非 static）就是 Jackson 的属性来源
    for match in _GETTER.finditer(source):
        prefix, stem = match.group(2), match.group(3)
        return_type = match.group(1).strip()
        if prefix == "is" and return_type not in _BOOLEAN_TYPES:
            continue
        property_name = decapitalize(stem)
        if camel_to_snake(property_name) in {camel_to_snake(item) for item in ignored_fields}:
            continue
        group = _getter_annotations(source, annotations, match.start())
        if any(item.name == "JsonIgnore" for item in group):
            continue
        renamed = _json_property_name(group)
        if (renamed or property_name) not in bean.properties:
            bean.properties.append(renamed or property_name)

    # ---- @Excel：字段级注解，决定导出列名与列序
    bean.excel = _parse_excel(source, annotations)
    return bean


def _getter_annotations(source: str, annotations: List, offset: int) -> List:
    """``offset`` 之前的、与该 getter 紧邻（中间只有空白）的注解."""

    cursor = offset
    collected = []
    for index in range(len(annotations) - 1, -1, -1):
        annotation = annotations[index]
        if annotation.end > cursor:
            continue
        if source[annotation.end : cursor].strip():
            break
        collected.append(annotation)
        cursor = annotation.start
    return collected


def _json_property_name(annotations: Sequence) -> Optional[str]:
    """``@JsonProperty("x")`` -> ``"x"``；``@JsonProperty`` 无参 -> ``None``."""

    for annotation in annotations:
        if annotation.name != "JsonProperty":
            continue
        found = re.findall(r'"([^"]*)"', annotation.args)
        if found:
            return found[0]
    return None


def _parse_excel(source: str, annotations: List) -> List[Tuple[str, str]]:
    """``@Excel`` / ``@Excels`` -> ``[(字段名, 表头)]``，保持源码顺序."""

    columns: List[Tuple[str, str]] = []
    for annotation in annotations:
        if annotation.name not in ("Excel", "Excels"):
            continue
        bodies = (
            [annotation.args]
            if annotation.name == "Excel"
            else _INNER_EXCEL.findall(annotation.args)
        )
        declaration = _FIELD_DECL.search(source, annotation.end)
        if not declaration:
            continue
        field_name = declaration.group(2)
        for body in bodies:
            header = _EXCEL_NAME.search(body)
            if header:
                columns.append((field_name, header.group(1)))
    return columns


def resolve_inheritance(beans: Dict[str, JavaBean]) -> None:
    """把父类属性/列拼到子类前面（Jackson 与 ``ExcelUtil`` 都是父类优先）."""

    resolved: Dict[str, Tuple[List[str], List[Tuple[str, str]]]] = {}

    def walk(name: str, seen: Tuple[str, ...]) -> Tuple[List[str], List[Tuple[str, str]]]:
        if name in resolved:
            return resolved[name]
        bean = beans[name]
        if not bean.extends or bean.extends not in beans or bean.extends in seen:
            resolved[name] = (list(bean.properties), list(bean.excel))
            return resolved[name]
        parent_properties, parent_excel = walk(bean.extends, seen + (name,))
        resolved[name] = (parent_properties + list(bean.properties), parent_excel + list(bean.excel))
        return resolved[name]

    for name in beans:
        properties, excel = walk(name, ())
        beans[name].properties = properties
        beans[name].excel = excel


def collect_java() -> Dict[str, JavaBean]:
    beans: Dict[str, JavaBean] = {}
    for pattern in JAVA_DOMAIN_GLOBS:
        for path in sorted(PROJECT_ROOT.glob(pattern)):
            if "target" in path.parts:
                continue
            bean = parse_java_bean(path)
            if bean and bean.name not in beans:
                beans[bean.name] = bean
    resolve_inheritance(beans)
    return beans


def collect_python() -> Dict[str, PythonModel]:
    """导入全部 domain 包，收集 **在这里定义** 的 ``DomainModel`` 子类."""

    sys.path.insert(0, str(PY_ROOT))
    import importlib
    import pkgutil

    from app.common.core.domain.domain_model import DomainModel

    models: Dict[str, PythonModel] = {}
    for package_name in PYTHON_PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except Exception:  # noqa: BLE001 - 某个包导入失败不应该让整个审计挂掉
            continue
        for info in pkgutil.walk_packages(package.__path__, prefix=f"{package_name}."):
            # 递归：``app.manager.domain.vo.bigscreen`` 这类子包里的 VO 同样是接口出参
            module = importlib.import_module(info.name)
            for attribute in vars(module).values():
                if (
                    isinstance(attribute, type)
                    and issubclass(attribute, DomainModel)
                    and attribute is not DomainModel
                    and attribute.__module__ == module.__name__
                ):
                    models[attribute.__name__] = _describe_model(attribute, module.__name__)
    return models


def _describe_model(model: type, module: str) -> PythonModel:
    from app.common.annotation.excel import EXCEL_FIELDS_NAME

    described = PythonModel(name=model.__name__, module=module)
    described.fields = list(model.model_fields)
    described.properties = [
        info.alias or name
        for name, info in model.model_fields.items()
        if not info.exclude
    ]
    # ``@computed_field`` 不在 ``model_fields`` 里，但 Java 的对应 getter 同样会输出
    # （``SysJob.nextValidTime``、``SysRole.admin``、``SysUser.admin`` 都是这样）。
    described.properties.extend(
        snake_to_camel(name) if "_" in name else name
        for name in model.model_computed_fields
    )
    described.excel = [
        # Excel 列名比对统一到 Java 的 camelCase：EXCEL_FIELDS 里写的是 Python 属性名。
        (snake_to_camel(attribute), excel.name)
        for attribute, excel in getattr(model, EXCEL_FIELDS_NAME, ())
    ]
    return described


@dataclass
class FieldReport:
    """审计结果."""

    java: Dict[str, JavaBean] = field(default_factory=dict)
    python: Dict[str, PythonModel] = field(default_factory=dict)
    exports: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def matched(self) -> List[str]:
        return sorted(set(self.java) & set(self.python))

    @property
    def java_only(self) -> List[str]:
        return sorted(set(self.java) - set(self.python))

    @property
    def python_only(self) -> List[str]:
        return sorted(set(self.python) - set(self.java))

    @property
    def property_gaps(self) -> Dict[str, Tuple[List[str], List[str]]]:
        gaps: Dict[str, Tuple[List[str], List[str]]] = {}
        for name in self.matched:
            java_keys = set(self.java[name].properties)
            python_keys = set(self.python[name].properties)
            missing = sorted(java_keys - python_keys)
            extra = sorted(python_keys - java_keys)
            if missing or extra:
                gaps[name] = (missing, extra)
        return gaps

    @property
    def excel_gaps(self) -> Dict[str, Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]]:
        """要导出的实体上，Java ``@Excel`` 列与 Python ``EXCEL_FIELDS`` 的差异.

        只比对 **Java 真的会导出**（全项目有 ``new ExcelUtil<X>``）的实体：没被导出的
        实体上摆着 ``@Excel`` 也只是死注解，不会进任何 HTTP 响应或文件，不迁移它
        不构成行为差异（那批实体单独列在 :attr:`excel_unused`）。
        """

        gaps = {}
        for name in self.matched:
            if name not in self.exports and not self.python[name].excel:
                continue
            java_columns = self.java[name].excel
            python_columns = self.python[name].excel
            if java_columns != python_columns:
                gaps[name] = (java_columns, python_columns)
        return gaps

    @property
    def excel_unused(self) -> Dict[str, int]:
        """Java 声明了 ``@Excel`` 但全项目从不导出的实体 -> 列数.

        ``@Excel`` 只被 ``ExcelUtil`` 读，没有 ``new ExcelUtil<X>`` 就永远读不到，
        所以 Python 侧**有意**不搬这些表头。
        """

        return {
            name: len(self.java[name].excel)
            for name in self.matched
            if self.java[name].excel
            and name not in self.exports
            and not self.python[name].excel
        }

    @property
    def export_gaps(self) -> Dict[str, List[str]]:
        """Java 真的会导出、Python 实体却没有 ``EXCEL_FIELDS`` 的类型.

        这种差异不会报错，只会让 xlsx **没有表头**（Java 有），是最隐蔽的一类。
        """

        gaps: Dict[str, List[str]] = {}
        for name, callers in self.exports.items():
            java_bean = self.java.get(name)
            python_model = self.python.get(name)
            if java_bean is None or python_model is None or not java_bean.excel:
                continue
            if not python_model.excel:
                gaps[name] = callers
        return dict(sorted(gaps.items()))


def build_report() -> FieldReport:
    return FieldReport(
        java=collect_java(),
        python=collect_python(),
        exports=collect_exports(),
    )


def collect_exports() -> Dict[str, List[str]]:
    """扫全部 Java 控制器，收集 ``new ExcelUtil<X>`` 用到的实体."""

    found: Dict[str, List[str]] = {}
    for path in sorted(PROJECT_ROOT.glob("ruoyi-*/src/main/java/**/*.java")):
        if "target" in path.parts:
            continue
        source = strip_comments(path.read_text(encoding="utf-8", errors="replace"))
        if "ExcelUtil" not in source:
            continue
        for match in _EXCEL_UTIL.finditer(source):
            found.setdefault(match.group(1), [])
            if path.stem not in found[match.group(1)]:
                found[match.group(1)].append(path.stem)
    return found


def render(report: FieldReport) -> str:
    lines: List[str] = []
    lines.append(f"Java 域对象 : {len(report.java)}")
    lines.append(f"Python 模型 : {len(report.python)}")
    lines.append(f"同名可对比   : {len(report.matched)}")
    lines.append(f"仅 Java 有  : {len(report.java_only)}")
    lines.append(f"仅 Python 有: {len(report.python_only)}")
    lines.append("")

    if report.java_only:
        lines.append("== 仅 Java 有（可能未迁移，也可能只是没被接口用到） ==")
        for name in report.java_only:
            lines.append(f"  {name:48s} {report.java[name].source}")
        lines.append("")

    if report.python_only:
        lines.append("== 仅 Python 有 ==")
        for name in report.python_only:
            lines.append(f"  {name:48s} {report.python[name].module}")
        lines.append("")

    gaps = report.property_gaps
    if gaps:
        lines.append("== JSON 属性差异 ==")
        for name in sorted(gaps):
            missing, extra = gaps[name]
            lines.append(f"  {name}")
            if missing:
                lines.append(f"    Java 有 / Python 无: {', '.join(missing)}")
            if extra:
                lines.append(f"    Python 有 / Java 无: {', '.join(extra)}")
        lines.append("")

    excel = report.excel_gaps
    if excel:
        lines.append("== @Excel 列差异 ==")
        for name in sorted(excel):
            java_columns, python_columns = excel[name]
            lines.append(f"  {name}")
            lines.append(f"    Java  : {_format_columns(java_columns)}")
            lines.append(f"    Python: {_format_columns(python_columns)}")
        lines.append("")

    exports = report.export_gaps
    if exports:
        lines.append("== 导出实体缺 EXCEL_FIELDS（xlsx 会丢表头） ==")
        for name, callers in exports.items():
            lines.append(f"  {name:40s} <- {', '.join(callers)}")
        lines.append("")

    unused = report.excel_unused
    if unused:
        lines.append("== Java 有 @Excel 但从未导出（注解是死代码，Python 有意不搬） ==")
        for name, count in unused.items():
            lines.append(f"  {name:40s} {count} 列")
        lines.append("")

    return "\n".join(lines)


def _format_columns(columns: Iterable[Tuple[str, str]]) -> str:
    return " | ".join(f"{name}:{header}" for name, header in columns) or "(空)"


def main() -> int:
    parser = argparse.ArgumentParser(description="Java/Python 域字段一致性审计")
    parser.add_argument("--json", action="store_true", help="输出 JSON 而不是报告文本")
    parser.add_argument("--output", help="同时写入 UTF-8 文件（Windows 控制台是 GBK，直接打印会崩）")
    arguments = parser.parse_args()

    report = build_report()

    if arguments.json:
        payload = {
            "java": len(report.java),
            "python": len(report.python),
            "matched": len(report.matched),
            "javaOnly": report.java_only,
            "pythonOnly": report.python_only,
            "propertyGaps": {
                name: {"missing": missing, "extra": extra}
                for name, (missing, extra) in report.property_gaps.items()
            },
            "excelGaps": {
                name: {"java": java_columns, "python": python_columns}
                for name, (java_columns, python_columns) in report.excel_gaps.items()
            },
            "exportGaps": report.export_gaps,
            "excelUnused": report.excel_unused,
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = render(report)

    if arguments.output:
        Path(arguments.output).write_text(text, encoding="utf-8")
        print(f"已写入 {arguments.output}")
    else:
        # Windows 控制台默认 GBK，域对象里的表头含 CJK 部首等 GBK 未收录字符，
        # 直接 print 会抛 UnicodeEncodeError；errors="replace" 保证报告总能看完。
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
        print(text)

    return 1 if (report.property_gaps or report.excel_gaps) else 0

if __name__ == "__main__":
    raise SystemExit(main())
