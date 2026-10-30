"""代码生成业务服务层.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/service/IGenTableService.java
# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/service/GenTableServiceImpl.java

三个 ``generatorCode`` / ``previewCode`` 的**初始化顺序各不相同**
--------------------------------------------------------------
这不是笔误，四处代码里五个 ``init*`` 的调用顺序都不一样：

======================================  ==========================================
方法                                     顺序
======================================  ==========================================
``previewCode``                          filter -> richText -> upload -> dict -> link
``generatorCode(String)``（自定义路径）    dict -> richText -> filter -> link -> upload
``generatorCode(String, ZipOutputStream)``  dict -> upload -> richText -> link -> filter
======================================  ==========================================

顺序影响 ``initLinkTableInfo`` 里读到的 ``dictTypeCamelCase`` / 过滤后的列集合，
所以必须逐处照抄，不能抽成一个公共的 ``_init_all``。

``isMybatisPlus`` 在本项目里是 ``true``
---------------------------------------
``application.yml`` 的 ``generator-code.mybatis-plus.enable`` 写死为 ``true``，
于是 ``VelocityUtils.getTemplateList`` 走 ``vmplus/`` 那套模板（不是 ``vm/``）。
``/tool/gen/preview`` 的响应键因此是 ``vmplus/java/domain.java.vm`` 这种形式，
前端 ``gen/index.vue`` 按这个键取要展示的文件。

``validateEdit`` 里有一处**永远为假**的分支
------------------------------------------
``else if (GenConstants.TPL_SUB.equals(genTable.getTplCategory()))`` 嵌在
``if (TPL_TREE.equals(tplCategory))`` 内部 —— 外面已经要求 ``tplCategory == "tree"``，
里面再判 ``== "sub"`` 永远不成立。于是**主子表从来不校验子表名与外键名**。
这两条错误文案（``关联子表的表名不能为空`` / ``子表关联的外键名不能为空``）是死代码。
照抄：把这个分支保留在原位，不要"修"到外层去。

``importGenTable`` 会把任何异常包成 ``CustomException``
----------------------------------------------------
``catch (Exception e) { throw new CustomException("导入失败：" + e.getMessage()); }``
—— 连 ``NullPointerException`` 也包。所以导入失败时 ``msg`` 是
``"导入失败：null"``（NPE 的 ``getMessage()`` 为 null，字符串拼接成 ``"null"``）。
"""

from __future__ import annotations

import json
import os
import zipfile
from io import BytesIO
from typing import Any, Dict, List, Optional, Sequence, Union

from app.common.constant import constants as Constants
from app.common.constant.gen_constants import (
    PARENT_MENU_ID,
    PARENT_MENU_NAME,
    TPL_SUB,
    TPL_TREE,
    TREE_CODE,
    TREE_NAME,
    TREE_PARENT_CODE,
)
from app.common.exception.exceptions import CustomException
from app.common.utils.json_utils import to_json_string
from app.common.utils.security_utils import get_username
from app.common.utils.string_utils import (
    is_empty,
    is_not_blank,
    is_not_empty,
    is_not_null,
    join,
    to_camel_case,
)
from app.settings import get_settings
from app.generator.domain.dictionary_info import DictionaryInfo
from app.generator.domain.gen_column_dialog import GenColumnDialog
from app.generator.domain.gen_table import GenTable
from app.generator.domain.gen_table_column import GenTableColumn
from app.generator.domain.generate_rich_text_info import GenerateRichTextInfo
from app.generator.domain.generate_upload_info import GenerateUploadInfo
from app.generator.domain.link_table_field import LinkTableField
from app.generator.mapper.gen_table_column_mapper import GenTableColumnMapper
from app.generator.mapper.gen_table_mapper import GenTableMapper
from app.generator.service.gen_table_column_service import (
    GenTableColumnService,
    get_gen_table_column_service,
)
from app.generator.util import gen_utils as GenUtils
from app.generator.util.enumeration.link_table_filed_type_enum import LinkTableFiledTypeEnum
from app.generator.util.velocity_engine import get_template
from app.generator.util.velocity_utils import get_file_name, get_template_list, prepare_context

#: Java: ``private static final List<String> FILTER_COLUMN_NAME_LIST``
#: （``static{}`` 块里逐个 ``add``，顺序即列表顺序）。
FILTER_COLUMN_NAME_LIST: List[str] = ["sort", "epsId", "delFlag", "tenantId"]


