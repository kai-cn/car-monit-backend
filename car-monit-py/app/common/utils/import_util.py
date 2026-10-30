"""Excel 导入工具（``com.ruoyi.web.util.ImportSysUtil`` / ``ImportUtil`` / 两个实体）.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportSysUtil.java
# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportUtil.java
# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportEntity.java
# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/util/ImportErrorEntity.java

这套工具是 2020 年的老代码，只有 ``CarInfoController#doImport`` 与
``CarExceptRecordController#importData`` 两处调用。迁移时按以下原则照抄：

1. **表头校验**逐列严格 ``equals``（不 trim、不忽略大小写）；
2. **数据行**从第 1 行（0 基，即 Excel 第 2 行）开始；首列出现 ``break`` 或
   ``结束`` 立即停止；遇到"整行为空"也停止（Java 是 ``row`` 为 ``null`` 触发 NPE
   被 catch 住 ``break``）；
3. **单元格取值**：日期 → ``yyyy/MM/dd``（``getCellFormatValue07``）或
   ``yyyy-MM-dd HH:mm:ss``（``getCellFormatValue08``）；数字 → ``DecimalFormat("#.##")``
   （**四舍六入五成双**，与 Java 默认 ``RoundingMode.HALF_EVEN`` 一致）；
   其余按字符串；最后整体 ``trim``；
4. ``getErrorBO(row, ...)`` 里写的是 ``rowNo = row + 1``，而调用方传的已经是
   ``index + 1`` —— 于是报错行号比真实行号**大 1**。这是现网行为，照抄。

已知差异（见 ``COMPATIBILITY.md``）
-----------------------------------
Java 用 ``WorkbookFactory``，``.xls``（HSSF）与 ``.xlsx``（XSSF）都能读；Python 侧
``.xlsx`` 走 openpyxl，``.xls`` 需要可选依赖 ``xlrd``（未列入 ``requirements.txt``）。
两个调用方都先判断 ``.xlsx`` 后缀，所以实际运行路径只用到 XSSF 分支。
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, BinaryIO, Dict, List, Optional, Sequence, Type

from app.common.exception.exceptions import UtilException

# --------------------------------------------------------------------------- 正则

#: Java: ``ImportUtil.xiaoshu`` —— 2 小数或整数
XIAOSHU = r"^(-?\d+)(\.\d+)?$"

#: Java: ``ImportUtil.znumber`` —— 3 整数
ZNUMBER = r"^[0-9]*$"

#: Java: ``ImportUtil.eLtime2`` —— 4 日期
E_LTIME2 = r"[0-9]{4}-[0-9]{2}-[0-9]{2}"

#: Java: ``ImportUtil.idCard`` —— 5 身份证
ID_CARD = r"^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])\d{3}([0-9]|X|x)$"

#: Java: ``ImportUtil.elTimeYM`` —— 6 年月
EL_TIME_YM = r"^\d{4}(-|/|\.)\d{1,2}$"

#: Java: ``ImportUtil.dateTimeRegex`` —— 8 年月日时分秒
DATE_TIME_REGEX = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"

#: Java: ``ImportUtil.VERIFY_NUMBER_TYPE`` —— 7 数值类型
VERIFY_NUMBER_TYPE = r"^(\-|\+)?\d+(\.\d+)?$"


def _is_null_str(value: Any) -> str:
    """Java: ``ImportSysUtil#isNull(Object)`` —— ``null`` -> ``""``，**不 trim**."""
    if value is None:
        return ""
    return str(value)


def _trim(value: str) -> str:
    """Java ``String.trim()``：只削 ``<= U+0020`` 的字符。"""
    return value.strip("".join(chr(code) for code in range(0x21)))


