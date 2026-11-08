"""把 Java 域对象上的 ``@Excel`` 注解翻译成 Python 的 ``EXCEL_FIELDS``.

用法::

    python scripts/gen_excel_fields.py --java <Xxx.java> [...]      # 只打印
    python scripts/gen_excel_fields.py --all-gaps                   # 打印全部导出缺口

为什么要有这个脚本
------------------
``@Excel`` 是 **字段级注解**，Python 没有注解，只能把它搬成类变量
``EXCEL_FIELDS``（见 ``app/common/annotation/excel.py``）。手抄 200+ 个表头极易出错，
而漏掉一个 ``EXCEL_FIELDS`` 的后果很隐蔽：接口不报错，导出的 xlsx 只是**没有表头**。
所以这里机械翻译，只保留与 Java 注解默认值不同的属性（默认值见 ``Excel.java``）。

属性名怎么定
------------
Java 的 camelCase 字段名要先换算成 Python 模型的 snake_case 属性名。换算结果会到
对应模型里核对：模型有这个字段就用它，没有就退回 ``camel_to_snake`` 并打 ``# ?``
警告，避免生成一张"表头对但属性名错、导出全空"的表。
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PY_ROOT = PROJECT_ROOT / "car-monit-py"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_domains import camel_to_snake, collect_python, snake_to_camel  # noqa: E402
from audit_endpoints import iter_annotations, strip_comments  # noqa: E402

#: Java 注解属性 -> Python ``Excel`` 属性
ATTRIBUTE_NAMES: Dict[str, str] = {
    "sort": "sort",
    "name": "name",
    "dateFormat": "date_format",
    "dictType": "dict_type",
    "readConverterExp": "read_converter_exp",
    "separator": "separator",
    "scale": "scale",
    "roundingMode": "rounding_mode",
    "height": "height",
    "width": "width",
    "suffix": "suffix",
    "defaultValue": "default_value",
    "prompt": "prompt",
    "combo": "combo",
    "needMerge": "need_merge",
    "isExport": "is_export",
    "targetAttr": "target_attr",
    "isStatistics": "is_statistics",
    "cellType": "cell_type",
    "headerBackgroundColor": "header_background_color",
    "headerColor": "header_color",
    "backgroundColor": "background_color",
    "color": "color",
    "align": "align",
    "handler": "handler",
    "args": "args",
    "type": "type",
}

#: ``Excel.java`` 里的默认值（写成 Python 表达式的样子，用来判断"要不要写出来"）。
DEFAULTS: Dict[str, str] = {
    "sort": "2147483647",
    "name": '""',
    "dateFormat": '""',
    "dictType": '""',
    "readConverterExp": '""',
    "separator": '","',
    "scale": "-1",
    "roundingMode": "6",
    "height": "14",
    "width": "16",
    "suffix": '""',
    "defaultValue": '""',
    "prompt": '""',
    "combo": "()",
    "needMerge": "False",
    "isExport": "True",
    "targetAttr": '""',
    "isStatistics": "False",
    "cellType": "ColumnType.STRING",
    "headerBackgroundColor": "GREY_50_PERCENT",
    "headerColor": "WHITE",
    "backgroundColor": "WHITE",
    "color": "BLACK",
    "align": "HorizontalAlignment.CENTER",
    "handler": "ExcelHandlerAdapter",
    "args": "()",
    "type": "Type.ALL",
}

#: ``BigDecimal.ROUND_*`` -> int（``Excel.roundingMode()`` 存的就是 int）
ROUNDING_MODES = {
    "ROUND_UP": "0",
    "ROUND_DOWN": "1",
    "ROUND_CEILING": "2",
    "ROUND_FLOOR": "3",
    "ROUND_HALF_UP": "4",
    "ROUND_HALF_DOWN": "5",
    "ROUND_HALF_EVEN": "6",
    "ROUND_UNNECESSARY": "7",
}

_FIELD_DECL = re.compile(
    r"\b(?:private|protected|public)\s+(?!static\b)(?:final\s+)?(?:transient\s+)?"
    r"([\w<>\[\],.\s?]+?)\s+(\w+)\s*(?:=[^;]*)?;"
)
_INNER_EXCEL = re.compile(r"@Excel\s*\((.*?)\)\s*[,}]", re.DOTALL)
_UNKNOWN_MARK = "# TODO 未支持的注解值"


@dataclass
class ExcelColumn:
    """一列 ``@Excel``。"""

    java_field: str
    attribute: str
    kwargs: List[Tuple[str, str]] = field(default_factory=list)
    problems: List[str] = field(default_factory=list)


def split_top_level(text: str) -> List[str]:
    """按**顶层**逗号切分注解参数（`name="a,b"` / `{ "x", "y" }` 不能切坏）。"""

    parts: List[str] = []
    depth = 0
    current: List[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in "\"'":
            quote = char
            cursor = index + 1
            while cursor < len(text):
                if text[cursor] == "\\":
                    cursor += 2
                    continue
                if text[cursor] == quote:
                    break
                cursor += 1
            current.append(text[index : cursor + 1])
            index = cursor + 1
            continue
        if char in "{[(":
            depth += 1
        elif char in "}])":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    if "".join(current).strip():
        parts.append("".join(current))
    return parts


def parse_arguments(body: str) -> List[Tuple[str, str]]:
    """``name="x", cellType=ColumnType.NUMERIC`` -> ``[(name, "x"), ...]``."""

    pairs: List[Tuple[str, str]] = []
    for part in split_top_level(body):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            # 位置参数（Java 注解没有，但容错一下）
            pairs.append(("value", part))
            continue
        key, _, value = part.partition("=")
        pairs.append((key.strip(), value.strip()))
    return pairs


def to_python_value(java_attribute: str, raw: str, problems: List[str]) -> str:
    """Java 注解的右值 -> Python 表达式。"""

    raw = raw.strip()
    if raw in ("true", "false"):
        return "True" if raw == "true" else "False"

    quoted = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', raw, re.DOTALL)
    if quoted:
        literal = quoted.group(1)
        # Java 的转义在 Python 里同样合法（\" \\ \n \t），但这里是表头文本，
        # 只要把 Python 字符串里的反斜杠与双引号再转义一次即可。
        escaped = literal.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        return f'"{escaped}"'

    array = re.fullmatch(r"\{(.*)\}", raw, re.DOTALL)
    if array:
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', array.group(1))
        return "(" + ", ".join(f'"{item}"' for item in items) + ("," if len(items) == 1 else "") + ")"

    enum_ref = re.fullmatch(r"([A-Z]\w*)\.([A-Z_0-9]+)", raw)
    if enum_ref:
        enum_class, constant = enum_ref.group(1), enum_ref.group(2)
        if enum_class == "IndexedColors":
            # Python 侧颜色常量直接是模块级名字（GREY_50_PERCENT / WHITE / BLACK）
            return constant
        if enum_class == "BigDecimal":
            mapped = ROUNDING_MODES.get(constant)
            if mapped is not None:
                return mapped
        return f"{enum_class}.{constant}"

    if re.fullmatch(r"-?\d+(?:\.\d+)?[dDfFlL]?", raw):
        return raw.rstrip("dDfFlL")

    problems.append(f"{java_attribute}={raw}")
    return raw


def parse_excel_columns(java_source: str) -> List[ExcelColumn]:
    """按源码顺序取出全部 ``@Excel`` 列（``@Excels`` 摊平成多列）。"""

    source = strip_comments(java_source)
    annotations = iter_annotations(source)
    columns: List[ExcelColumn] = []
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
        for body in bodies:
            column = ExcelColumn(java_field=declaration.group(2), attribute="")
            for java_attribute, raw in parse_arguments(body):
                if java_attribute not in ATTRIBUTE_NAMES:
                    column.problems.append(f"{java_attribute}={raw}")
                    continue
                python_attribute = ATTRIBUTE_NAMES[java_attribute]
                expression = to_python_value(java_attribute, raw, column.problems)
                if DEFAULTS[java_attribute] == expression:
                    continue
                column.kwargs.append((python_attribute, expression))
            columns.append(column)
    return columns


def resolve_attribute(java_field: str, model_fields: Sequence[str], problems: List[str]) -> str:
    """Java 字段名 -> Python 属性名（优先取模型里真实存在的那个）。"""

    available = set(model_fields)
    exact = camel_to_snake(java_field)
    if exact in available:
        return exact
    for name in model_fields:
        if snake_to_camel(name) == java_field:
            return name
    problems.append(f"属性 {java_field}（推算 {exact}）不在模型字段里")
    return exact


def render_columns(
    model_name: str,
    columns: List[ExcelColumn],
    model_fields: Sequence[str],
) -> str:
    """渲染成可以直接粘进模型类的 ``EXCEL_FIELDS``。"""

    lines: List[str] = []
    used: set = set()
    problems: List[str] = []

    rendered: List[str] = []
    for column in columns:
        attribute = resolve_attribute(column.java_field, model_fields, problems)
        arguments = ", ".join(f"{key}={value}" for key, value in column.kwargs)
        rendered.append(f'    ("{attribute}", Excel({arguments})),')
        for key, _ in column.kwargs:
            used.add(key)
        problems.extend(column.problems)

    lines.append(f"# ---- {model_name} ----")
    for item in rendered:
        lines.append(item)
    if problems:
        lines.append(f"# {_UNKNOWN_MARK}: {', '.join(sorted(set(problems)))}")
    lines.append(f"# imports: {_render_imports(used)}")
    lines.append("")
    return "\n".join(lines)


def _render_imports(used: set) -> str:
    names = {"Excel"}
    if "cell_type" in used:
        names.add("ColumnType")
    if "type" in used:
        names.add("Type")
    if "align" in used:
        names.add("HorizontalAlignment")
    if "handler" in used:
        names.add("ExcelHandlerAdapter")
    names.add("ExcelFields")
    return "from app.common.annotation.excel import " + ", ".join(sorted(names))


def find_java_files(names: Sequence[str]) -> Dict[str, Path]:
    found: Dict[str, Path] = {}
    for path in PROJECT_ROOT.glob("ruoyi-*/src/main/java/**/*.java"):
        if "target" in path.parts:
            continue
        if path.stem in names and path.stem not in found:
            found[path.stem] = path
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Java @Excel -> Python EXCEL_FIELDS")
    parser.add_argument("--java", nargs="*", default=[], help="Java 域对象文件名（可多位）")
    parser.add_argument("--all-gaps", action="store_true", help="处理 audit_domains 报出的全部导出缺口")
    arguments = parser.parse_args()

    models = collect_python()

    names: List[str] = []
    if arguments.all_gaps:
        from audit_domains import build_report

        names.extend(build_report().export_gaps)
    names.extend(Path(item).stem for item in arguments.java)
    if not names:
        parser.error("用 --java Xxx.java 或 --all-gaps 指定目标")

    located = find_java_files(list(dict.fromkeys(names)))
    missing = [name for name in dict.fromkeys(names) if name not in located]
    if missing:
        print(f"找不到 Java 源文件: {', '.join(missing)}")
        return 1

    for name in dict.fromkeys(names):
        columns = parse_excel_columns(located[name].read_text(encoding="utf-8", errors="replace"))
        model = models.get(name)
        model_fields = list(model.fields) if model else []
        if model is None:
            model_fields = [camel_to_snake(column.java_field) for column in columns]
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
        print(render_columns(name, columns, model_fields))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