class GenTableService:
    """Java: ``IGenTableService`` (impl: ``GenTableServiceImpl``)."""

    def __init__(
        self,
        table_mapper: Optional[GenTableMapper] = None,
        column_mapper: Optional[GenTableColumnMapper] = None,
        column_service: Optional[GenTableColumnService] = None,
    ) -> None:
        self._table_mapper = table_mapper or GenTableMapper()
        self._column_mapper = column_mapper or GenTableColumnMapper()
        #: Java: ``@Autowired private IGenTableColumnService tableColumnService``
        self._column_service = column_service or get_gen_table_column_service()

    # ------------------------------------------------------------------ 读

    # Java: GenTable selectGenTableById(Long id)
    def select_gen_table_by_id(self, table_id: Optional[int]) -> Optional[GenTable]:
        """查业务信息 + 用 ``options`` 回填树 / 菜单字段。

        ``setTableFromOptions`` 在 ``genTable`` 为 ``null`` 时会 NPE（Java 同样），
        所以查不到时这里也抛 ``AttributeError``。
        """
        gen_table = self._table_mapper.select_gen_table_by_id(table_id)
        self.set_table_from_options(gen_table)
        return gen_table

    # Java: List<GenTable> selectGenTableList(GenTable genTable)
    def select_gen_table_list(self, gen_table: GenTable) -> List[GenTable]:
        return self._table_mapper.select_gen_table_list(gen_table)

    # Java: List<GenTable> selectDbTableList(GenTable genTable)
    def select_db_table_list(self, gen_table: GenTable) -> List[GenTable]:
        return self._table_mapper.select_db_table_list(gen_table)

    # Java: List<GenTable> selectDbTableListByNames(String[] tableNames)
    def select_db_table_list_by_names(self, table_names: Sequence[str]) -> List[GenTable]:
        return self._table_mapper.select_db_table_list_by_names(table_names)

    # Java: List<GenTable> selectGenTableAll()
    def select_gen_table_all(self) -> List[GenTable]:
        return self._table_mapper.select_gen_table_all()

    # ------------------------------------------------------------------ 写

    # Java: @Transactional void updateGenTable(GenTable genTable)
    def update_gen_table(self, gen_table: GenTable) -> None:
        """``params`` 整体序列化进 ``options``，再逐个更新列。

        Java 没有判空就 ``for (GenTableColumn ... : genTable.getColumns())`` ——
        ``columns`` 为 null 时是 NPE（-> 500）。这里保留（``None`` 迭代会抛
        ``TypeError``）。
        """
        options = to_json_string(gen_table.params)
        gen_table.options = options
        row = self._table_mapper.update_gen_table(gen_table)
        if row > 0:
            for gen_table_column in gen_table.columns:  # type: ignore[union-attr]
                self._column_mapper.update_gen_table_column(gen_table_column)

    # Java: @Transactional void deleteGenTableByIds(Long[] tableIds)
    def delete_gen_table_by_ids(self, table_ids: Sequence[int]) -> None:
        self._table_mapper.delete_gen_table_by_ids(table_ids)
        self._column_mapper.delete_gen_table_column_by_ids(table_ids)

    # Java: @Transactional void importGenTable(List<GenTable> tableList)
    def import_gen_table(self, table_list: Sequence[GenTable]) -> None:
        """导入表结构：``initTable`` -> 插入主表 -> 读物理列 -> 逐列插入。

        整体 try/catch，任何异常（含 NPE）都变成
        ``CustomException("导入失败：" + e.getMessage())``。
        """
        oper_name = get_username()  # Java: SecurityUtils.getUsername()
        try:
            for table in table_list:
                table_name = table.table_name
                GenUtils.init_table(table, oper_name)
                row = self._table_mapper.insert_gen_table(table)
                if row > 0:
                    # 保存列信息
                    gen_table_columns = self._column_mapper.select_db_table_columns_by_name(
                        table_name  # type: ignore[arg-type]
                    )
                    for column in gen_table_columns:
                        GenUtils.init_column_field(column, table)
                        self._column_mapper.insert_gen_table_column(column)
        except Exception as error:  # noqa: BLE001 —— Java 侧的 catch (Exception e) 就是这个范围
            raise CustomException("导入失败：" + _java_exception_message(error)) from error

    # ------------------------------------------------------------------ 预览 / 生成

    # Java: Map<String, String> previewCode(Long tableId)
    def preview_code(self, table_id: Optional[int]) -> Dict[str, str]:
        """预览代码 —— 返回 ``LinkedHashMap``（键序 = 模板列表序）。

        键是**模板路径**（``vmplus/java/domain.java.vm``），值是渲染后的全文。
        """
        data_map: Dict[str, str] = {}
        # 查询表信息
        table = self._table_mapper.select_gen_table_by_id(table_id)
        # 过滤字段信息
        self.init_filter_column_info(table)  # type: ignore[arg-type]
        # 初始化富文本信息
        self.init_rich_text_info(table)  # type: ignore[arg-type]
        # 初始化附件上传信息
        self.init_upload_info(table)  # type: ignore[arg-type]
        # 将字典的key转换成驼峰类型
        self.dictionary_key_to_camel_case(table)  # type: ignore[arg-type]
        # 初始化关联表信息
        self.init_link_table_info(table)  # type: ignore[arg-type]

        # 设置主子表信息
        self.set_sub_table(table)  # type: ignore[arg-type]
        # 设置主键列信息
        self.set_pk_column(table)  # type: ignore[arg-type]
        # Java: VelocityInitializer.initVelocity() —— Python 侧模板引擎无需初始化

        context = prepare_context(table)  # type: ignore[arg-type]

        # 获取模板列表
        templates = get_template_list(table.tpl_category, self._is_mybatis_plus())  # type: ignore[union-attr]
        for template in templates:
            # 渲染模板
            data_map[template] = get_template(template).merge(context)
        return data_map

    # Java: byte[] downloadCode(String tableName)
    # Java: byte[] downloadCode(String[] tableNames)
    def download_code(self, table_names: Union[str, Sequence[str]]) -> bytes:
        """生成代码（下载方式）—— Java 两个重载合并成一个（按入参类型分派）。

        返回 zip 字节流；zip 条目名由 ``VelocityUtils.getFileName`` 决定。
        """
        output_stream = BytesIO()
        with zipfile.ZipFile(output_stream, "w", zipfile.ZIP_DEFLATED) as zip_file:
            if isinstance(table_names, str):
                self._generator_code_to_zip(table_names, zip_file)
            else:
                for table_name in table_names:
                    self._generator_code_to_zip(table_name, zip_file)
        return output_stream.getvalue()

    # Java: void generatorCode(String tableName) —— 写自定义路径
    def generator_code(self, table_name: str) -> None:
        """生成代码到 ``genPath``，**跳过** 4 类前端/SQL 模板。

        跳过的是 ``sql.vm`` / ``api.js.vm`` / ``index.vue.vm`` /
        ``index-tree.vue.vm`` —— 注意 ``containsAny`` 是子串匹配
        ``index.vue.vm``，``index-form.vue.vm`` 不含这个子串，所以
        ``index-form.vue.vm`` **会**被写出去。
        """
        # 查询表信息
        table = self._table_mapper.select_gen_table_by_name(table_name)
        # 将字典的key转换成驼峰类型
        self.dictionary_key_to_camel_case(table)  # type: ignore[arg-type]
        # 初始化富文本信息
        self.init_rich_text_info(table)  # type: ignore[arg-type]
        # 过滤字段信息
        self.init_filter_column_info(table)  # type: ignore[arg-type]
        # 初始化关联表信息
        self.init_link_table_info(table)  # type: ignore[arg-type]
        # 初始化附件上传信息
        self.init_upload_info(table)  # type: ignore[arg-type]

        # 设置主子表信息
        self.set_sub_table(table)  # type: ignore[arg-type]
        # 设置主键列信息
        self.set_pk_column(table)  # type: ignore[arg-type]

        context = prepare_context(table)  # type: ignore[arg-type]

        # 获取模板列表
        templates = get_template_list(table.tpl_category, self._is_mybatis_plus())  # type: ignore[union-attr]
        for template in templates:
            if not _contains_any(template, "sql.vm", "api.js.vm", "index.vue.vm", "index-tree.vue.vm"):
                # 渲染模板
                rendered = get_template(template).merge(context)
                path = self.get_gen_path(table, template)  # type: ignore[arg-type]
                try:
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write(rendered)
                except OSError as error:
                    raise CustomException(
                        "渲染模板失败，表名：" + str(table.table_name)  # type: ignore[union-attr]
                    ) from error

    # Java: @Transactional void synchDb(String tableName)
    def synch_db(self, table_name: str) -> None:
        """同步数据库：补新列、删已消失的列。

        ``table.getColumns()`` 为 null 时 Java NPE；这里同样直接迭代。
        """
        table = self._table_mapper.select_gen_table_by_name(table_name)
        table_columns = table.columns  # type: ignore[union-attr]
        table_column_names = [column.column_name for column in table_columns]

        db_table_columns = self._column_mapper.select_db_table_columns_by_name(table_name)
        if not db_table_columns:
            raise CustomException("同步数据失败，原表结构不存在")
        db_table_column_names = [column.column_name for column in db_table_columns]

        for column in db_table_columns:
            if column.column_name not in table_column_names:
                GenUtils.init_column_field(column, table)  # type: ignore[arg-type]
                self._column_mapper.insert_gen_table_column(column)

        del_columns = [
            column for column in table_columns if column.column_name not in db_table_column_names
        ]
        if del_columns:
            self._column_mapper.delete_gen_table_columns(del_columns)

    # ------------------------------------------------------------------ 校验

    # Java: void validateEdit(GenTable genTable)
    def validate_edit(self, gen_table: GenTable) -> None:
        """修改保存参数校验 —— **只校验树表**。

        ``TLP_SUB`` 的那两条校验嵌在树表分支内部，永远不成立（见模块 docstring），
        这里原样保留，不要挪到外层 —— 挪了就是"主子表编辑突然开始报错"。
        """
        if TPL_TREE == gen_table.tpl_category:
            options = to_json_string(gen_table.params)
            params_obj = _parse_object(options)
            if is_empty(_get_string(params_obj, TREE_CODE)):
                raise CustomException("树编码字段不能为空")
            elif is_empty(_get_string(params_obj, TREE_PARENT_CODE)):
                raise CustomException("树父编码字段不能为空")
            elif is_empty(_get_string(params_obj, TREE_NAME)):
                raise CustomException("树名称字段不能为空")
            elif TPL_SUB == gen_table.tpl_category:
                # 死分支：外层已限定 TPL_TREE，此处永远进不来。照抄（见 docstring）。
                if is_empty(gen_table.sub_table_name):
                    raise CustomException("关联子表的表名不能为空")
                elif is_empty(gen_table.sub_table_fk_name):
                    raise CustomException("子表关联的外键名不能为空")

    # ------------------------------------------------------------------ 公开工具方法

    # Java: public void setPkColumn(GenTable table)
    def set_pk_column(self, table: GenTable) -> None:
        """挑主键列：第一个 ``isPk()`` 的列，否则取第 0 列。

        ``columns`` 为空时 Java 在 ``get(0)`` 处抛
        ``IndexOutOfBoundsException``；``columns`` 为 null 时在 for 处 NPE。
        ``TPL_SUB`` 还会对子表做同样的事，``subTable`` 为 null 时 NPE。
        """
        for column in table.columns:  # type: ignore[union-attr]
            if column.pk:
                table.pk_column = column
                break
        if table.pk_column is None:
            table.pk_column = table.columns[0]  # type: ignore[index]
        if TPL_SUB == table.tpl_category:
            sub_table = table.sub_table
            for column in sub_table.columns:  # type: ignore[union-attr]
                if column.pk:
                    sub_table.pk_column = column  # type: ignore[union-attr]
                    break
            if sub_table.pk_column is None:  # type: ignore[union-attr]
                sub_table.pk_column = sub_table.columns[0]  # type: ignore[index,union-attr]

    # Java: public void setSubTable(GenTable table)
    def set_sub_table(self, table: GenTable) -> None:
        sub_table_name = table.sub_table_name
        if is_not_empty(sub_table_name):
            table.sub_table = self._table_mapper.select_gen_table_by_name(sub_table_name)

    # Java: public void setTableFromOptions(GenTable genTable)
    def set_table_from_options(self, gen_table: GenTable) -> None:
        """把 ``options`` 里的树 / 菜单字段回填到实体上.

        ``JSONObject.parseObject(null)`` 返回 null -> ``isNotNull`` 为假 -> 什么都不做；
        查不到表（``genTable == null``）时 Java 在 ``getOptions()`` 处 NPE。
        """
        params_obj = _parse_object(gen_table.options)
        if is_not_null(params_obj):
            gen_table.tree_code = _get_string(params_obj, TREE_CODE)
            gen_table.tree_parent_code = _get_string(params_obj, TREE_PARENT_CODE)
            gen_table.tree_name = _get_string(params_obj, TREE_NAME)
            gen_table.parent_menu_id = _get_string(params_obj, PARENT_MENU_ID)
            gen_table.parent_menu_name = _get_string(params_obj, PARENT_MENU_NAME)

    # Java: public static String getGenPath(GenTable table, String template)
    @staticmethod
    def get_gen_path(table: GenTable, template: str) -> str:
        """``genPath == "/"`` 时落到**当前工作目录**下的 ``src/``.

        Java 用 ``System.getProperty("user.dir")`` —— 是进程启动目录，不是项目根。
        这里用 ``os.getcwd()``，语义相同。
        """
        gen_path = table.gen_path
        if "/" == gen_path:
            return os.getcwd() + os.sep + "src" + os.sep + get_file_name(template, table)
        return str(gen_path) + os.sep + get_file_name(template, table)

    # ------------------------------------------------------------------ 私有：初始化

    # Java: private void initFilterColumnInfo(GenTable genTable)
    @staticmethod
    def init_filter_column_info(gen_table: GenTable) -> None:
        """生成 ``filterColumnList``：剔除无 ``javaField`` / String 型 id / 四个内部列."""
        column_list = gen_table.columns
        if not column_list:
            return

        filter_column_list: List[GenTableColumn] = []
        for column in column_list:
            if is_empty(column.java_field):
                continue
            # 过滤id为String类型的字段
            if (
                Constants.COLUMN_PRIMARY_KEY == column.java_field
                and Constants.STRING_CLASS_KEY == column.java_type
            ):
                continue
            if column.java_field in FILTER_COLUMN_NAME_LIST:
                continue
            filter_column_list.append(column)
        gen_table.filter_column_list = filter_column_list

    # Java: private void initRichTextInfo(GenTable table)
    @staticmethod
    def init_rich_text_info(table: GenTable) -> None:
        """``htmlType == "editor"`` 的列 -> ``richTextInfo``.

        注意装列的是 ``columnList``（不是 ``richTextColumnList``），字段名就叫
        ``columnList`` —— 与 ``GenerateUploadInfo`` 的 ``uploadColumn`` 不对称。
        """
        column_list = table.columns
        if not column_list:
            return
        rich_text_column_list = [column for column in column_list if "editor" == column.html_type]
        generate_rich_text_info = GenerateRichTextInfo()
        if rich_text_column_list:
            generate_rich_text_info.rich_text_count = len(rich_text_column_list)
            generate_rich_text_info.column_list = rich_text_column_list
        else:
            generate_rich_text_info.rich_text_count = 0
        table.rich_text_info = generate_rich_text_info

    # Java: private void initUploadInfo(GenTable table)
    @staticmethod
    def init_upload_info(table: GenTable) -> None:
        """``htmlType == "fileUpload"`` 的列 -> ``uploadInfo``（字段名 ``uploadFiledNames``）."""
        column_list = table.columns
        if not column_list:
            return
        upload_column_list = [column for column in column_list if "fileUpload" == column.html_type]
        generate_upload_info = GenerateUploadInfo()
        if upload_column_list:
            java_field_name_list = [column.java_field for column in upload_column_list]
            generate_upload_info.upload_count = len(upload_column_list)
            generate_upload_info.upload_column = upload_column_list
            generate_upload_info.upload_filed_names = join(java_field_name_list, ",")
        else:
            generate_upload_info.upload_count = 0
        table.upload_info = generate_upload_info

    # Java: private void initLinkTableInfo(GenTable genTable)
    def init_link_table_info(self, gen_table: GenTable) -> None:
        """关联表 / 对话框信息（``columnDialogInfo``）.

        ``majorLinkFieldInfo`` 用 ``Optional.get()`` 取值 —— 找不到对应映射时抛
        ``NoSuchElementException``（本实现抛 ``LookupError``），最终 500。
        """
        column_list = gen_table.columns
        if not column_list:
            return

        # 关联表信息列表
        link_table_column_list = [
            column
            for column in column_list
            if column.link_table_id is not None and is_not_blank(column.field_map_string)
        ]

        # 初始化对话框查询显示列表数据信息
        self.init_dialog_query_show_data(link_table_column_list)

        # 多选对话框列表 / 单选对话框列表
        checkbox_column_list: List[GenTableColumn] = []
        radio_column_list: List[GenTableColumn] = []

        # 全部字段列表 / 全部自定义字段列表 / 全部表中字段列表
        all_field_list: List[LinkTableField] = []
        all_custom_field_list: List[LinkTableField] = []
        all_table_field_list: List[LinkTableField] = []

        for column in link_table_column_list:
            # 单选对话框
            if "1" == column.single_selection:
                radio_column_list.append(column)
            # 多选对话框
            if "1" == column.multiple_selections:
                checkbox_column_list.append(column)

            # 字段映射
            link_table_field_list = _parse_array(column.field_map_string, LinkTableField)

            table_field_list = [
                field_info
                for field_info in link_table_field_list
                if LinkTableFiledTypeEnum.TABLE == field_info.field_type
            ]
            custom_field_list = [
                field_info
                for field_info in link_table_field_list
                if LinkTableFiledTypeEnum.CUSTOM_FIELD == field_info.field_type
            ]

            if table_field_list:
                column.table_field_list = table_field_list
                all_table_field_list.extend(table_field_list)
                all_field_list.extend(table_field_list)

            if custom_field_list:
                column.custom_field_list = custom_field_list
                all_custom_field_list.extend(custom_field_list)
                all_field_list.extend(custom_field_list)

            # 设置生成关联表标识
            column.generate_link_table_flag = "1"
            # 设置字段主要映射关系 —— Java: findFirst().get()，找不到即抛
            column.major_link_field_info = _first_required(
                [
                    data
                    for data in table_field_list
                    if column.column_id is not None
                    and data.current_table_file_id is not None
                    and column.column_id == data.current_table_file_id
                ],
                "majorLinkFieldInfo",
            )

        # 设置表字段信息
        self.init_table_field_info(all_table_field_list)
        # 设置关联表字段信息
        self.init_link_table_field_info(all_field_list)

        # 设置对话框信息
        column_dialog = GenColumnDialog()
        column_dialog.dialog_column_list = link_table_column_list
        column_dialog.dialog_number = len(link_table_column_list) if link_table_column_list else 0
        column_dialog.check_box_column_list = checkbox_column_list
        column_dialog.checkbox_number = len(checkbox_column_list) if checkbox_column_list else 0
        column_dialog.radio_column_list = radio_column_list
        column_dialog.radio_number = len(radio_column_list) if radio_column_list else 0
        column_dialog.table_field_list = all_table_field_list
        column_dialog.custom_field_list = all_custom_field_list
        column_dialog.field_list = all_field_list
        gen_table.column_dialog_info = column_dialog

    # Java: private void initTableFieldInfo(List<LinkTableField> allTableFieldList)
    def init_table_field_info(self, all_table_field_list: List[LinkTableField]) -> None:
        if not all_table_field_list:
            return
        table_id_list = [field.current_table_file_id for field in all_table_field_list]
        table_column_list = self._column_service.select_gen_table_column_list_by_table_column_id_list(
            table_id_list
        )
        if table_column_list:
            table_column_map = {column.column_id: column for column in table_column_list}
            for field_info in all_table_field_list:
                gen_table_column = table_column_map.get(field_info.current_table_file_id)
                if gen_table_column is not None:
                    field_info.table_file_info = gen_table_column

    # Java: private void initLinkTableFieldInfo(List<LinkTableField> allFieldList)
    def init_link_table_field_info(self, all_field_list: List[LinkTableField]) -> None:
        if not all_field_list:
            return
        link_field_id_list = [field.link_table_field_id for field in all_field_list]
        link_field_list = self._column_service.select_gen_table_column_list_by_table_column_id_list(
            link_field_id_list
        )
        if link_field_list:
            column_map = {column.column_id: column for column in link_field_list}
            for field_info in all_field_list:
                gen_table_column = column_map.get(field_info.link_table_field_id)
                if gen_table_column is not None:
                    field_info.link_table_field_info = gen_table_column

    # Java: private void initDialogQueryShowData(List<GenTableColumn> linkTableColumnList)
    def init_dialog_query_show_data(self, link_table_column_list: List[GenTableColumn]) -> None:
        if not link_table_column_list:
            return
        for column in link_table_column_list:
            dialog_search_column_ids = column.dialog_search_column_ids
            dialog_list_column_ids = column.dialog_list_column_ids
            link_table_id = column.link_table_id

            # dialog查询字段信息
            if is_not_empty(dialog_search_column_ids):
                column.dialog_search_column_list = (
                    self._column_service.select_gen_table_column_list_by_table_column_ids(
                        dialog_search_column_ids
                    )
                )
            # dialog展示字段信息
            if is_not_empty(dialog_list_column_ids):
                column.dialog_show_column_list = (
                    self._column_service.select_gen_table_column_list_by_table_column_ids(
                        dialog_list_column_ids
                    )
                )
            # 关联表信息
            link_table = self._table_mapper.select_gen_table_by_id(link_table_id)
            # 设置主键列信息（linkTable 为 None 时 Java NPE）
            self.set_pk_column(link_table)  # type: ignore[arg-type]
            column.link_table = link_table

    # Java: private void dictionaryKeyToCamelCase(GenTable table)
    @staticmethod
    def dictionary_key_to_camel_case(table: Optional[GenTable]) -> None:
        """有 ``dictType`` 的列补 ``dictTypeCamelCase``，并汇总成 ``dictionaryInfoList``.

        ``dictionaryListKeySuffix`` 只要 ``columns`` 非空就设（哪怕一个 dictType 都没有），
        因为模板里 ``#set($dictKey="$column.dictTypeCamelCase$dictionaryListKeySuffix")``
        依赖它。
        """
        if table is not None and table.columns:
            column_list = table.columns
            dictionary_info_list: List[DictionaryInfo] = []
            for column in column_list:
                if not is_not_empty(column.dict_type):
                    continue
                dict_type_camel_case = to_camel_case(column.dict_type)
                column.dict_type_camel_case = dict_type_camel_case
                dictionary_info_list.append(
                    DictionaryInfo(
                        dictionary_key=column.dict_type,
                        dictionary_key_camel_case=dict_type_camel_case,
                    )
                )

            # 设置字典信息
            if dictionary_info_list:
                table.dictionary_info_list = dictionary_info_list
                dict_key_list = [info.dictionary_key for info in dictionary_info_list]
                table.dictionary_info_string = join(dict_key_list, ",")

            # 设置 生成代码-字典列表键后缀
            table.dictionary_list_key_suffix = Constants.GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX

    # ------------------------------------------------------------------ 私有：zip

    # Java: private void generatorCode(String tableName, ZipOutputStream zip)
    def _generator_code_to_zip(self, table_name: str, zip_file: zipfile.ZipFile) -> None:
        """往 zip 里追加一张表的全部模板产物（顺序 = 模板列表序）。"""
        # 查询表信息
        table = self._table_mapper.select_gen_table_by_name(table_name)
        # 将字典的key转换成驼峰类型
        self.dictionary_key_to_camel_case(table)  # type: ignore[arg-type]
        # 初始化附件上传信息
        self.init_upload_info(table)  # type: ignore[arg-type]
        # 初始化富文本信息
        self.init_rich_text_info(table)  # type: ignore[arg-type]
        # 初始化关联表信息
        self.init_link_table_info(table)  # type: ignore[arg-type]
        # 过滤字段信息
        self.init_filter_column_info(table)  # type: ignore[arg-type]

        # 设置主子表信息
        self.set_sub_table(table)  # type: ignore[arg-type]
        # 设置主键列信息
        self.set_pk_column(table)  # type: ignore[arg-type]

        context = prepare_context(table)  # type: ignore[arg-type]

        # 获取模板列表
        templates = get_template_list(table.tpl_category, self._is_mybatis_plus())  # type: ignore[union-attr]
        for template in templates:
            rendered = get_template(template).merge(context)
            try:
                # 添加到zip
                zip_file.writestr(get_file_name(template, table), rendered)  # type: ignore[arg-type]
            except OSError:
                # Java: catch (IOException e) { log.error("渲染模板失败，表名：" + ...) }
                # —— 只记日志、继续下一个模板。
                continue

    # ------------------------------------------------------------------ 私有：配置

    @staticmethod
    def _is_mybatis_plus() -> bool:
        """Java: ``@Value("${generator-code.mybatis-plus.enable:false}") private boolean isMybatisPlus``.

        本项目 ``application.yml`` 里写死 ``true``，于是走 ``vmplus/`` 模板。
        读不到配置时按 Java 的默认值 ``false`` 兜底。
        """
        settings = get_settings()
        return bool(settings.generator_code.mybatis_plus.enable)