def _decimal_format_2(value: float) -> str:
    """Java: ``new DecimalFormat("#.##").format(double)``.

    ``#.##`` 不保留末尾的 0，整数不带小数点；舍入模式是 Java 默认的
    ``HALF_EVEN``（不是很多端口误用的 ``HALF_UP``）。
    """
    quantized = Decimal(repr(float(value))).quantize(Decimal("0.01"), ROUND_HALF_EVEN)
    text = format(quantized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        text = "0"
    return text


class ImportEntity:
    """Java: ``class ImportEntity implements Serializable`` —— 导入列定义."""

    __slots__ = ("col_name", "col_prop", "valad_res")

    def __init__(
        self, col_name: str = "", col_prop: str = "", valad_res: str = ""
    ) -> None:
        #: 表头
        self.col_name = col_name
        #: 列（实体属性名，``camelCase``）
        self.col_prop = col_prop
        #: 校验规则 1 必填 / 2 数字 / 3 整数 / 4 日期 / 5 身份证 / 6 年月 / 7 数值 / 8 年月日时分秒
        #: 多个用逗号分隔
        self.valad_res = valad_res


class ImportErrorEntity:
    """Java: ``class ImportErrorEntity implements Serializable`` —— 单行错误."""

    __slots__ = ("row_no", "col_name", "message")

    def __init__(
        self, row_no: int = 0, col_name: Optional[str] = None, message: Optional[str] = None
    ) -> None:
        #: 第几行
        self.row_no = row_no
        #: 列名
        self.col_name = col_name
        #: 错误信息
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """``@Data`` 的 JSON 形态（``AjaxResult.error("error", errorList)`` 用它）。"""
        return {"rowNo": self.row_no, "colName": self.col_name, "message": self.message}


class ImportSysUtil:
    """Java: ``class ImportSysUtil`` —— POI 解析封装（只实现被用到的 07 分支 + 完整 03）."""

    # -------------------------------------------------------------- 03（.xls）

    def get_hssf_sheet03(self, stream: BinaryIO, index: int) -> Any:
        """Java: ``HSSFSheet getHSSFSheet03(InputStream, int)``."""
        try:
            import xlrd  # noqa: F401 —— 可选依赖
        except ImportError as error:  # pragma: no cover —— 见模块 docstring
            raise UtilException(
                "读取 .xls 需要可选依赖 xlrd（pip install xlrd）；"
                "本项目的导入接口只接受 .xlsx"
            ) from error
        import xlrd

        book = xlrd.open_workbook(file_contents=stream.read())
        return book.sheet_by_index(index)

    def col_vda_excel03(self, sheet: Any, cols_name: Sequence[str]) -> bool:
        """Java: ``boolean colVdaExcel03(HSSFSheet, String[])``."""
        if sheet.nrows == 0:
            return False
        for index, expected in enumerate(cols_name):
            if index >= sheet.ncols:
                return False
            if expected != self._get_cell_format_value03(sheet.cell_value(0, index), None):
                return False
        return True

    def data_rtn_excel03(self, sheet: Any, cols_name: Sequence[str]) -> List[List[str]]:
        """Java: ``List<String[]> dataRtnExcel03(HSSFSheet, String[])``."""
        rows: List[List[str]] = []
        for row_index in range(1, sheet.nrows):
            values = list(sheet.row_values(row_index))
            first = self._get_cell_format_value03(
                values[0] if values else "", None
            )
            if first == "break" or first == "结束":
                break
            row: List[str] = []
            for column in range(len(cols_name)):
                cell = values[column] if column < len(values) else ""
                row.append(_is_null_str(self._get_cell_format_value03(cell, None)))
            rows.append(row)
        return rows

    def _get_cell_format_value03(self, value: Any, date_mode: Optional[bool]) -> str:  # noqa: D401
        """Java: ``private String getCellFormatValue03(HSSFCell)``（xlrd 值已是 Python 类型）."""
        if value is None or value == "":
            return ""
        if isinstance(value, (datetime, date)):
            return value.strftime("%Y/%m/%d")
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, float):
            return _decimal_format_2(value)
        return _trim(str(value))

    # -------------------------------------------------------------- 07（.xlsx）

    def get_xssf_sheet(self, stream: BinaryIO, index: int) -> Any:
        """Java: ``XSSFSheet getXSSFSheet(InputStream, int)``."""
        from openpyxl import load_workbook

        workbook = load_workbook(stream, data_only=True)
        return workbook.worksheets[index]

    def col_vda_excel07(self, sheet: Any, cols_name: Sequence[str]) -> bool:
        """Java: ``boolean colVdaExcel07(XSSFSheet, String[])`` —— 校验第 0 行表头."""
        return self._col_vda(sheet, cols_name, 0)

    def col_vda_excel08(self, sheet: Any, cols_name: Sequence[str], num: int) -> bool:
        """Java: ``boolean colVdaExcel08(XSSFSheet, String[], Integer)``."""
        return self._col_vda(sheet, cols_name, num)

    def col_vda_excel07_row3(self, sheet: Any, cols_name: Sequence[str]) -> bool:
        """Java: ``boolean colVdaExcel07Row3(XSSFSheet, String[])`` —— 表头在第 4 行."""
        return self._col_vda(sheet, cols_name, 3)

    def _col_vda(self, sheet: Any, cols_name: Sequence[str], row_index: int) -> bool:
        if row_index + 1 > sheet.max_row:
            # Java: sheet.getRow(num) == null -> false
            return False
        for index, expected in enumerate(cols_name):
            cell = sheet.cell(row=row_index + 1, column=index + 1)
            if expected != self.get_cell_format_value07(cell):
                return False
        return True

    def data_rtn_excel07(self, sheet: Any, cols_name: Sequence[str]) -> List[List[str]]:
        """Java: ``List<String[]> dataRtnExcel07(XSSFSheet, String[])``."""
        return self._data_rtn(sheet, cols_name, 1)

    def data_rtn_excel07_row3(self, sheet: Any, cols_name: Sequence[str]) -> List[List[str]]:
        """Java: ``List<String[]> dataRtnExcel07Row3(XSSFSheet, String[])``.

        注意 Java 的 ``rowCount = getLastRowNum() - 1``：最后一行会被**吃掉**，照抄。
        """
        return self._data_rtn(sheet, cols_name, 4, last_row_delta=-1)

    def data_rtn_excel08(
        self,
        sheet: Any,
        cols_name: Sequence[str],
        row_nume: Sequence[int],
        num: int,
    ) -> List[List[str]]:
        """Java: ``List<String[]> dataRtnExcel08(XSSFSheet, String[], Integer[], Integer)``.

        ``row_nume`` 里的列号**不做取值**（保持默认空串），其余列用
        :meth:`get_cell_format_value08`（日期带时分秒）。
        """
        rows: List[List[str]] = []
        last_row = sheet.max_row
        for row_index in range(num, last_row + 1):
            current = self._row_values(sheet, row_index, len(cols_name))
            if current is None:
                break
            if current[0] == "break" or current[0] == "结束":
                break
            row: List[str] = []
            for column in range(len(cols_name)):
                if column in row_nume:
                    row.append("")
                else:
                    cell = sheet.cell(row=row_index + 1, column=column + 1)
                    row.append(_is_null_str(self.get_cell_format_value08(cell)))
            rows.append(row)
        return rows

    def _data_rtn(
        self,
        sheet: Any,
        cols_name: Sequence[str],
        start_row: int,
        last_row_delta: int = 0,
    ) -> List[List[str]]:
        rows: List[List[str]] = []
        last_row = sheet.max_row + last_row_delta
        for row_index in range(start_row, last_row + 1):
            values = self._row_values(sheet, row_index, len(cols_name))
            if values is None:
                break
            if values[0] == "break" or values[0] == "结束":
                break
            rows.append([_is_null_str(value) for value in values])
        return rows

    def _row_values(
        self, sheet: Any, row_index: int, column_count: int
    ) -> Optional[List[str]]:
        """读取一行；行不存在返回 ``None``（对应 Java 的 ``row == null`` -> break）."""
        if row_index + 1 > sheet.max_row:
            return None
        values: List[str] = []
        for column in range(column_count):
            cell = sheet.cell(row=row_index + 1, column=column + 1)
            values.append(self.get_cell_format_value07(cell))
        return values

    def get_cell_format_value07(self, cell: Any) -> str:
        """Java: ``private String getCellFormatValue07(XSSFCell)`` —— 日期按 ``yyyy/MM/dd``."""
        return self._cell_value(cell, "%Y/%m/%d")

    def get_cell_format_value08(self, cell: Any) -> str:
        """Java: ``private String getCellFormatValue08(XSSFCell)`` —— 日期带时分秒."""
        return self._cell_value(cell, "%Y-%m-%d %H:%M:%S")

    def _cell_value(self, cell: Any, date_format: str) -> str:
        if cell is None or cell.value is None:
            return ""
        value = cell.value
        if isinstance(value, (datetime, date)):
            return value.strftime(date_format)
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return _trim(_decimal_format_2(value))
        return _trim(str(value))

    # -------------------------------------------------------------- 校验 / 报错

    def get_error_bo(self, row: int, col_name: Optional[str], message: str) -> ImportErrorEntity:
        """Java: ``ImportErrorEntity getErrorBO(int row, String colName, String message)``.

        ``rowNo = row + 1`` —— 调用方传的已是 ``index + 1``，所以行号会多 1，照抄。
        """
        return ImportErrorEntity(row_no=row + 1, col_name=col_name, message=message)

    def validate_value_regex(self, value: str, regex: str) -> bool:
        """Java: ``boolean validateValueRegex(String value, String regex)``."""
        return re.fullmatch(regex, value) is not None


