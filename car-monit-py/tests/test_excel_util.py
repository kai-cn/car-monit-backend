"""``ExcelUtil`` -- POI 导出/导入工具的 openpyxl 等价物.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/poi/ExcelUtil.java
#   (no Java test) -- behaviour copied from ExcelUtil.java + 每个实体的 @Excel 注解

这一层测什么
------------
Java 侧没有 ``ExcelUtilTest``（POI 的读写靠人肉点页面验证），所以这里的用例全部是
**从 Java 源码反推出来的断言**，值都写成了字面量，不是从 Python 实现里抄的：

* **列_表**：8 个实体的表头文案与顺序逐字对照 ``@Excel(name = ...)``；
* ``Type.ALL`` / ``EXPORT`` / ``IMPORT`` 的过滤效果（``SysUser`` 导出 **21** 列、
  导入模板 **18** 列 —— 差额来自 ``deptId`` 只导入、``loginIp`` / ``loginDate`` /
  ``dept.*`` 只导出）；
* ``@Excels`` 摊平：``SysUser.dept`` 在表里出现 **两次**，靠 ``target_attr`` 区分；
* ``hideColumn`` 的两条判据（``"dept"`` 整列排除 vs ``"dept.dept_name"`` 只排一条）；
* ``convertByExp`` / ``reverseByExp``，含 ``userType`` 那个**只有一个 ``=``** 的怪串；
* 落盘文件名 ``<uuid>_<sheet>.xlsx``，以及 ``AjaxResult.success(String)`` 把文件名
  塞进 **``msg``** 而不是 ``data``；
* POI 的单位换算：列宽 ``(int)((16 + 0.72) * 256) / 256 == 16.71875``。

为什么不把 ``tmp_path`` 直接塞给 ``RuoYiConfig``
------------------------------------------------
``RuoYiConfig.profile`` 是 ``@ConfigurationProperties``，Python 侧对应
``RUOYI__PROFILE`` 环境变量（Spring relaxed binding 的等价物）。用例统一走环境变量 +
``reset_settings_cache()``，这样 ``getAbsoluteFile`` 的 ``mkdirs`` 也一并被测到。
"""

from __future__ import annotations

import re
from datetime import datetime
from io import BytesIO
from typing import Any, Iterator, List, Tuple

import pytest
from openpyxl import Workbook, load_workbook

from app.common.annotation.excel import (
    BLACK,
    GREY_50_PERCENT,
    WHITE,
    ColumnType,
    Excel,
    ExcelField,
    ExcelHandlerAdapter,
    HorizontalAlignment,
    Type,
)
from app.common.core.domain.entity.sys_dict_data import SysDictData
from app.common.core.domain.entity.sys_dict_type import SysDictType
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.core.domain.entity.sys_user import SysUser
from app.common.exception.exceptions import UtilException
from app.common.utils.poi.excel_util import (
    ExcelUtil,
    _declared_excel_fields,
    _style_key_data,
    _style_key_header,
)
from app.settings import reset_settings_cache
from app.system.domain.sys_config import SysConfig
from app.system.domain.sys_index_menu import SysIndexMenu
from app.system.domain.sys_post import SysPost
from app.system.domain.sys_upgrade_info import SysUpgradeInfo

#: Java: ``ExcelUtil.encodingFilename`` —— ``UUID.randomUUID() + "_" + filename + ".xlsx"``
FILENAME_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_(?P<sheet>.+)\.xlsx$"
)

#: ``SysUser.java`` 上 21 个被 ``@Excel`` 注解的字段展开后的表头（导出，21 列）。
SYS_USER_EXPORT_HEADERS: Tuple[str, ...] = (
    "用户序号",
    "用户编码",
    "登录名称",
    "用户名称",
    "用户类型",
    "用户邮箱",
    "手机号码",
    "用户性别",
    "帐号状态",
    "最后登录IP",
    "最后登录时间",
    "证书Id",
    "证书实体Id",
    "业务id",
    "业务名称",
    "单位名称",
    "租户单位id",
    "租户单位名称",
    "角色编码",
    "部门名称",
    "部门负责人",
)