# --------------------------------------------------------------------------- JSON 辅助


def _contains_any(text: str, *values: Optional[str]) -> bool:
    """Java: ``StringUtils.containsAny(CharSequence cs, CharSequence... searchCharSequences)``."""
    return any(value is not None and value != "" and value in text for value in values)


def _parse_object(text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Java: ``JSONObject.parseObject(String)`` —— ``null`` / 空串 / 非对象都返回 ``None``.

    fastjson2 对空串返回 null（不抛异常），对非法 JSON 抛 ``JSONException``；
    这里同样：空 -> ``None``，非法 -> 让 ``json.JSONDecodeError`` 冒泡（-> 500）。
    """
    if text is None or text == "":
        return None
    parsed = json.loads(text)
    return parsed if isinstance(parsed, dict) else None


def _get_string(params_obj: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    """Java: ``JSONObject.getString(String key)`` —— 缺失返回 ``null``，非字符串走 ``toString``."""
    if params_obj is None:
        return None
    value = params_obj.get(key)
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _parse_array(text: Optional[str], model: type) -> List[Any]:
    """Java: ``JSON.parseArray(String text, Class<T> clazz)``.

    ``null`` / 空串得到空列表；每个元素按 ``model`` 构造（未知字段忽略，
    与 fastjson2 的默认 ``ignoreUnknown`` 一致）。
    """
    if text is None or text == "":
        return []
    parsed = json.loads(text)
    if not isinstance(parsed, list):
        return []
    return [model(**item) if isinstance(item, dict) else model() for item in parsed]


def _first_required(items: List[Any], name: str) -> Any:
    """Java: ``stream().findFirst().get()`` —— 空集合抛 ``NoSuchElementException``.

    ``initLinkTableInfo`` 靠它取 ``majorLinkFieldInfo``：关联列在
    ``fieldMapString`` 里找不到自己的 ``currentTableFileId`` 时直接 500。
    """
    if not items:
        raise LookupError(f"NoSuchElementException: {name}")
    return items[0]


def _java_exception_message(error: BaseException) -> str:
    """Java: ``e.getMessage()`` 参与字符串拼接时的样子.

    ``String.valueOf((Object) null)`` 得到 ``"null"``，所以 NPE 拼出来的文案是
    ``"导入失败：null"``，**不是** ``"导入失败：java.lang.NullPointerException: ..."``。
    本工程用 ``AttributeError`` 承担 NPE 的角色（见 ``app.config.exception_handlers``），
    所以这条判据必须与 ``_java_message`` 一致：文案是哨兵就是 ``null``。

    不直接 import ``_java_message``：那个模块反向依赖了整个 ``app.api`` 包，
    service 层引它会造成循环导入。
    """
    text = str(error)
    if isinstance(error, AttributeError) and (
        text.startswith("'NoneType' object has no attribute")
        or text.startswith("java.lang.NullPointerException")
    ):
        return "null"
    return text


#: Controller 侧的默认单例（Java: ``@Autowired`` 注入同一个 bean）。
_GEN_TABLE_SERVICE: Optional[GenTableService] = None


def get_gen_table_service() -> GenTableService:
    """取共享的 service 实例（懒建，避免 import 期就连库）."""
    global _GEN_TABLE_SERVICE
    if _GEN_TABLE_SERVICE is None:
        _GEN_TABLE_SERVICE = GenTableService()
    return _GEN_TABLE_SERVICE


def reset_gen_table_service(service: Optional[GenTableService] = None) -> None:
    """测试钩子：替换 / 还原模块级单例."""
    global _GEN_TABLE_SERVICE
    _GEN_TABLE_SERVICE = service


__all__ = [
    "FILTER_COLUMN_NAME_LIST",
    "GenTableService",
    "get_gen_table_service",
    "reset_gen_table_service",
]