def is_null(value: Any) -> str:
    """Java: ``ImportUtil.isNull(Object)`` —— ``null`` -> ``""``，否则 ``toString().trim()``."""
    if value is None:
        return ""
    return _trim(str(value))


def _keep_empty_string(model: Type[Any], prop: str) -> bool:
    """空串是否应当原样写入：``String`` 字段保留 ``""``，数值/日期字段留 ``None``。

    Java 走 ``JSONObject.toJavaObject``：``""`` 落到 ``String`` 上是 ``""``，落到
    ``Long`` / ``BigDecimal`` / ``Date`` 上是 ``null``。
    """
    annotations = getattr(model, "model_fields", None)
    if not annotations or prop not in annotations:
        return True
    annotation = str(annotations[prop].annotation)
    return "str" in annotation or "Any" in annotation


def import_excel(
    error_list: List[ImportErrorEntity],
    bo_list: Sequence[ImportEntity],
    index: int,
    excel_values: Sequence[str],
    model_cls: Type[Any],
    util: Optional[ImportSysUtil] = None,
) -> Optional[Any]:
    """Java: ``ImportUtil.importExcel(List, List, int, String[], Class)``.

    只有 ``error_list`` **整体为空**时才返回对象（Java 同样是全局判空，不是逐行）。
    """
    sys_util = util or ImportSysUtil()
    obj_map: Dict[str, str] = {}
    for position, bo in enumerate(bo_list):
        value = is_null(excel_values[position] if position < len(excel_values) else None)
        obj_map[bo.col_prop] = value
        if is_null(bo.valad_res) == "":
            continue
        for rule in bo.valad_res.split(","):
            if rule == "1":
                # 必填
                if value == "":
                    error_list.append(sys_util.get_error_bo(index + 1, bo.col_name, "不能为空"))
            if value == "":
                continue
            if rule == "2":
                if not sys_util.validate_value_regex(value, XIAOSHU):
                    error_list.append(sys_util.get_error_bo(index + 1, bo.col_name, "不是小数"))
            elif rule == "3":
                if not sys_util.validate_value_regex(value, ZNUMBER):
                    error_list.append(
                        sys_util.get_error_bo(index + 1, bo.col_name, "不是正整数")
                    )
            elif rule == "4":
                if not sys_util.validate_value_regex(value, E_LTIME2):
                    error_list.append(
                        sys_util.get_error_bo(
                            index + 1, bo.col_name, "日期格式（年-月-日）不正确"
                        )
                    )
            elif rule == "5":
                if not sys_util.validate_value_regex(value, ID_CARD):
                    error_list.append(
                        sys_util.get_error_bo(index + 1, bo.col_name, "身份证号码不正确")
                    )
            elif rule == "6":
                if not sys_util.validate_value_regex(value, EL_TIME_YM):
                    error_list.append(
                        sys_util.get_error_bo(
                            index + 1, bo.col_name, "日期格式（年-月）不正确"
                        )
                    )
            elif rule == "7":
                if not sys_util.validate_value_regex(value, VERIFY_NUMBER_TYPE):
                    error_list.append(sys_util.get_error_bo(index + 1, bo.col_name, "不是数值"))
            elif rule == "8":
                if not sys_util.validate_value_regex(value, DATE_TIME_REGEX):
                    error_list.append(
                        sys_util.get_error_bo(
                            index + 1, bo.col_name, "日期格式（年月日时分秒）不正确"
                        )
                    )
    if error_list:
        return None
    payload = {
        prop: value
        for prop, value in obj_map.items()
        if value != "" or _keep_empty_string(model_cls, prop)
    }
    return model_cls(**payload)


__all__ = [
    "DATE_TIME_REGEX",
    "EL_TIME_YM",
    "E_LTIME2",
    "ID_CARD",
    "ImportEntity",
    "ImportErrorEntity",
    "ImportSysUtil",
    "VERIFY_NUMBER_TYPE",
    "XIAOSHU",
    "ZNUMBER",
    "import_excel",
    "is_null",
]
