"""自定义导出 Excel 数据注解.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/annotation/Excel.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/annotation/Excels.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelHandlerAdapter.java

Java 的注解挂在 **字段** 上，Python 没有注解，所以每个实体类声明一个类变量
``EXCEL_FIELDS``，元素是 :class:`Excel` 实例，顺序 = Java 里 ``getDeclaredFields()``
的顺序。``ExcelUtil`` 读它的方式与 Java 读 ``Field.getAnnotation(Excel.class)`` 等价。

``@Excels`` 被摊平
------------------
Java 的 ``@Excels({@Excel(...), @Excel(...)})``（一个字段多条注解，靠 ``targetAttr``
区分）在 :data:`EXCEL_FIELDS` 里写成 **两条并列** 的 :class:`Excel`。这不是妥协：
``ExcelUtil#getFields()`` 本来就把 ``@Excels`` 的每一项 append 进同一个扁平
``fields`` 列表，摊平后列表内容与顺序完全相同。本项目只有一处 ``@Excels``
（``SysUser.dept``：部门名称 + 部门负责人）。

枚举的 ``str()`` 必须等于名字
-----------------------------
样式表的主键是 ``StringUtils.format("header_{}_{}", attr.headerColor(),
attr.headerBackgroundColor())`` 这类**字符串拼接**，Java 拼进去的是
``Enum.toString()``，也就是 **枚举常量名**（``"WHITE"`` / ``"GREY_50_PERCENT"`` /
``"CENTER"`` / ``"NUMERIC"``）。所以下面每个枚举都重写了 ``__str__``，否则
Python 默认会拼出 ``"IndexedColors.WHITE"``，样式键就与 Java 对不上了。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, Tuple


class _NamedEnum(Enum):
    """Java ``Enum.toString()`` 返回常量名；Python 默认返回 ``类名.常量名``。"""

    def __str__(self) -> str:  # pragma: no cover - 一行
        return self.name


# Java: Excel.Type —— 字段类型（0：导出导入；1：仅导出；2：仅导入）
class Type(IntEnum):
    ALL = 0
    EXPORT = 1
    IMPORT = 2

    def __str__(self) -> str:
        return self.name


# Java: Excel.ColumnType —— 导出类型（0数字 1字符串 2图片 3文本）
class ColumnType(IntEnum):
    NUMERIC = 0
    STRING = 1
    IMAGE = 2
    TEXT = 3

    def __str__(self) -> str:
        return self.name


class HorizontalAlignment(_NamedEnum):
    """``org.apache.poi.ss.usermodel.HorizontalAlignment``（只列注解默认值用到的 + 邻近项）."""

    GENERAL = 0
    LEFT = 1
    CENTER = 2
    RIGHT = 3
    FILL = 4
    JUSTIFY = 5
    CENTER_SELECTION = 6
    DISTRIBUTED = 7


class IndexedColor:
    """``org.apache.poi.ss.usermodel.IndexedColors`` 的一个常量.

    ``index`` 与 POI 一致（用于 ``setFillForegroundColor`` / ``setFontColor``）；
    ``rgb`` 是 POI 调色板里同一位置的 ARGB，openpyxl 需要它。

    只声明注解默认值实际引用到的三个常量（``headerBackgroundColor`` =
    ``GREY_50_PERCENT``、``headerColor`` / ``backgroundColor`` = ``WHITE``、
    ``color`` = ``BLACK``）—— ``Excel`` 的四个颜色属性默认值恰好就是这三个。
    """

    __slots__ = ("index", "rgb", "name")

    def __init__(self, index: int, rgb: str) -> None:
        self.index = index
        self.rgb = rgb
        # Java: Enum.name() —— 样式键里拼的就是它
        self.name = ""

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"IndexedColor({self.name})"

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, IndexedColor) and other.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)


def _indexed_color(index: int, rgb: str, name: str) -> IndexedColor:
    color = IndexedColor(index, rgb)
    color.name = name
    return color


# Java: IndexedColors.BLACK — index 8, 0x000000
BLACK = _indexed_color(8, "FF000000", "BLACK")
# Java: IndexedColors.WHITE — index 9, 0xFFFFFF
WHITE = _indexed_color(9, "FFFFFFFF", "WHITE")
# Java: IndexedColors.GREY_50_PERCENT — index 22, 0x808080
GREY_50_PERCENT = _indexed_color(22, "FF808080", "GREY_50_PERCENT")


class ExcelHandlerAdapter:
    """自定义数据处理器接口.

    ``Excel.handler()`` 的默认值就是它本身，``ExcelUtil`` 用它判断"有没有自定义处理器"：
    ``!attr.handler().equals(ExcelHandlerAdapter.class)``。用 Python 的类做同一个哨兵。

    本项目**没有任何**字段声明 ``handler``，所以 ``dataFormatHandlerAdapter`` 永远走不到。
    """

    # Java: Object format(Object value, String[] args, Cell cell, Workbook wb)
    def format(self, value: Any, args: Tuple[str, ...], cell: Any, wb: Any) -> Any:  # pragma: no cover
        return value


#: Java: ``Integer.MAX_VALUE`` —— ``sort()`` 的默认值，意味着"不排序，保持声明顺序"。
UNSORTED = 2147483647

#: Java: ``BigDecimal.ROUND_HALF_EVEN`` —— ``roundingMode()`` 的默认值。
ROUND_HALF_EVEN = 6


@dataclass(frozen=True)
class Excel:
    """``com.ruoyi.common.annotation.Excel`` —— 27 个属性逐一对齐.

    属性名用 snake_case，与 Java 的 camelCase 一一对应（``dateFormat`` ->
    ``date_format``）。默认值与 Java 注解声明完全相同，**不要**"顺手"改：
    ``scale = -1`` 表示"不做 BigDecimal 格式化"，``sort = Integer.MAX_VALUE``
    表示"排在所有显式排序字段之后"。
    """

    #: 导出时在 excel 中排序（默认 ``Integer.MAX_VALUE``；``sorted()`` 是稳定排序）
    sort: int = UNSORTED
    #: 导出到 Excel 中的名字
    name: str = ""
    #: 日期格式, 如 ``yyyy-MM-dd``
    date_format: str = ""
    #: 字典类型（如 ``sys_user_sex``）
    dict_type: str = ""
    #: 读取内容转表达式（如 ``0=男,1=女,2=未知``）
    read_converter_exp: str = ""
    #: 分隔符，读取字符串组内容
    separator: str = ","
    #: BigDecimal 精度，默认 -1（不开启）
    scale: int = -1
    #: BigDecimal 舍入规则，默认 ``ROUND_HALF_EVEN``
    rounding_mode: int = ROUND_HALF_EVEN
    #: 每列高度
    height: float = 14
    #: 每列宽度
    width: float = 16
    #: 文字后缀，如 ``%`` 让 ``90`` 变成 ``90%``
    suffix: str = ""
    #: 值为空时的默认值
    default_value: str = ""
    #: 提示信息
    prompt: str = ""
    #: 只能选择不能输入的列内容
    combo: Tuple[str, ...] = ()
    #: 是否需要纵向合并单元格（应对 list 集合单元格）
    need_merge: bool = False
    #: 是否导出数据（false = 只出表头，留给用户手填）
    is_export: bool = True
    #: 另一个类中的属性名称，支持多级获取（以小数点隔开）
    target_attr: str = ""
    #: 是否自动统计（末尾追加一行合计）
    is_statistics: bool = False
    #: 导出类型
    cell_type: ColumnType = ColumnType.STRING
    #: 列头背景颜色
    header_background_color: IndexedColor = field(default=GREY_50_PERCENT)
    #: 列头字体颜色
    header_color: IndexedColor = field(default=WHITE)
    #: 单元格背景颜色
    background_color: IndexedColor = field(default=WHITE)
    #: 单元格字体颜色
    color: IndexedColor = field(default=BLACK)
    #: 对齐方式
    align: HorizontalAlignment = HorizontalAlignment.CENTER
    #: 自定义数据处理器（默认值就是"没有"，见 :class:`ExcelHandlerAdapter`）
    handler: type = ExcelHandlerAdapter
    #: 自定义数据处理器参数
    args: Tuple[str, ...] = ()
    #: 字段类型（ALL / EXPORT / IMPORT）
    type: Type = Type.ALL

    # ------------------------------------------------------------------ 便捷判断

    def has_handler(self) -> bool:
        """Java: ``!attr.handler().equals(ExcelHandlerAdapter.class)``."""
        return self.handler is not ExcelHandlerAdapter


#: 实体类上的注解表。``ExcelUtil`` 按 MRO 由基类到子类收集，等价于 Java 的
#: ``clazz.getSuperclass().getDeclaredFields()`` + ``clazz.getDeclaredFields()``。
#:
#: 每一项是 ``(属性名, Excel)``，对应 Java 的 ``Object[]{ Field, Excel }`` ——
#: ``Field`` 在 Python 里就是 pydantic 字段的 ``snake_case`` 名字。
ExcelField = Tuple[str, Excel]
ExcelFields = Tuple[ExcelField, ...]

#: ``@Excels`` 的别名：一个字段多条注解，在 :data:`ExcelFields` 里写成两条并列项
#: （同一个属性名），靠 ``target_attr`` 区分。
Excels = Tuple[Excel, ...]

#: 实体类声明注解用的类变量名（``ClassVar`` 保证 pydantic 不把它当字段）。
EXCEL_FIELDS_NAME = "EXCEL_FIELDS"

__all__ = [
    "BLACK",
    "ColumnType",
    "EXCEL_FIELDS_NAME",
    "Excel",
    "ExcelField",
    "ExcelFields",
    "ExcelHandlerAdapter",
    "Excels",
    "GREY_50_PERCENT",
    "HorizontalAlignment",
    "IndexedColor",
    "ROUND_HALF_EVEN",
    "Type",
    "UNSORTED",
    "WHITE",
]
