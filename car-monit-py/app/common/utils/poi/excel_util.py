"""Excel 相关处理.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java

1797 行 Apache POI 工具类的 Python 等价物（openpyxl 3.1.5），**逐方法对照**。
下面只写"读代码时最容易踩空"的地方，其余行为逐行照抄。

只迁了本工程真正会用到的两条链路
--------------------------------
本项目 **8** 个 ``export`` 端点全都调 ``exportExcel(list, sheetName)``（写文件 +
返回文件名那个重载），``SysUserController`` 另外用 ``importExcel`` /
``importTemplateExcel``。**没有任何**调用点用 ``HttpServletResponse`` 那两个重载，
但它们仍然迁了（``export_excel_to_sink`` / ``import_template_excel_to_sink``）——
按迁移规则"看似没用的 Java 代码也要搬，并标注"。

``exportExcel`` 返回的是 **AjaxResult**，文件名在 ``msg`` 里
------------------------------------------------------------
``return AjaxResult.success(filename)`` 中的 ``filename`` 是 ``String``，Java 的重载
决议挑 ``success(String msg)``（比 ``success(Object data)`` 更具体），于是文件名落在
**``msg``**、``data`` 整个消失：

    {"code": 200, "msg": "<uuid>_用户数据.xlsx"}

Python 侧用 :meth:`AjaxResult.success_message`。与 ``sys_file`` 的 ``-111111``、
``fileLogId`` 是同一类坑（COMPATIBILITY §36.12 / §37）。

文件落盘位置
------------
``RuoYiConfig.getDownloadPath()`` = ``{profile}/download/``（**末尾带斜杠**），
``getAbsoluteFile`` 负责 ``mkdirs``。文件名 = ``UUID.randomUUID() + "_" + sheetName
+ ".xlsx"``。客户端随后必须走 ``GET /common/download?fileName=...`` 才能拿到内容
（:mod:`app.api.common.common_controller`）。

样式键 = Java 的字符串拼接
--------------------------
``styles`` 的键是 ``"title"`` / ``"data"`` / ``"total"`` /
``"header_{headerColor}_{headerBackgroundColor}"`` /
``"data_{align}_{color}_{backgroundColor}_{cellType}"``。Java 拼进去的是
``Enum.toString()``（常量名），所以 :mod:`app.common.annotation.excel` 里每个枚举
都重写了 ``__str__`` —— 否则键会变成 ``"IndexedColors.WHITE"``，与 Java 对不上。

与 POI 的单位换算
-----------------
================  =============================  ============================
POI               单位                           openpyxl
================  =============================  ============================
列宽              ``1/256`` 个字符宽             字符数（``poi / 256``）
``setHeight()``   ``1/20`` 磅                    磅（``twips / 20``）
``setHeightInPoints()``  磅                     磅（原值）
================  =============================  ============================

``setCellValue(String)`` 与 openpyxl 的差异
-------------------------------------------
POI 的 ``setCellValue(String)`` **永远**建成字符串单元格；openpyxl 的
``cell.value = "=A1"`` 会把单元格变成**公式**。所以所有写字符串的地方都走
:meth:`ExcelUtil._set_string`，必要时把 ``data_type`` 拨回 ``"s"``。

``addCell`` 把异常吞掉
----------------------
整个方法体包在 ``try { ... } catch (Exception e) { log.error("导出Excel失败{}", e); }``
里 —— 单列出错**不会**中断导出，只会留下"有样式、没值"的空单元格（``NUMERIC`` 列
遇到非数字就是这个下场）。Python 侧同样 ``except Exception``，别改成只捕
``(ValueError, TypeError)``。

``importExcel`` 只认 xlsx
-------------------------
``WorkbookFactory.create(is)`` 同时支持 ``.xls`` 与 ``.xlsx``；openpyxl 只支持后者
（``load_workbook`` 读 ``.xls`` 抛 ``InvalidFileException``）。差异见
``COMPATIBILITY.md`` §37。

休眠代码
--------
``ColumnType.IMAGE`` / ``handler`` / ``combo`` / ``needMerge`` / ``isStatistics`` /
Collection 子列表这六块**当前没有任何实体使用**（全工程只有 ``SysUser.dept`` 一处
``@Excels``、两处 ``prompt``），但仍然完整迁过来了，按迁移规则标注为休眠。
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import date, datetime, timedelta
from decimal import ROUND_CEILING, ROUND_DOWN, ROUND_FLOOR, ROUND_HALF_DOWN, ROUND_HALF_EVEN
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal
from io import BytesIO
from os import makedirs
from os.path import exists
from typing import (
    Any,
    BinaryIO,
    Callable,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from app.common.annotation.excel import (
    EXCEL_FIELDS_NAME,
    GREY_50_PERCENT,
    ColumnType,
    Excel,
    ExcelField,
    IndexedColor,
    Type,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.text.convert import to_bool, to_double, to_int, to_long, to_str
from app.common.exception.exceptions import UtilException
from app.common.utils import date_utils as DateUtils
from app.common.utils import dict_utils as DictUtils
from app.common.utils.string_utils import is_empty, is_not_empty, split_regex, strip_end
from app.settings import get_settings

T = TypeVar("T")

logger = logging.getLogger("app.common.utils.poi.excel_util")

#: Java: ``ExcelUtil.FORMULA_REGEX_STR``
FORMULA_REGEX_STR = r"=|-|\+|@"
#: Java: ``ExcelUtil.FORMULA_STR``
FORMULA_STR: Tuple[str, ...] = ("=", "-", "+", "@")
#: Java: ``ExcelUtil.sheetSize``
SHEET_SIZE = 65536
#: Java: ``DecimalFormat("######0.00")`` —— 由 :func:`_format_double_00` 实现
DOUBLE_FORMAT = "######0.00"

#: Java: ``BigDecimal.ROUND_*`` 常量 -> :mod:`decimal` 的舍入模式
_ROUNDING_MODES: Dict[int, str] = {
    0: ROUND_UP,
    1: ROUND_DOWN,
    2: ROUND_CEILING,
    3: ROUND_FLOOR,
    4: ROUND_HALF_UP,
    5: ROUND_HALF_DOWN,
    6: ROUND_HALF_EVEN,
}

#: Java: ``HorizontalAlignment`` -> openpyxl 的 ``horizontal``
_ALIGNMENTS: Dict[str, str] = {
    "GENERAL": "general",
    "LEFT": "left",
    "CENTER": "center",
    "RIGHT": "right",
    "FILL": "fill",
    "JUSTIFY": "justify",
    "CENTER_SELECTION": "centerContinuous",
    "DISTRIBUTED": "distributed",
}

#: Excel 1900 日期系统的纪元（POI ``DateUtil.getJavaDate`` 用同一基准，已经算进了
#: 1900-02-29 那个不存在的闰日，所以是 12-30 而不是 12-31）。
_EXCEL_EPOCH = datetime(1899, 12, 30)


class _CellStyle:
    """``org.apache.poi.ss.usermodel.CellStyle`` 的最小替身（五个可变属性）."""

    __slots__ = ("font", "fill", "border", "alignment", "number_format")

    def __init__(
        self,
        font: Font,
        fill: PatternFill,
        border: Border,
        alignment: Alignment,
        number_format: str = "General",
    ) -> None:
        self.font = font
        self.fill = fill
        self.border = border
        self.alignment = alignment
        self.number_format = number_format

    def apply_to(self, cell: Any) -> None:
        cell.font = self.font
        cell.fill = self.fill
        cell.border = self.border
        cell.alignment = self.alignment
        cell.number_format = self.number_format


class _Row(Sequence[Any]):
    """``org.apache.poi.ss.usermodel.Row`` 的最小替身.

    ``sheet.createRow(index)`` 等价于 ``_Row(sheet, index, n)`` —— openpyxl 没有独立的
    行对象（``sheet[k]`` 每次返回一个新元组，而且拿不到 ``height``），所以包一层：
    下标访问映射到 ``sheet.cell()``，``height`` 映射到 ``row_dimensions``。
    """

    __slots__ = ("_sheet", "_cells", "index")

    def __init__(self, sheet: Worksheet, index: int, columns: int) -> None:
        self._sheet = sheet
        self.index = index
        self._cells = tuple(sheet.cell(row=index + 1, column=column + 1) for column in range(columns))

    def __getitem__(self, column: int) -> Any:  # type: ignore[override]
        return self._cells[column]

    def __len__(self) -> int:
        return len(self._cells)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._cells)

    # Java: row.setHeight(short) —— **1/20 磅**
    @property
    def height(self) -> Optional[float]:
        return self._sheet.row_dimensions[self.index + 1].height

    @height.setter
    def height(self, points: float) -> None:
        self._sheet.row_dimensions[self.index + 1].height = points


def _declared_excel_fields(clazz: type) -> Tuple[ExcelField, ...]:
    """Java: ``clazz.getSuperclass().getDeclaredFields()`` + ``clazz.getDeclaredFields()``.

    按 MRO 由基类到子类收集每个类 **自己** 的 ``EXCEL_FIELDS``（用 ``__dict__`` 取，
    避免子类把父类的表再收一遍），等价于 Java 先取父类声明字段再取本类声明字段。
    """
    collected: List[ExcelField] = []
    for klass in reversed(getattr(clazz, "__mro__", (clazz,))):
        collected.extend(klass.__dict__.get(EXCEL_FIELDS_NAME, ()))
    return tuple(collected)


def _style_key_header(attr: Excel) -> str:
    """Java: ``StringUtils.format("header_{}_{}", attr.headerColor(), attr.headerBackgroundColor())``."""
    return f"header_{attr.header_color}_{attr.header_background_color}"


def _style_key_data(attr: Excel) -> str:
    """Java: ``StringUtils.format("data_{}_{}_{}_{}", align, color, backgroundColor, cellType)``."""
    return f"data_{attr.align}_{attr.color}_{attr.background_color}_{attr.cell_type}"


class ExcelUtil(Generic[T]):
    """Excel 相关处理 / spreadsheet writer + reader.

    与 Java 一样是**有状态**的：``init()`` 之后同一个实例只能导出一份文件
    （``writeSheet`` 会往 ``self._sheet`` 里追加行）。
    """

    #: Java: ``public static final String FORMULA_REGEX_STR``
    FORMULA_REGEX_STR = FORMULA_REGEX_STR
    #: Java: ``public static final String[] FORMULA_STR``
    FORMULA_STR = FORMULA_STR
    #: Java: ``public static final int sheetSize``
    sheet_size = SHEET_SIZE

    def __init__(self, clazz: type[T]) -> None:
        #: Java: ``public Class<T> clazz``
        self.clazz: type[T] = clazz
        #: Java: ``public Map<String, String> sysDictMap`` —— 避免重复查字典缓存。
        #: 键是 ``dictType + value``（**直接拼接，没有分隔符**，照抄）。
        self.sys_dict_map: Dict[str, str] = {}
        #: Java: ``public String[] excludeFields``
        self.exclude_fields: Sequence[str] = ()

        self._sheet_name: str = ""
        self._type: Type = Type.EXPORT
        self._wb: Optional[Workbook] = None
        self._sheet: Optional[Worksheet] = None
        self._styles: Dict[str, _CellStyle] = {}
        self._list: List[T] = []
        #: ``(属性名, Excel)`` 列表，对应 Java 的 ``List<Object[]> fields``
        self._fields: List[ExcelField] = []
        self._rownum: int = 0
        self._title: str = ""
        #: Java: ``short maxHeight``（twips = 1/20 磅）
        self._max_height: int = 0
        self._sub_merged_last_row_num: int = 0
        self._sub_merged_first_row_num: int = 1
        self._sub_method: Optional[Callable[[Any], Any]] = None
        self._sub_fields: Optional[List[ExcelField]] = None
        self._statistics: Dict[int, float] = {}
        #: ``sheet.getLastRowNum()`` 的镜像（0 基，空表为 -1）
        self._last_row_index: int = -1

    # ------------------------------------------------------------------ 属性

    @property
    def sheet_name(self) -> str:
        return self._sheet_name

    @property
    def type(self) -> Type:
        return self._type

    @property
    def sheet(self) -> Worksheet:
        assert self._sheet is not None, "init() 尚未调用"
        return self._sheet

    @property
    def workbook(self) -> Workbook:
        assert self._wb is not None, "init() 尚未调用"
        return self._wb

    # Java: public void hideColumn(String... fields)
    def hide_column(self, *fields: str) -> None:
        self.exclude_fields = fields

    # Java: public void init(List<T> list, String sheetName, String title, Type type)
    def init(self, entities: Optional[List[T]], sheet_name: str, title: str, type_: Type) -> None:
        self._list = list(entities) if entities is not None else []
        self._sheet_name = sheet_name
        self._type = type_
        self._title = title
        self.create_excel_field()
        self.create_workbook()
        self.create_title()
        self.create_sub_head()

    # ------------------------------------------------------------------ 字段

    # Java: private void createExcelField()
    def create_excel_field(self) -> None:
        """收集字段并按 ``Excel.sort()`` 稳定排序.

        ``Stream.sorted`` 是**稳定**排序，而 ``sort()`` 的默认值是
        ``Integer.MAX_VALUE``，所以没写 ``sort`` 的字段保持"父类在前、本类声明顺序"。
        """
        fields = list(self.get_fields())
        fields.sort(key=lambda item: item[1].sort)
        self._fields = fields
        self._max_height = self.get_row_height()

    # Java: public List<Object[]> getFields()
    def get_fields(self) -> List[ExcelField]:
        """``excludeFields`` 的两条判据.

        Java 对单注解查 ``field.getName()``，对 ``@Excels`` 里的每一条查
        ``field.getName() + "." + targetAttr()``。这里 ``@Excels`` 已摊平成多条，
        所以两条判据都判——顺序也照抄：先整体排除字段，再逐条排除 ``字段.目标属性``。
        """
        excluded = self.exclude_fields
        fields: List[ExcelField] = []
        for name, attr in _declared_excel_fields(self.clazz):
            if name in excluded:
                continue
            if f"{name}.{attr.target_attr}" in excluded:
                continue
            if attr.type is Type.ALL or attr.type is self._type:
                fields.append((name, attr))
        return fields

    # Java: public short getRowHeight()
    def get_row_height(self) -> int:
        max_height = 0.0
        for _name, attr in self._fields:
            max_height = max(max_height, attr.height)
        # Java: (short) (maxHeight * 20) —— 直接截断，不四舍五入
        return int(max_height * 20)

    # ------------------------------------------------------------------ 工作簿

    # Java: public void createWorkbook()
    def create_workbook(self) -> None:
        # Java: new SXSSFWorkbook(500) —— 流式写；openpyxl 只有普通 Workbook
        self._wb = Workbook()
        self._sheet = self._wb.active
        self._sheet.title = self._sheet_name
        self._last_row_index = -1
        self._styles = self.create_styles(self._wb)

    # Java: private Map<String, CellStyle> createStyles(Workbook wb)
    def create_styles(self, wb: Workbook) -> Dict[str, _CellStyle]:
        styles: Dict[str, _CellStyle] = {}
        none_fill = PatternFill()
        none_border = Border()
        center = Alignment(horizontal="center", vertical="center")

        # Java: "title" —— Arial 16 粗体 + 文本格式，**没有**边框
        styles["title"] = _CellStyle(Font(name="Arial", size=16, bold=True), none_fill, none_border, center, "@")

        # Java: "data" —— Arial 10 + 灰色细边框，**没有**填充
        margin = Side(style="thin", color=GREY_50_PERCENT.rgb)
        data_border = Border(left=margin, right=margin, top=margin, bottom=margin)
        styles["data"] = _CellStyle(Font(name="Arial", size=10), none_fill, data_border, center, "General")

        # Java: "total" —— 合计行，没有边框、没有填充
        styles["total"] = _CellStyle(Font(name="Arial", size=10), none_fill, none_border, center, "General")

        styles.update(self.annotation_header_styles(wb, styles, data_border, center))
        styles.update(self.annotation_data_styles(wb, data_border))
        return styles

    # Java: private Map<String, CellStyle> annotationHeaderStyles(Workbook wb, Map<String, CellStyle> styles)
    def annotation_header_styles(
        self, wb: Workbook, styles: Dict[str, _CellStyle], border: Border, center: Alignment
    ) -> Dict[str, _CellStyle]:
        """``cloneStyleFrom(styles.get("data"))`` 后覆盖填充 / 字体.

        ``wb`` 与 ``styles`` 两个形参在 Java 里也是"只用 ``styles`` 里的 ``data``"，
        保留签名以便逐行对照（openpyxl 的 ``Font`` / ``PatternFill`` 不需要 workbook）。
        """
        header_styles: Dict[str, _CellStyle] = {}
        for _name, attr in self._fields:
            key = _style_key_header(attr)
            if key in header_styles:
                continue
            header_styles[key] = _CellStyle(
                Font(name="Arial", size=10, bold=True, color=attr.header_color.rgb),
                _solid_fill(attr.header_background_color),
                border,
                center,
                "@",
            )
        return header_styles

    # Java: private Map<String, CellStyle> annotationDataStyles(Workbook wb)
    def annotation_data_styles(self, wb: Workbook, border: Border) -> Dict[str, _CellStyle]:
        styles: Dict[str, _CellStyle] = {}
        for _name, attr in self._fields:
            key = _style_key_data(attr)
            if key in styles:
                continue
            styles[key] = _CellStyle(
                Font(name="Arial", size=10, color=attr.color.rgb),
                _solid_fill(attr.background_color),
                border,
                Alignment(horizontal=_ALIGNMENTS[str(attr.align)], vertical="center"),
                # Java: 只有 TEXT 设 DataFormat("@")，其余保持 General
                "@" if attr.cell_type is ColumnType.TEXT else "General",
            )
        return styles

    # Java: public void createTitle()
    def create_title(self) -> None:
        if is_empty(self._title):
            return
        self._sub_merged_first_row_num += 1
        self._sub_merged_last_row_num += 1
        title_last_col = len(self._fields) - 1
        if self.is_sub_list():
            assert self._sub_fields is not None
            title_last_col += len(self._sub_fields) - 1
        # Java: sheet.createRow(rownum == 0 ? rownum++ : 0)
        row_index = 0
        if self._rownum == 0:
            row_index = self._rownum
            self._rownum += 1
        row = self._create_row(row_index)
        # Java: titleRow.setHeightInPoints(30)
        row.height = 30
        cell = row[0]
        self._styles["title"].apply_to(cell)
        self._set_string(cell, self._title)
        # Java: addMergedRegion(new CellRangeAddress(rowNum, rowNum, rowNum, titleLastCol))
        # 第一列的起点用的是**行号**而不是 0（照抄；只有行 0 时 0..lastCol 才正确）
        self._merge(row_index, row_index, row_index, title_last_col)

    # Java: public void createSubHead()
    def create_sub_head(self) -> None:
        if not self.is_sub_list():
            return
        assert self._sub_fields is not None
        self._sub_merged_first_row_num += 1
        self._sub_merged_last_row_num += 1
        row = self._create_row(self._rownum)
        excel_num = 0
        for _name, attr in self._fields:
            head = row[excel_num]
            self._set_string(head, attr.name)
            self._styles[_style_key_header(attr)].apply_to(head)
            excel_num += 1
        head_first_row = excel_num - 1
        head_last_row = head_first_row + len(self._sub_fields) - 1
        if head_last_row > head_first_row:
            self._merge(self._rownum, self._rownum, head_first_row, head_last_row)
        self._rownum += 1

    # Java: public void createSheet(int sheetNo, int index)
    def create_sheet(self, sheet_no: int, index: int) -> None:
        if sheet_no > 1 and index > 0:
            self._sheet = self.workbook.create_sheet()
            # ``getLastRowNum()`` 是**每个 sheet** 各自的计数
            self._last_row_index = -1
            self.create_title()
            # Java: wb.setSheetName(index, sheetName + index)
            self._sheet.title = f"{self._sheet_name}{index}"

    # ------------------------------------------------------------------ 写

    # Java: public void writeSheet()
    def write_sheet(self) -> None:
        # Java: Math.max(1, (int) Math.ceil(list.size() * 1.0 / sheetSize))
        sheet_no = max(1, -((-len(self._list)) // SHEET_SIZE))
        for index in range(sheet_no):
            self.create_sheet(sheet_no, index)
            row = self._create_row(self._rownum)
            column = 0
            for name, excel in self._fields:
                if self._is_collection_field(name):
                    assert self._sub_fields is not None
                    for _sub_name, sub_excel in self._sub_fields:
                        self.create_head_cell(sub_excel, row, column)
                        column += 1
                else:
                    self.create_head_cell(excel, row, column)
                    column += 1
            if self._type is Type.EXPORT:
                self.fill_excel_data(index, row)
                self.add_statistics_row()

    # Java: public Cell createHeadCell(Excel attr, Row row, int column)
    def create_head_cell(self, attr: Excel, row: _Row, column: int) -> Any:
        cell = row[column]
        self._set_string(cell, attr.name)
        self.set_data_validation(attr, row, column)
        self._styles[_style_key_header(attr)].apply_to(cell)
        if self.is_sub_list() and attr.need_merge:
            # Java: addMergedRegion(new CellRangeAddress(rownum - 1, rownum, column, column))
            self._merge(self._rownum - 1, self._rownum, column, column)
        # Java 还有一句 ``sheet.setDefaultColumnStyle(column, dataStyle)``（只在子列表时），
        # openpyxl 没有"列默认样式"，合并区域的样式由 fillExcelData 里的 addCell 补齐。
        return cell

    # Java: public void fillExcelData(int index, Row row)
    def fill_excel_data(self, index: int, row: _Row) -> None:
        start_no = index * SHEET_SIZE
        end_no = min(start_no + SHEET_SIZE, len(self._list))
        row_no = (1 + self._rownum) - start_no
        for i in range(start_no, end_no):
            # Java: rowNo = isSubList() ? (i > 1 ? rowNo + 1 : rowNo + i) : i + 1 + rownum - startNo
            if self.is_sub_list():
                row_no = row_no + 1 if i > 1 else row_no + i
            else:
                row_no = i + 1 + self._rownum - start_no
            row = self._create_row(row_no)
            vo = self._list[i]
            sub_list: List[Any] = []
            if self.is_sub_list():
                if self.is_sub_list_value(vo):
                    sub_list = self.get_list_cell_value(vo)
                    self._sub_merged_last_row_num += len(sub_list)
                else:
                    self._sub_merged_first_row_num += 1
                    self._sub_merged_last_row_num += 1
            column = 0
            for name, excel in self._fields:
                if self._is_collection_field(name) and sub_list:
                    sub_first = False
                    assert self._sub_fields is not None
                    for obj in sub_list:
                        if sub_first:
                            row_no += 1
                            row = self._create_row(row_no)
                        for sub_index, (sub_name, attr) in enumerate(self._sub_fields):
                            self.add_cell(attr, row, obj, sub_name, column + sub_index)
                        sub_first = True
                    self._sub_merged_first_row_num += len(sub_list)
                else:
                    self.add_cell(excel, row, vo, name, column)
                    column += 1

    # Java: public Cell addCell(Excel attr, Row row, T vo, Field field, int column)
    def add_cell(self, attr: Excel, row: _Row, vo: Any, attribute: str, column: int) -> Any:
        cell = None
        try:
            # Java: row.setHeight(maxHeight) —— twips -> 磅
            row.height = self._max_height / 20
            # Java: 根据 Excel 中设置情况决定是否导出
            if not attr.is_export:
                return cell
            cell = row[column]
            if self.is_sub_list_value(vo) and len(self.get_list_cell_value(vo)) > 1 and attr.need_merge:
                self._merge(
                    self._sub_merged_first_row_num, self._sub_merged_last_row_num, column, column
                )
            self._styles[_style_key_data(attr)].apply_to(cell)

            value = self.get_target_value(vo, attribute, attr)
            if is_not_empty(attr.date_format) and value is not None:
                self._set_string(cell, self.parse_date_to_str(attr.date_format, value))
            elif is_not_empty(attr.read_converter_exp) and value is not None:
                self._set_string(
                    cell, self.convert_by_exp(to_str(value) or "", attr.read_converter_exp, attr.separator)
                )
            elif is_not_empty(attr.dict_type) and value is not None:
                # Java: 缓存键是 dictType + value，直接拼接
                key = f"{attr.dict_type}{to_str(value)}"
                if key not in self.sys_dict_map:
                    self.sys_dict_map[key] = self.convert_dict_by_exp(
                        to_str(value) or "", attr.dict_type, attr.separator
                    )
                self._set_string(cell, self.sys_dict_map[key])
            elif isinstance(value, Decimal) and attr.scale != -1:
                scaled = value.quantize(
                    Decimal(1).scaleb(-attr.scale),
                    rounding=_ROUNDING_MODES.get(attr.rounding_mode, ROUND_HALF_EVEN),
                )
                cell.value = float(scaled)
            elif attr.has_handler():
                self._set_string(cell, self.data_format_handler_adapter(value, attr, cell))
            else:
                self.set_cell_vo(value, attr, cell)
            self.add_statistics_data(column, to_str(value) or "", attr)
        except Exception as exc:  # noqa: BLE001 - Java 的 catch (Exception) 就是全捕
            logger.error("导出Excel失败%s", exc)
        return cell

    # Java: public void setCellVo(Object value, Excel attr, Cell cell)
    def set_cell_vo(self, value: Any, attr: Excel, cell: Any) -> None:
        if attr.cell_type in (ColumnType.STRING, ColumnType.TEXT):
            # Java: 保留 null 语义 —— ``isNull(cellValue)`` 只判 null，空串照常拼 suffix
            cell_value = to_str(value)
            # Java: 以 =-+@ 开头的单元格前加 tab，防 CSV 注入
            if cell_value is not None and cell_value[:1] in FORMULA_STR:
                cell_value = "\t" + cell_value
            if isinstance(value, (list, tuple)) and cell_value == "[]":
                cell_value = ""
            self._set_string(cell, attr.default_value if cell_value is None else cell_value + attr.suffix)
        elif attr.cell_type is ColumnType.NUMERIC:
            if value is not None:
                # Java: setCellValue(contains(".") ? Convert.toDouble : Convert.toInt)
                # toInt / toDouble 转换失败返回 null -> setCellValue(Integer) 抛 NPE，
                # 被 addCell 的 catch 吞掉（单元格留在"有样式、没值"）。
                text = to_str(value) or ""
                number = to_double(value) if "." in text else to_int(value)
                if number is None:
                    raise TypeError("java.lang.NullPointerException: numeric cell value is null")
                cell.value = number
        elif attr.cell_type is ColumnType.IMAGE:
            # Java 会把图片锚进单元格并 addPicture；本工程没有任何字段用 IMAGE，
            # 图片读写整体未迁（见 COMPATIBILITY §37）。
            raise NotImplementedError("ColumnType.IMAGE 未迁移（无调用点）")

    # Java: public void setDataValidation(Excel attr, Row row, int column)
    def set_data_validation(self, attr: Excel, row: _Row, column: int) -> None:
        letter = get_column_letter(column + 1)
        if "注：" in attr.name:
            # Java: sheet.setColumnWidth(column, 6000)
            self.sheet.column_dimensions[letter].width = 6000 / 256
        else:
            # Java: sheet.setColumnWidth(column, (int) ((attr.width() + 0.72) * 256))
            self.sheet.column_dimensions[letter].width = int((attr.width + 0.72) * 256) / 256
        if is_not_empty(attr.prompt) or len(attr.combo) > 0:
            if len(attr.combo) > 15 or len(",".join(attr.combo)) > 255:
                # Java: 下拉数 > 15 或字符串长度 > 255 时改用一个隐藏 sheet 存候选值
                self.set_xssf_validation_with_hidden(self.sheet, attr.combo, attr.prompt, 1, 100, column, column)
            else:
                self.set_prompt_or_validation(self.sheet, attr.combo, attr.prompt, 1, 100, column, column)

    # Java: public void setPromptOrValidation(Sheet sheet, String[] textlist, String promptContent, ...)
    def set_prompt_or_validation(
        self,
        sheet: Worksheet,
        textlist: Sequence[str],
        prompt_content: str,
        first_row: int,
        end_row: int,
        first_col: int,
        end_col: int,
    ) -> None:
        if len(textlist) > 0:
            validation = DataValidation(type="list", formula1='"' + ",".join(textlist) + '"', allow_blank=True)
        else:
            # Java: helper.createCustomConstraint("DD1") —— 公式就是字面量 "DD1"
            validation = DataValidation(type="custom", formula1="DD1", allow_blank=True)
        if is_not_empty(prompt_content):
            validation.promptTitle = ""
            validation.prompt = prompt_content
            validation.showInputMessage = True
        # Java: setSuppressDropDownArrow(true) + setShowErrorBox(true)（XSSF 分支）
        # openpyxl 的 showDropDown 与 OOXML 属性同名但语义相反：False = 显示下拉箭头。
        validation.showDropDown = False
        validation.showErrorMessage = True
        validation.add(_range_ref(first_row, end_row, first_col, end_col))
        sheet.add_data_validation(validation)

    # Java: public void setXSSFValidationWithHidden(...)
    def set_xssf_validation_with_hidden(
        self,
        sheet: Worksheet,
        textlist: Sequence[str],
        prompt_content: str,
        first_row: int,
        end_row: int,
        first_col: int,
        end_col: int,
    ) -> None:
        from openpyxl.workbook.defined_name import DefinedName

        hide_sheet_name = f"combo_{first_col}_{end_col}"
        hide_sheet = self.workbook.create_sheet(hide_sheet_name)
        for index, item in enumerate(textlist):
            hide_sheet.cell(row=index + 1, column=1, value=item)
        # Java: wb.createName() + setRefersToFormula(hideSheetName + "!$A$1:$A$" + length)
        self.workbook.defined_names.add(
            DefinedName(f"{hide_sheet_name}_data", attr_text=f"{hide_sheet_name}!$A$1:$A${len(textlist)}")
        )
        validation = DataValidation(type="list", formula1=f"{hide_sheet_name}_data", allow_blank=True)
        if is_not_empty(prompt_content):
            validation.promptTitle = ""
            validation.prompt = prompt_content
            validation.showInputMessage = True
        validation.showDropDown = False
        validation.showErrorMessage = True
        validation.add(_range_ref(first_row, end_row, first_col, end_col))
        sheet.add_data_validation(validation)
        # Java: wb.setSheetHidden(wb.getSheetIndex(hideSheet), true)
        hide_sheet.sheet_state = "hidden"

    # Java: private void addStatisticsData(Integer index, String text, Excel entity)
    def add_statistics_data(self, index: int, text: str, entity: Optional[Excel]) -> None:
        if entity is not None and entity.is_statistics:
            if index not in self._statistics:
                self._statistics[index] = 0.0
            try:
                temp = float(text)
            except (TypeError, ValueError):
                temp = 0.0
            self._statistics[index] = self._statistics[index] + temp

    # Java: public void addStatisticsRow()
    def add_statistics_row(self) -> None:
        if not self._statistics:
            return
        row = self._create_row(self._last_row_index + 1)
        cell = row[0]
        self._styles["total"].apply_to(cell)
        self._set_string(cell, "合计")
        # Java 直接遍历 HashMap 的 keySet —— 顺序不确定；这里按列号升序，可预期
        for key in sorted(self._statistics):
            cell = row[key]
            self._styles["total"].apply_to(cell)
            self._set_string(cell, _format_double_00(self._statistics[key]))
        self._statistics.clear()

    # Java: private Object getTargetValue(T vo, Field field, Excel excel)
    def get_target_value(self, vo: Any, attribute: str, excel: Excel) -> Any:
        value = getattr(vo, attribute, None)
        if is_not_empty(excel.target_attr):
            target = excel.target_attr
            if "." in target:
                for name in split_regex(target, r"[.]"):
                    value = self._get_value(value, name)
            else:
                value = self._get_value(value, target)
        return value

    # Java: private Object getValue(Object o, String name)
    @staticmethod
    def _get_value(obj: Any, name: str) -> Any:
        if obj is not None and is_not_empty(name):
            return getattr(obj, name, None)
        return obj

    # Java: public String dataFormatHandlerAdapter(Object value, Excel excel, Cell cell)
    def data_format_handler_adapter(self, value: Any, excel: Excel, cell: Any) -> str:
        try:
            instance = excel.handler()
            value = instance.format(value, excel.args, cell, self._wb)
        except Exception as exc:  # noqa: BLE001 - Java 的 catch (Exception)
            logger.error("不能格式化数据 %s%s", excel.handler, exc)
        return to_str(value) or ""

    # ------------------------------------------------------------------ 导出入口

    # Java: public AjaxResult exportExcel(List<T> list, String sheetName)
    def export_excel(self, entities: List[T], sheet_name: str) -> AjaxResult:
        return self.export_excel_with_title(entities, sheet_name, "")

    # Java: public AjaxResult exportExcel(List<T> list, String sheetName, String title)
    def export_excel_with_title(self, entities: List[T], sheet_name: str, title: str) -> AjaxResult:
        self.init(entities, sheet_name, title, Type.EXPORT)
        return self._write_to_file()

    # Java: public AjaxResult importTemplateExcel(String sheetName)
    def import_template_excel(self, sheet_name: str) -> AjaxResult:
        return self.import_template_excel_with_title(sheet_name, "")

    # Java: public AjaxResult importTemplateExcel(String sheetName, String title)
    def import_template_excel_with_title(self, sheet_name: str, title: str) -> AjaxResult:
        self.init(None, sheet_name, title, Type.IMPORT)
        return self._write_to_file()

    # Java: public AjaxResult exportExcel()
    def _write_to_file(self) -> AjaxResult:
        """``writeSheet`` + 落盘 + ``AjaxResult.success(filename)``.

        Java 的 ``exportExcel()`` 是无参 **public** 方法；这里改成私有，因为它的返回值
        与 :meth:`export_excel` 完全相同，公开出去只会让调用点分不清该用哪个。
        """
        try:
            self.write_sheet()
            filename = self.encoding_filename(self._sheet_name)
            path = self.get_absolute_file(filename)
            self.workbook.save(path)
            # Java: AjaxResult.success(String filename) -> 文件名落在 msg 里
            return AjaxResult.success_message(filename)
        except Exception as exc:  # noqa: BLE001
            logger.error("导出Excel异常%s", exc)
            raise UtilException("导出Excel失败，请联系网站管理员！") from exc
        finally:
            self._close()

    # Java: public String encodingFilename(String filename)
    @staticmethod
    def encoding_filename(filename: str) -> str:
        return f"{uuid.uuid4()}_{filename}.xlsx"

    # Java: public String getAbsoluteFile(String filename)
    @staticmethod
    def get_absolute_file(filename: str) -> str:
        download_path = get_settings().ruoyi.download_path + filename
        parent = download_path.rsplit("/", 1)[0]
        if parent and not exists(parent):
            makedirs(parent, exist_ok=True)
        return download_path

    # Java: public void exportExcel(HttpServletResponse response, List<T> list, String sheetName, String title)
    def export_excel_to_sink(self, sink: Any, entities: List[T], sheet_name: str, title: str = "") -> None:
        """``HttpServletResponse`` 变体（**本工程无调用点**，按迁移规则照搬）.

        ``sink`` 需要提供 ``set_content_type(str)`` 与 ``get_output_stream()``
        （见 :class:`app.system.service.sys_file_service.ResponseSink`）。
        """
        sink.set_content_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.init(entities, sheet_name, title, Type.EXPORT)
        self._export_to_sink(sink)

    # Java: public void importTemplateExcel(HttpServletResponse response, String sheetName, String title)
    def import_template_excel_to_sink(self, sink: Any, sheet_name: str, title: str = "") -> None:
        sink.set_content_type("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.init(None, sheet_name, title, Type.IMPORT)
        self._export_to_sink(sink)

    # Java: public void exportExcel(HttpServletResponse response)
    def _export_to_sink(self, sink: Any) -> None:
        """异常**吞掉**（只记日志）—— 与写文件变体不同，这里不抛 ``UtilException``。"""
        try:
            self.write_sheet()
            stream: BinaryIO = sink.get_output_stream()
            self.workbook.save(stream)
        except Exception as exc:  # noqa: BLE001
            logger.error("导出Excel异常%s", exc)
        finally:
            self._close()

    # ------------------------------------------------------------------ 读

    # Java: public List<T> importExcel(InputStream is)
    def import_excel(self, stream: BinaryIO) -> List[T]:
        try:
            return self.import_excel_with_title_num(stream, 0)
        except Exception as exc:  # noqa: BLE001
            logger.error("导入Excel异常%s", exc)
            raise UtilException(str(exc)) from exc
        finally:
            stream.close()

    # Java: public List<T> importExcel(InputStream is, int titleNum)
    def import_excel_with_title_num(self, stream: BinaryIO, title_num: int) -> List[T]:
        return self.import_excel_sheet("", stream, title_num)

    # Java: public List<T> importExcel(String sheetName, InputStream is, int titleNum)
    def import_excel_sheet(self, sheet_name: str, stream: BinaryIO, title_num: int) -> List[T]:
        self._type = Type.IMPORT
        # Java: WorkbookFactory.create(is) —— openpyxl 只认 xlsx/xlsm
        self._wb = load_workbook(filename=BytesIO(stream.read()), data_only=True)
        entities: List[T] = []
        if is_not_empty(sheet_name):
            sheet = self._wb[sheet_name] if sheet_name in self._wb.sheetnames else None
        else:
            sheet = self._wb.worksheets[0]
        if sheet is None:
            # Java: throw new IOException("文件sheet不存在")
            raise OSError("文件sheet不存在")
        self._sheet = sheet
        # Java: sheet.getLastRowNum() —— 最后一个非空行的 **0 基** 下标
        rows = sheet.max_row - 1
        if rows > 0:
            cell_map: Dict[Optional[str], int] = {}
            header = _row_of(sheet, title_num)
            for i in range(len(header)):
                cell = header[i]
                if _cell_value(cell) is not None:
                    cell_map[to_str(self.get_cell_value(header, i))] = i
                else:
                    cell_map[None] = i
            fields_map: Dict[int, ExcelField] = {}
            for field in self.get_fields():
                column = cell_map.get(field[1].name)
                if column is not None:
                    fields_map[column] = field
            for i in range(title_num + 1, rows + 1):
                row = _row_of(sheet, i)
                if _is_row_empty(row):
                    continue
                entity: Any = None
                for column, (name, attr) in fields_map.items():
                    val = self.get_cell_value(row, column)
                    # Java: 第一条有效列时才新建实例
                    if entity is None:
                        entity = self.clazz()
                    val = _convert_import_value(val, attr, self.clazz, name)
                    if is_not_empty(attr.read_converter_exp):
                        val = self.reverse_by_exp(to_str(val) or "", attr.read_converter_exp, attr.separator)
                    elif is_not_empty(attr.dict_type):
                        val = self.reverse_dict_by_exp(to_str(val) or "", attr.dict_type, attr.separator)
                    elif attr.cell_type is ColumnType.IMAGE:
                        # Java: 按 "行_列" 从 sheet 图片表取图再落盘 —— 未迁移
                        val = ""
                    _invoke_setter(entity, name, attr, val)
                entities.append(entity)  # type: ignore[arg-type]
        return entities

    # Java: public Object getCellValue(Row row, int column)
    def get_cell_value(self, row: Sequence[Any], column: int) -> Any:
        if row is None:
            return row
        val: Any = ""
        try:
            cell = row[column] if column < len(row) else None
            if cell is not None:
                raw = _cell_value(cell)
                if raw is None:
                    pass
                elif isinstance(raw, bool):
                    val = raw
                elif isinstance(raw, (int, float)):
                    if _cell_is_date(cell):
                        # Java: DateUtil.getJavaDate((Double) val)
                        val = _EXCEL_EPOCH + timedelta(days=float(raw))
                    elif float(raw) % 1 != 0:
                        # Java: new BigDecimal(val.toString())
                        val = Decimal(str(raw))
                    else:
                        # Java: new DecimalFormat("0").format(val)
                        val = str(Decimal(str(raw)).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
                else:
                    val = raw
        except Exception:  # noqa: BLE001 - Java 的 catch 直接返回当前 val
            return val
        return val

    # ------------------------------------------------------------------ 表达式

    # Java: public static String convertByExp(String propertyValue, String converterExp, String separator)
    @staticmethod
    def convert_by_exp(property_value: str, converter_exp: str, separator: str) -> str:
        return _by_exp(property_value, converter_exp, separator, source=0, target=1)

    # Java: public static String reverseByExp(String propertyValue, String converterExp, String separator)
    @staticmethod
    def reverse_by_exp(property_value: str, converter_exp: str, separator: str) -> str:
        return _by_exp(property_value, converter_exp, separator, source=1, target=0)

    # Java: public static String convertDictByExp(String dictValue, String dictType, String separator)
    @staticmethod
    def convert_dict_by_exp(dict_value: str, dict_type: str, separator: str) -> str:
        return DictUtils.get_dict_label_with_separator(dict_type, dict_value, separator)

    # Java: public static String reverseDictByExp(String dictLabel, String dictType, String separator)
    @staticmethod
    def reverse_dict_by_exp(dict_label: str, dict_type: str, separator: str) -> str:
        return DictUtils.get_dict_value_with_separator(dict_type, dict_label, separator)

    # Java: public String parseDateToStr(String dateFormat, Object val)
    @staticmethod
    def parse_date_to_str(date_format: str, val: Any) -> str:
        if val is None:
            return ""
        if isinstance(val, datetime):
            return DateUtils.parse_date_to_str(date_format, val) or ""
        if isinstance(val, date):
            # Java: DateUtils.toDate(LocalDate) —— 当天零点
            return DateUtils.parse_date_to_str(date_format, datetime(val.year, val.month, val.day)) or ""
        return str(val)

    # ------------------------------------------------------------------ 子列表

    # Java: public boolean isSubList()
    def is_sub_list(self) -> bool:
        return self._sub_fields is not None and len(self._sub_fields) > 0

    # Java: public boolean isSubListValue(T vo)
    def is_sub_list_value(self, vo: Any) -> bool:
        if not self.is_sub_list():
            return False
        return len(self.get_list_cell_value(vo)) > 0

    # Java: public Collection<?> getListCellValue(Object obj)
    def get_list_cell_value(self, obj: Any) -> List[Any]:
        try:
            assert self._sub_method is not None
            value = self._sub_method(obj)
        except Exception:  # noqa: BLE001 - Java 的 catch 返回空 ArrayList
            return []
        return list(value or [])

    # Java: public Method getSubMethod(String name, Class<?> pojoClass)
    def get_sub_method(self, name: str, pojo_class: type) -> Optional[Callable[[Any], Any]]:
        """Java 反射找 ``getXxx()``；Python 直接取同名属性.

        本项目没有任何实体声明 Collection 字段的 ``@Excel``，所以 ``_sub_fields``
        永远是 ``None``，这一整块是**休眠代码**（按迁移规则保留）。
        """
        if not hasattr(pojo_class, name):
            logger.error("获取对象异常%s", name)
            return None
        return lambda instance: getattr(instance, name)

    # ------------------------------------------------------------------ 内部

    def _is_collection_field(self, name: str) -> bool:
        """Java: ``Collection.class.isAssignableFrom(field.getType())``."""
        if self._sub_fields is None:
            return False
        return _is_list_annotation(_declared_annotation(self.clazz, name))

    def _create_row(self, index: int) -> _Row:
        """``sheet.createRow(index)`` 的等价物，并推进 ``getLastRowNum()``."""
        row = _Row(self.sheet, index, max(1, self._columns_hint()))
        if index > self._last_row_index:
            self._last_row_index = index
        return row

    def _columns_hint(self) -> int:
        count = len(self._fields)
        if self.is_sub_list() and self._sub_fields:
            count += len(self._sub_fields) - 1
        return count

    @staticmethod
    def _set_string(cell: Any, text: str) -> None:
        """Java: ``cell.setCellValue(String)`` —— 强制字符串类型.

        POI 里以 ``=`` 开头的字符串仍然只是字符串；openpyxl 会把它当公式，所以拨回来。
        """
        cell.value = text
        if getattr(cell, "data_type", None) == "f":
            cell.data_type = "s"

    def _merge(self, first_row: int, last_row: int, first_col: int, last_col: int) -> None:
        """``sheet.addMergedRegion(new CellRangeAddress(firstRow, lastRow, firstCol, lastCol))``.

        四个参数都是 **0 基**，与 POI 一致；openpyxl 用 1 基，所以整体 +1。
        """
        if last_row < first_row or last_col < first_col:
            return
        self.sheet.merge_cells(
            start_row=first_row + 1,
            end_row=last_row + 1,
            start_column=first_col + 1,
            end_column=last_col + 1,
        )

    def _close(self) -> None:
        """Java: ``IOUtils.closeQuietly(wb)`` —— openpyxl 的工作簿不需要显式关闭."""
        self._wb = None
        self._sheet = None


# --------------------------------------------------------------------------- 模块内工具


def _solid_fill(color: IndexedColor) -> PatternFill:
    return PatternFill(fill_type="solid", start_color=color.rgb, end_color=color.rgb)


def _range_ref(first_row: int, end_row: int, first_col: int, end_col: int) -> str:
    """``CellRangeAddressList`` -> ``"A2:C101"``（openpyxl 用 1 基坐标）."""
    return (
        f"{get_column_letter(first_col + 1)}{first_row + 1}:"
        f"{get_column_letter(end_col + 1)}{end_row + 1}"
    )


def _by_exp(property_value: str, converter_exp: str, separator: str, source: int, target: int) -> str:
    """``convertByExp`` / ``reverseByExp`` 的公共实现（差别只在取哪一半）.

    Java 原文 ``containsAny(propertyValue, separator)`` 判的是"值里有没有分隔符"，
    有则走多值分支（**按注解顺序**追加 ``itemArray[target] + separator``，最后
    ``stripEnd``），没有则命中即 ``return``（**不** stripEnd）。
    """
    multi = bool(separator) and any(char in property_value for char in separator)
    pieces: List[str] = []
    for item in split_regex(converter_exp, ","):
        # Java: item.split("=") —— 空串 split 出来是 [""]
        item_array = split_regex(item, "=") if item != "" else [""]
        if multi:
            for value in split_regex(property_value, _regex_escape(separator)):
                if len(item_array) > source and item_array[source] == value:
                    if len(item_array) > target:
                        pieces.append(f"{item_array[target]}{separator}")
                    break
        elif len(item_array) > source and item_array[source] == property_value:
            return item_array[target] if len(item_array) > target else ""
    return strip_end("".join(pieces), separator)


def _regex_escape(text: str) -> str:
    return re.escape(text)


def _format_double_00(value: float) -> str:
    """Java: ``DecimalFormat("######0.00")`` —— 恰好两位小数."""
    return f"{Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):f}"


def _cell_value(cell: Any) -> Any:
    """取单元格值；``None`` / openpyxl 的 ``EmptyCell`` 都返回 ``None``."""
    if cell is None:
        return None
    return getattr(cell, "value", None)


def _cell_is_date(cell: Any) -> bool:
    return bool(getattr(cell, "is_date", False))


def _row_of(sheet: Worksheet, index: int) -> Tuple[Any, ...]:
    """Java: ``sheet.getRow(index)`` —— 0 基行号，返回该行的单元格元组."""
    return tuple(sheet.cell(row=index + 1, column=column) for column in range(1, sheet.max_column + 1))


def _is_row_empty(row: Sequence[Any]) -> bool:
    """Java: ``isRowEmpty(Row)`` —— 每个单元格都是 BLANK（这里：值都是 ``None``）."""
    if row is None:
        return True
    return all(_cell_value(cell) is None for cell in row)


def _convert_import_value(val: Any, attr: Excel, entity_cls: type, name: str) -> Any:
    """``importExcel`` 里按"目标字段**声明**类型"分派的那段 ``if / else if``.

    Java 用 ``field.getType()`` 分派，Python 用 pydantic 的
    ``model_fields[name].annotation`` —— 拿到的都是声明类型，不是当前值类型。

    ``Integer`` 与 ``Long`` 在 Python 里都是 ``int``，Java 对前者用 ``toInt``、后者用
    ``toLong``；这里统一用 ``to_long``（值域更大）：本项目所有带 ``@Excel`` 的整型字段
    在 Java 里都是 ``Long``，不存在"int 字段被放宽"的情形。
    """
    field_type = _unwrap_optional(_declared_annotation(entity_cls, name))
    if field_type is str:
        text = to_str(val) or ""
        # Java: endsWith(".0") -> substringBefore(s, ".0")，把 Excel 数字 3.0 变回 "3"
        if text.endswith(".0"):
            return text[: -len(".0")]
        if is_not_empty(attr.date_format):
            return ExcelUtil.parse_date_to_str(attr.date_format, val)
        return to_str(val)
    if field_type is int:
        text = to_str(val)
        # Java: 只有 isNumeric 时才转换，否则保留 getCellValue 的原值
        if text is not None and text.isdigit():
            return to_long(val)
        return val
    if field_type is float:
        return to_double(val)
    if field_type is Decimal:
        return _to_decimal(val)
    if field_type in (datetime, date):
        if isinstance(val, str):
            return DateUtils.parse_date(val)
        if isinstance(val, float):
            return _EXCEL_EPOCH + timedelta(days=val)
        return val
    if field_type is bool:
        return to_bool(val) or False
    return val


def _invoke_setter(entity: Any, name: str, attr: Excel, val: Any) -> None:
    """Java: ``ReflectUtils.invokeSetter(entity, propertyName, val)``.

    ``propertyName`` 带 ``targetAttr`` 时是 ``"dept.deptName"`` 这种两段式，Java 逐段走
    **getter**（不是"取到 null 就新建"），中间为 null 时下一段 NPE。
    """
    if is_not_empty(attr.target_attr):
        names = attr.target_attr.split(".")
        target = getattr(entity, name, None)
        for segment in names[:-1]:
            if target is None:
                raise AttributeError(f"java.lang.NullPointerException: {name} is null")
            target = getattr(target, segment, None)
        if target is None:
            raise AttributeError(f"java.lang.NullPointerException: {name} is null")
        setattr(target, names[-1], val)
        return
    setattr(entity, name, val)


def _declared_annotation(entity_cls: type, name: str) -> Any:
    """pydantic 字段的声明注解；字段不存在时返回 ``None``."""
    fields = getattr(entity_cls, "model_fields", None)
    if not fields or name not in fields:
        return None
    return fields[name].annotation


def _unwrap_optional(annotation: Any) -> Optional[type]:
    import typing

    if annotation is None:
        return None
    if typing.get_origin(annotation) is typing.Union:
        args = [arg for arg in typing.get_args(annotation) if arg is not type(None)]
        return args[0] if len(args) == 1 and isinstance(args[0], type) else None
    return annotation if isinstance(annotation, type) else None


def _is_list_annotation(annotation: Any) -> bool:
    import typing

    if annotation is None:
        return False
    origin = typing.get_origin(annotation)
    return origin in (list, typing.List) if origin is not None else False


def _to_decimal(val: Any) -> Any:
    from app.common.core.text.convert import to_big_decimal

    return to_big_decimal(val)


__all__ = [
    "DOUBLE_FORMAT",
    "FORMULA_REGEX_STR",
    "FORMULA_STR",
    "SHEET_SIZE",
    "ExcelUtil",
]
