"""easypoi 模板导出（``TemplateExportParams`` + ``ExcelExportUtil``）.

# Migrated from: cn.afterturn.easypoi.excel.entity.TemplateExportParams
# Migrated from: cn.afterturn.easypoi.excel.ExcelExportUtil

Java 侧用法（本工程 15+ 个控制器的导出接口都是这两行）::

    TemplateExportParams params = new TemplateExportParams("templates/export/gantry.xlsx");
    Workbook workbook = ExcelExportUtil.exportExcel(params, map);

    map.put("entitylist", list);          // key = 模板里 {{$fe:<name> ...}} 的名字

模板长什么样
------------
以 ``templates/export/gantry.xlsx`` 为例，第 1 行是表头，第 2 行是**模板行**：

.. code-block:: text

    A2: {{$fe:entitylist t.orgCode   B2: t.orgName   ...   M2: t.isData}}

也就是说 ``{{$fe:`` 在 A2，``}}`` 在 M2 —— **一个 list 标记跨多个单元格**，
每个单元格里放一个属性名。easypoi 会把这一行按 list 的元素个数复制，逐个把
``t.orgCode`` 解析成对象的 ``orgCode`` 属性值。

本实现只覆盖这个形状（本工程的 23 份导出模板全是它），不做 easypoi 的
``{{name}}`` 标量替换、``{{!var}}`` 取值表达式、``fn:`` 函数、图片、合并单元格
公式等 —— 引擎里没有就别装。

两条与 Java 一致的细节
----------------------
1. 属性名带 ``t.`` 前缀（SQL 别名习惯），解析时先削掉再转 snake_case；
   取不到属性写空单元格，**不抛异常**（easypoi 同样静默留空）。
2. 列表为空时，模板行会被**清空**（不留下 ``{{$fe:...}}`` 字面量）。
"""

from __future__ import annotations

import io
import re
from copy import copy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet

from app.settings import PROJECT_ROOT

#: classpath 根 ``templates/export/xxx.xlsx`` 在 Python 侧的对应目录是
#: ``config/templates/export/xxx.xlsx`` —— 即 classpath 根 = ``config/``。
TEMPLATES_ROOT: Path = PROJECT_ROOT / "config"

#: ``{{$fe:`` 标记（大小写不敏感，和 easypoi 一样）。
_FE_START = re.compile(r"\{\{\s*\$fe:", re.IGNORECASE)
#: 结束标记。
_FE_END = "}}"

_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _snake(name: str) -> str:
    return _CAMEL_BOUNDARY.sub("_", name).lower()


class TemplateExportParams:
    """Java: ``new TemplateExportParams(String templateUrl)``."""

    def __init__(self, template_url: str, sheet_name: str = "") -> None:
        #: 形如 ``templates/export/gantry.xlsx``。
        self.template_url = template_url
        #: ``""`` = 第一张表。
        self.sheet_name = sheet_name

    @property
    def template_path(self) -> Path:
        """把 classpath 路径（``templates/export/x.xlsx``）映射到 ``config/`` 下的同名文件。"""
        return TEMPLATES_ROOT / self.template_url

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"TemplateExportParams({self.template_url!r}, {self.sheet_name!r})"


class ExcelExportUtil:
    """Java: ``static Workbook exportExcel(TemplateExportParams, Map<String,Object>)``."""

    @staticmethod
    def export_excel(params: TemplateExportParams, data: Mapping[str, Any]):
        """打开模板、填 list 标记、返回 ``openpyxl.Workbook``。"""
        workbook = load_workbook(params.template_path)
        worksheet = (
            workbook[params.sheet_name]
            if params.sheet_name
            else workbook.worksheets[0]
        )
        # 从下往上处理，多次 insert 不会打乱上面的行号。
        for marker in reversed(_find_list_markers(worksheet)):
            _render_list(worksheet, marker, data)
        return workbook


# --------------------------------------------------------------------------- 内部