#: 导入模板少 3 列表头（``loginIp`` / ``loginDate`` / ``dept.*`` 都是 ``Type.EXPORT``），
#: 多 1 列 ``departmentId``（``Type.IMPORT``）—— 21 - 4 + 1 = 18。
SYS_USER_IMPORT_HEADERS: Tuple[str, ...] = (
    "用户序号",
    "用户编码",
    "部门编号",
    "登录名称",
    "用户名称",
    "用户类型",
    "用户邮箱",
    "手机号码",
    "用户性别",
    "帐号状态",
    "证书Id",
    "证书实体Id",
    "业务id",
    "业务名称",
    "单位名称",
    "租户单位id",
    "租户单位名称",
    "角色编码",
)


@pytest.fixture(autouse=True)
def download_dir(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Iterator[Any]:
    """把 ``ruoyi.profile`` 指到临时目录，避免往 ``D:/ruoyi/uploadPath`` 写垃圾."""
    profile = tmp_path / "uploadPath"
    monkeypatch.setenv("RUOYI__PROFILE", str(profile))
    reset_settings_cache()
    yield profile
    reset_settings_cache()


def _fields(clazz: type, type_: Type = Type.EXPORT) -> List[ExcelField]:
    """``ExcelUtil#getFields()``，先按 Java 的方式 ``init()`` 一遍把 ``type`` 设好."""
    util: ExcelUtil = ExcelUtil(clazz)
    util.init(None, "sheet", "", type_)
    return util.get_fields()


def _headers(clazz: type, type_: Type = Type.EXPORT) -> List[str]:
    return [attr.name for _name, attr in _fields(clazz, type_)]


def _read_first_sheet(path: Any) -> Any:
    return load_workbook(path).worksheets[0]


# --------------------------------------------------------------------------- 列_表


class TestColumnTables:
    """表头文案 + 顺序 == Java ``@Excel(name = ...)`` 的声明顺序.

    这些字面量全部来自 Java 源文件，改坏任何一个都会在代码评审里立刻看出来。
    """

    def test_sys_user_export_has_21_columns(self) -> None:
        assert tuple(_headers(SysUser)) == SYS_USER_EXPORT_HEADERS

    def test_sys_user_import_template_has_18_columns(self) -> None:
        assert tuple(_headers(SysUser, Type.IMPORT)) == SYS_USER_IMPORT_HEADERS

    @pytest.mark.parametrize(
        ("clazz", "expected"),
        [
            (
                SysRole,
                ("角色序号", "角色名称", "角色权限", "角色排序", "数据范围", "角色状态"),
            ),
            (
                SysDictData,
                (
                    "字典编码",
                    "字典排序",
                    "字典标签",
                    "字典键值",
                    "字典类型",
                    "是否默认",
                    "状态",
                ),
            ),
            (SysDictType, ("字典主键", "字典名称", "字典类型", "状态")),
            (SysPost, ("岗位序号", "岗位编码", "岗位名称", "岗位排序", "状态")),
            (SysConfig, ("参数主键", "参数名称", "参数键名", "参数键值", "系统内置")),
            (SysIndexMenu, ("用户ID", "菜单ID")),
        ],
    )
    def test_other_entities(self, clazz: type, expected: Tuple[str, ...]) -> None:
        assert tuple(_headers(clazz)) == expected

    def test_sys_upgrade_info_has_no_annotation_at_all(self) -> None:
        """整个实体零 ``@Excel`` —— 导出的 sheet 里一列也没有（Java 原样行为）。"""
        assert _fields(SysUpgradeInfo) == []
        assert _fields(SysUpgradeInfo, Type.IMPORT) == []

    def test_generic_entities_declare_the_same_fields_for_import(self) -> None:
        """除 ``SysUser`` 外没有 ``Type.EXPORT`` / ``Type.IMPORT`` 例外."""
        for clazz in (SysRole, SysDictData, SysDictType, SysPost, SysConfig, SysIndexMenu):
            assert _headers(clazz, Type.IMPORT) == _headers(clazz, Type.EXPORT), clazz


# --------------------------------------------------------------------------- 字段收集


class TestFieldCollection:
    def test_dept_id_is_import_only(self) -> None:
        export_names = [name for name, _attr in _fields(SysUser)]
        import_names = [name for name, _attr in _fields(SysUser, Type.IMPORT)]

        assert "dept_id" not in export_names
        assert "dept_id" in import_names

    def test_login_columns_are_export_only(self) -> None:
        export_names = [name for name, _attr in _fields(SysUser)]
        import_names = [name for name, _attr in _fields(SysUser, Type.IMPORT)]

        assert "login_ip" in export_names and "login_ip" not in import_names
        assert "login_date" in export_names and "login_date" not in import_names

    def test_excels_is_flattened_into_two_entries(self) -> None:
        """``@Excels({部门名称, 部门负责人})`` —— 同一个字段名出现两次."""
        dept_entries = [(n, a) for n, a in _fields(SysUser) if n == "dept"]

        assert [attr.name for _n, attr in dept_entries] == ["部门名称", "部门负责人"]
        assert [attr.target_attr for _n, attr in dept_entries] == ["dept_name", "leader"]
        assert all(attr.type is Type.EXPORT for _n, attr in dept_entries)

    def test_hide_column_drops_the_whole_field(self) -> None:
        util: ExcelUtil = ExcelUtil(SysUser)
        util.init(None, "sheet", "", Type.EXPORT)
        util.hide_column("dept")

        names = [name for name, _attr in util.get_fields()]

        assert "dept" not in names
        assert len(names) == 19

    def test_hide_column_can_drop_a_single_target_attr(self) -> None:
        """Java 的第二条判据是 ``field.getName() + "." + targetAttr()``."""
        util: ExcelUtil = ExcelUtil(SysUser)
        util.init(None, "sheet", "", Type.EXPORT)
        util.hide_column("dept.leader")

        remaining = [attr.name for name, attr in util.get_fields() if name == "dept"]

        assert remaining == ["部门名称"]

    def test_sort_is_a_stable_sort_ascending(self) -> None:
        """``fields.sort((a, b) -> a.sort() - b.sort())``；默认值 ``Integer.MAX_VALUE``."""

        class _Sorted:
            EXCEL_FIELDS = (
                ("b", Excel(name="B", sort=1)),
                ("a", Excel(name="A", sort=2)),
                ("c", Excel(name="C")),
            )

        util: ExcelUtil = ExcelUtil(_Sorted)
        util.init(None, "sheet", "", Type.EXPORT)

        assert [attr.name for _name, attr in util._fields] == ["B", "A", "C"]

    def test_superclass_fields_come_first(self) -> None:
        """Java: ``getSuperclass().getDeclaredFields()`` 然后 ``getDeclaredFields()``."""

        class _Base:
            EXCEL_FIELDS = (("base", Excel(name="父")),)

        class _Child(_Base):
            EXCEL_FIELDS = (("child", Excel(name="子")),)

        assert [name for name, _attr in _declared_excel_fields(_Child)] == ["base", "child"]

    def test_row_height_is_twips(self) -> None:
        """``Excel.height`` 默认 14 磅 -> ``(short)(14 * 20)`` = 280 twips."""
        util: ExcelUtil = ExcelUtil(SysUser)
        util.init(None, "sheet", "", Type.EXPORT)

        assert util.get_row_height() == 280


# --------------------------------------------------------------------------- 样式键


class TestStyleKeys:
    """样式表的键是 Java 的**字符串拼接**，所以枚举的 ``str()`` 必须是常量名."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (WHITE, "WHITE"),
            (BLACK, "BLACK"),
            (GREY_50_PERCENT, "GREY_50_PERCENT"),
            (Type.EXPORT, "EXPORT"),
            (Type.IMPORT, "IMPORT"),
            (ColumnType.NUMERIC, "NUMERIC"),
            (ColumnType.STRING, "STRING"),
            (HorizontalAlignment.CENTER, "CENTER"),
        ],
    )
    def test_enum_str_is_the_constant_name(self, value: Any, expected: str) -> None:
        assert str(value) == expected

    def test_header_key_uses_the_annotation_defaults(self) -> None:
        assert _style_key_header(Excel(name="x")) == "header_WHITE_GREY_50_PERCENT"

    def test_data_key_includes_the_cell_type(self) -> None:
        assert _style_key_data(Excel(name="x")) == "data_CENTER_BLACK_WHITE_STRING"
        assert (
            _style_key_data(Excel(name="x", cell_type=ColumnType.NUMERIC))
            == "data_CENTER_BLACK_WHITE_NUMERIC"
        )

    def test_create_styles_covers_every_field(self) -> None:
        util: ExcelUtil = ExcelUtil(SysUser)
        util.init(None, "sheet", "", Type.EXPORT)

        assert set(util._styles) == {
            "title",
            "data",
            "total",
            "header_WHITE_GREY_50_PERCENT",
            "data_CENTER_BLACK_WHITE_STRING",
            "data_CENTER_BLACK_WHITE_NUMERIC",
        }


# --------------------------------------------------------------------------- 表达式转换


class TestConvertByExp:
    """``convertByExp`` / ``reverseByExp`` —— 逐行照抄 Java 的 ``String.split`` 语义."""

    def test_single_value(self) -> None:
        assert ExcelUtil.convert_by_exp("0", "0=男,1=女,2=未知", ",") == "男"
        assert ExcelUtil.convert_by_exp("2", "0=男,1=女,2=未知", ",") == "未知"

    def test_single_equals_sign_swallows_the_rest(self) -> None:
        """``userType`` 的注解是 ``1=机构用户2专家3供应商`` —— 只有一个 ``=``.

        这不是笔误，是 ``SysUser.java`` 的原样。于是 ``"1"`` 变成整串
        ``"机构用户2专家3供应商"``，其它值（``"2"`` / ``"3"``）原样返回空串。
        """
        exp = "1=机构用户2专家3供应商"

        assert ExcelUtil.convert_by_exp("1", exp, ",") == "机构用户2专家3供应商"
        assert ExcelUtil.convert_by_exp("2", exp, ",") == ""
        # reverse 只会命中 ``机构用户2专家3供应商`` 这一整串
        assert ExcelUtil.reverse_by_exp("机构用户2专家3供应商", exp, ",") == "1"
        assert ExcelUtil.reverse_by_exp("专家", exp, ",") == ""

    def test_unknown_value_returns_empty_string(self) -> None:
        assert ExcelUtil.convert_by_exp("9", "0=男,1=女", ",") == ""

    def test_reverse_round_trip(self) -> None:
        exp = "0=正常,1=停用"

        assert ExcelUtil.reverse_by_exp("正常", exp, ",") == "0"
        assert ExcelUtil.reverse_by_exp("停用", exp, ",") == "1"
        assert ExcelUtil.reverse_by_exp("未知", exp, ",") == ""

    def test_multi_value_uses_the_separator_and_strip_end(self) -> None:
        """值里含分隔符时走多值分支，最后 ``StringUtils.stripEnd(result, separator)``.

        ⚠️ 多值分支**按注解顺序**逐个匹配，所以输出永远按 ``converterExp`` 的顺序，
        与入参里的顺序无关 —— ``"1,0"`` 得到的是 ``"男,女"``，不是 ``"女,男"``。
        这是 Java ``convertByExp`` 的原样行为。
        """
        exp = "0=男,1=女,2=未知"

        assert ExcelUtil.convert_by_exp("0,1", exp, ",") == "男,女"
        assert ExcelUtil.convert_by_exp("1,0,2", exp, ",") == "男,女,未知"
        assert ExcelUtil.convert_by_exp("1,0", exp, ",") == "男,女"

    def test_multi_value_reverse(self) -> None:
        exp = "0=男,1=女,2=未知"

        assert ExcelUtil.reverse_by_exp("男,女", exp, ",") == "0,1"
        assert ExcelUtil.reverse_by_exp("女,男", exp, ",") == "0,1"

    def test_custom_separator(self) -> None:
        assert ExcelUtil.convert_by_exp("0|1", "0=男,1=女", "|") == "男|女"


# --------------------------------------------------------------------------- 文件名


class TestFilename:
    def test_encoding_filename_is_uuid_underscore_sheet(self) -> None:
        filename = ExcelUtil.encoding_filename("用户数据")
        match = FILENAME_PATTERN.match(filename)

        assert match is not None
        assert match.group("sheet") == "用户数据"

    def test_two_calls_never_collide(self) -> None:
        assert ExcelUtil.encoding_filename("x") != ExcelUtil.encoding_filename("x")


# --------------------------------------------------------------------------- 导出落盘


class TestExportToFile:
    def _user(self) -> SysUser:
        return SysUser(
            user_id=2,
            user_no=1001,
            user_name="ry",
            nick_name="若依",
            user_type="1",
            email="ry@example.com",
            phonenumber="13800000000",
            sex="0",
            status="0",
            login_ip="127.0.0.1",
            login_date=datetime(2026, 10, 22, 10, 30, 0),
            dept=SysDept(dept_name="研发部", leader="若依"),
        )

    def test_returns_the_filename_in_msg_not_data(self, download_dir: Any) -> None:
        """``AjaxResult.success(String)`` 命中的是 ``success(String msg)`` 重载."""
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")

        assert result["code"] == 200
        assert "data" not in result
        assert FILENAME_PATTERN.match(result["msg"]) is not None
        assert result["msg"].endswith("_用户数据.xlsx")

    def test_file_lands_in_the_download_directory(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")

        assert (download_dir / "download" / result["msg"]).is_file()

    def test_sheet_name_and_header_row(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert sheet.title == "用户数据"
        assert tuple(cell.value for cell in sheet[1]) == SYS_USER_EXPORT_HEADERS

    def test_first_data_row(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])
        row = [cell.value for cell in sheet[2]]

        # NUMERIC 列写成数字，不是字符串
        assert row[0] == 2
        assert row[1] == 1001
        assert row[2] == "ry"
        assert row[3] == "若依"
        # readConverterExp
        assert row[4] == "机构用户2专家3供应商"
        assert row[7] == "男"
        assert row[8] == "正常"
        assert row[9] == "127.0.0.1"
        # dateFormat = "yyyy-MM-dd HH:mm:ss"
        assert row[10] == "2026-10-22 10:30:00"
        # @Excels 的两条 targetAttr
        assert row[19] == "研发部"
        assert row[20] == "若依"

    def test_column_width_is_the_poi_truncated_value(self, download_dir: Any) -> None:
        """``(int)((16 + 0.72) * 256) / 256`` = ``4280 / 256`` = 16.71875."""
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert sheet.column_dimensions["A"].width == pytest.approx(16.71875)
        # 最后登录时间（第 11 列 = K）width = 30 -> (int)(30.72 * 256) / 256
        assert sheet.column_dimensions["K"].width == pytest.approx(30.71875)

    def test_prompt_becomes_a_data_validation(self, download_dir: Any) -> None:
        """只有 ``userId`` / ``userNo`` 两列带 ``prompt``."""
        result = ExcelUtil(SysUser).export_excel([self._user()], "用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert len(sheet.data_validations.dataValidation) == 2

    def test_empty_list_still_writes_the_header(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).export_excel([], "用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert tuple(cell.value for cell in sheet[1]) == SYS_USER_EXPORT_HEADERS
        assert sheet.max_row == 1

    def test_zero_columns_still_writes_an_empty_sheet(self, download_dir: Any) -> None:
        """``SysUpgradeInfo`` 没有 ``@Excel`` —— Java 侧同样只出一个空 sheet."""
        result = ExcelUtil(SysUpgradeInfo).export_excel([SysUpgradeInfo(id="u-1")], "系统升级信息数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert sheet.title == "系统升级信息数据"
        # 没有任何列 —— 表头行也是空的。openpyxl 不会把"无值无样式"的空单元格落盘，
        # 所以断言"全表找不到任何非空值"（Java 侧的 xlsx 里同样只有一列空白）
        assert [
            cell.value for row in sheet.iter_rows() for cell in row if cell.value is not None
        ] == []
        assert result["msg"].endswith("_系统升级信息数据.xlsx")

    def test_save_failure_raises_util_exception(
        self, download_dir: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Java: ``catch (Exception e) { throw new UtilException(...) }``."""

        def _boom(*_args: Any, **_kwargs: Any) -> None:
            raise OSError("disk full")

        monkeypatch.setattr(Workbook, "save", _boom)

        with pytest.raises(UtilException):
            ExcelUtil(SysUser).export_excel([self._user()], "用户数据")

    def test_with_title_adds_a_merged_title_row(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).export_excel_with_title([self._user()], "用户数据", "用户报表")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert sheet.cell(row=1, column=1).value == "用户报表"
        assert tuple(cell.value for cell in sheet[2]) == SYS_USER_EXPORT_HEADERS
        assert "A1:U1" in {str(region) for region in sheet.merged_cells.ranges}


# --------------------------------------------------------------------------- 导入模板


class TestImportTemplate:
    def test_template_has_18_columns(self, download_dir: Any) -> None:
        result = ExcelUtil(SysUser).import_template_excel("用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert tuple(cell.value for cell in sheet[1]) == SYS_USER_IMPORT_HEADERS
        assert sheet.max_row == 1

    def test_template_has_no_data_rows(self, download_dir: Any) -> None:
        """``init(None, ...)`` + ``Type.IMPORT`` -> ``writeSheet`` 不写数据区."""
        result = ExcelUtil(SysUser).import_template_excel("用户数据")
        sheet = _read_first_sheet(download_dir / "download" / result["msg"])

        assert [cell.value for cell in sheet[2]] == [None] * 18


# --------------------------------------------------------------------------- 导入


def _workbook_bytes(headers: List[str], rows: List[List[Any]], title: str = "用户数据") -> BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


class TestImport:
    def test_reverses_read_converter_exp(self) -> None:
        stream = _workbook_bytes(
            ["登录名称", "用户名称", "用户性别", "帐号状态"],
            [["new1", "新用户", "男", "正常"]],
        )

        result = ExcelUtil(SysUser).import_excel(stream)

        assert len(result) == 1
        assert result[0].user_name == "new1"
        assert result[0].nick_name == "新用户"
        assert result[0].sex == "0"
        assert result[0].status == "0"

    def test_reads_the_import_only_department_id(self) -> None:
        stream = _workbook_bytes(["登录名称", "部门编号"], [["new1", 103]])

        result = ExcelUtil(SysUser).import_excel(stream)

        assert result[0].dept_id == 103

    def test_export_only_columns_are_ignored(self) -> None:
        """``最后登录IP`` / ``最后登录时间`` / ``部门名称`` 都不在 IMPORT 字段表里."""
        stream = _workbook_bytes(
            ["登录名称", "最后登录IP", "最后登录时间", "部门名称", "部门负责人"],
            [["new1", "10.0.0.1", "2026-10-22 10:30:00", "研发部", "若依"]],
        )

        result = ExcelUtil(SysUser).import_excel(stream)

        assert result[0].user_name == "new1"
        assert result[0].login_ip is None
        assert result[0].login_date is None
        assert result[0].dept is None

    def test_blank_rows_are_skipped(self) -> None:
        stream = _workbook_bytes(
            ["登录名称", "用户名称"],
            [["new1", "新用户"], [None, None], ["new2", "第二个"]],
        )

        result = ExcelUtil(SysUser).import_excel(stream)

        assert [user.user_name for user in result] == ["new1", "new2"]

    def test_unknown_headers_are_ignored(self) -> None:
        stream = _workbook_bytes(["登录名称", "不存在的列"], [["new1", "x"]])

        result = ExcelUtil(SysUser).import_excel(stream)

        assert len(result) == 1
        assert result[0].user_name == "new1"

    def test_numeric_cell_loses_the_trailing_dot_zero(self) -> None:
        """Excel 里的 ``1001.0`` 要变回字符串 ``"1001"``（``endsWith(".0")`` 分支）."""
        stream = _workbook_bytes(["登录名称"], [[1001.0]])

        result = ExcelUtil(SysUser).import_excel(stream)

        assert result[0].user_name == "1001"

    def test_xls_is_rejected(self) -> None:
        """``WorkbookFactory.create`` 能吃 ``.xls``；openpyxl 只认 OOXML.

        Java 侧没有这个限制 —— 差异已记入 ``COMPATIBILITY.md`` §37。
        """
        stream = BytesIO(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 512)

        with pytest.raises(UtilException):
            ExcelUtil(SysUser).import_excel(stream)

    def test_stream_is_closed_even_on_failure(self) -> None:
        stream = BytesIO(b"not an xlsx")

        with pytest.raises(UtilException):
            ExcelUtil(SysUser).import_excel(stream)

        assert stream.closed is True


# --------------------------------------------------------------------------- Response 变体


class _Sink:
    """``HttpServletResponse`` 的最小替身（本工程无调用点，按迁移规则仍要覆盖）."""

    def __init__(self) -> None:
        self.content_type: str = ""
        self.buffer = BytesIO()

    def set_content_type(self, value: str) -> None:
        self.content_type = value

    def get_output_stream(self) -> BytesIO:
        return self.buffer


class TestResponseVariants:
    def test_export_writes_the_same_bytes_to_the_stream(self) -> None:
        sink = _Sink()

        ExcelUtil(SysUser).export_excel_to_sink(
            sink,
            [SysUser(user_id=2, user_name="ry")],
            "用户数据",
            "",
        )

        assert sink.content_type == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        sheet = load_workbook(BytesIO(sink.buffer.getvalue())).worksheets[0]
        assert tuple(cell.value for cell in sheet[1]) == SYS_USER_EXPORT_HEADERS

    def test_stream_variant_swallows_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``exportExcel(HttpServletResponse)`` 的 ``catch`` 只记日志，**不抛**."""

        def _boom(*_args: Any, **_kwargs: Any) -> None:
            raise OSError("broken pipe")

        monkeypatch.setattr(Workbook, "save", _boom)

        ExcelUtil(SysUser).export_excel_to_sink(_Sink(), [], "用户数据", "")

    def test_import_template_to_sink(self) -> None:
        sink = _Sink()

        ExcelUtil(SysUser).import_template_excel_to_sink(sink, "用户数据", "")

        sheet = load_workbook(BytesIO(sink.buffer.getvalue())).worksheets[0]
        assert tuple(cell.value for cell in sheet[1]) == SYS_USER_IMPORT_HEADERS


# --------------------------------------------------------------------------- 默认值守卫


class TestAnnotationDefaults:
    """``@Excel`` 的默认值一旦被"顺手改掉"，导出就会静默变形 —— 这里钉住."""

    def test_excel_defaults(self) -> None:
        attr = Excel()

        assert attr.name == ""
        assert attr.sort == 2147483647
        assert attr.height == pytest.approx(14)
        assert attr.width == pytest.approx(16)
        assert attr.scale == -1
        assert attr.rounding_mode == 6
        assert attr.separator == ","
        assert attr.cell_type is ColumnType.STRING
        assert attr.align is HorizontalAlignment.CENTER
        assert attr.type is Type.ALL
        assert attr.is_export is True
        assert attr.need_merge is False
        assert attr.is_statistics is False
        assert attr.combo == ()
        assert attr.args == ()
        # Java: ``handler()`` 的默认值就是 ``ExcelHandlerAdapter`` 本身（哨兵）
        assert attr.handler is ExcelHandlerAdapter

    def test_default_colors_are_poi_indexed_colors(self) -> None:
        attr = Excel()

        assert attr.header_color is WHITE
        assert attr.header_background_color is GREY_50_PERCENT
        assert attr.background_color is WHITE
        assert attr.color is BLACK

    def test_has_handler_is_false_by_default(self) -> None:
        assert Excel().has_handler() is False