class _ListMarker:
    """一个 ``{{$fe:<name> field...}}`` 标记的定位结果."""

    def __init__(self, row: int, first_column: int, last_column: int, tokens: Sequence[str]) -> None:
        self.row = row
        self.first_column = first_column
        self.last_column = last_column
        self.tokens = tokens

    @property
    def list_name(self) -> str:
        return self.tokens[0]

    @property
    def fields(self) -> Sequence[str]:
        return self.tokens[1:]


def _find_list_markers(worksheet: Worksheet) -> List[_ListMarker]:
    markers: List[_ListMarker] = []
    for row in worksheet.iter_rows():
        for cell in row:
            value = cell.value
            if not isinstance(value, str) or not _FE_START.search(value):
                continue
            marker = _read_marker(worksheet, cell)
            if marker is not None:
                markers.append(marker)
    return markers


def _read_marker(worksheet: Worksheet, cell: Cell) -> Optional[_ListMarker]:
    """从 ``{{$fe:`` 所在的单元格向右收集到 ``}}``，拼出 token 列表。"""
    row = cell.row
    first = cell.column
    texts: List[str] = []
    last = first
    column = first
    while True:
        current = worksheet.cell(row=row, column=column)
        value = current.value
        if isinstance(value, str):
            texts.append(value)
        if isinstance(value, str) and _FE_END in value:
            last = column
            break
        column += 1
        if column > worksheet.max_column + 1:
            # 标记没有闭合（模板坏了）—— 与 easypoi 一样放弃这一行。
            return None
    joined = " ".join(texts)
    start = _FE_START.search(joined)
    assert start is not None
    body = joined[start.end():]
    end_index = body.find(_FE_END)
    if end_index >= 0:
        body = body[:end_index]
    tokens = [token for token in re.split(r"\s+", body.strip()) if token]
    if not tokens:
        return None
    return _ListMarker(row, first, last, tokens)


def _render_list(worksheet: Worksheet, marker: _ListMarker, data: Mapping[str, Any]) -> None:
    rows = data.get(marker.list_name) or []
    if not isinstance(rows, Iterable) or isinstance(rows, (str, bytes)):
        rows = []
    items = list(rows)
    template_row = marker.row
    styles = [
        copy(worksheet.cell(row=template_row, column=column)._style)
        for column in range(1, worksheet.max_column + 1)
    ]
    height = worksheet.row_dimensions[template_row].height

    for extra in range(max(0, len(items) - 1)):
        worksheet.insert_rows(template_row + 1 + extra)

    for offset, item in enumerate(items):
        target = template_row + offset
        if target != template_row:
            worksheet.row_dimensions[target].height = height
        for index, cell_style in enumerate(styles, start=1):
            target_cell = worksheet.cell(row=target, column=index)
            target_cell._style = copy(cell_style)
        for position, field in enumerate(marker.fields):
            column = marker.first_column + position
            worksheet.cell(row=target, column=column).value = _resolve(item, field)
        # 标记末尾之后、模板行内剩余的列清空（例如 M2 之后的 N2）。
        for column in range(
            marker.first_column + len(marker.fields), marker.last_column + 1
        ):
            worksheet.cell(row=target, column=column).value = None

    if not items:
        # 没有数据：把模板行整段清空，避免把 {{$fe:...}} 原样发出去。
        for column in range(marker.first_column, marker.last_column + 1):
            worksheet.cell(row=template_row, column=column).value = None


def _resolve(item: Any, field: str) -> Any:
    """``t.orgCode`` -> ``item.org_code``；取不到返回 ``None``。"""
    name = field.strip()
    if name.startswith("t."):
        name = name[2:]
    attribute = _snake(name) if not name.islower() else name
    value = _get(item, attribute)
    if value is None:
        value = _get(item, _snake(name))
    return value


def _get(item: Any, attribute: str) -> Any:
    if isinstance(item, Mapping):
        return item.get(attribute)
    return getattr(item, attribute, None)


def workbook_to_bytes(workbook: Any) -> bytes:
    """``workbook.write(OutputStream)`` 的等价物。"""
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


__all__ = [
    "ExcelExportUtil",
    "TEMPLATES_ROOT",
    "TemplateExportParams",
    "workbook_to_bytes",
]
