"""代码生成 操作处理 / code-generator controller.

# Migrated from: ruoyi-generator/src/main/java/com/ruoyi/generator/controller/GenController.java

15 个映射，全部迁移
-------------------
==============================  ==============================  ==============================
Java                            Method / Path                   权限点
==============================  ==============================  ==============================
``genList``                     GET ``/list``                   ``tool:gen:list``
``getAllGenerateTableList``     GET ``/all/list``               **无**（登录即可）
``getInfo``                     GET ``/{talbleId}``             ``tool:gen:query``
``dataList``                    GET ``/db/list``                ``tool:gen:list``
``columnList``                  GET ``/column/{talbleId}``      ``tool:gen:list``
``getColumnList``               POST ``/getColumnList``         **无**
``getAllColumnList``            POST ``/getAllColumnList``      **无**
``importTableSave``             POST ``/importTable``           ``tool:gen:list``
``editSave``                    PUT ``""``                      ``tool:gen:edit``
``remove``                      DELETE ``/{tableIds}``          ``tool:gen:remove``
``preview``                     GET ``/preview/{tableId}``      ``tool:gen:preview``
``download``                    GET ``/download/{tableName}``   ``tool:gen:code``
``genCode``                     GET ``/genCode/{tableName}``    ``tool:gen:code``
``synchDb``                     GET ``/synchDb/{tableName}``    ``tool:gen:edit``
``batchGenCode``                GET ``/batchGenCode``           ``tool:gen:code``
==============================  ==============================  ==============================

三条**没有** ``@PreAuthorize`` 的映射
-------------------------------------
``getAllGenerateTableList`` / ``getColumnList`` / ``getAllColumnList`` 源码上就没有注解，
``SecurityConfig`` 里也没有一条规则命中 ``/tool/**``，于是它们落到
``anyRequest().authenticated()`` —— **登录即可**。前端"生成配置"页在保存前要读全量表名，
权限点补上去会让只有查看权限的账号白屏，别"顺手"补。

``columnList`` 的路径变量是**死的**
-----------------------------------
Java 签名是 ``columnList(Long tableId)``，而 ``@GetMapping`` 上写的是
``/column/{talbleId}``（拼写错误），**参数上也没有** ``@PathVariable`` —— 于是：

* 路径里那一段完全不参与绑定（也不做 ``Long`` 转换，任意字符串都能进）；
* 真正的 ``tableId`` 从 **query string** 取，命名是 ``tableId``。

所以 ``GET /tool/gen/column/anything?tableId=3`` 与 ``.../column/0?tableId=3`` 等价。
Python 侧把路径变量收成 ``str`` 并丢弃，query 参数单独声明成 ``table_id``。

``columnList`` 手工拼 ``TableDataInfo``，所以 ``code`` 是 ``0``
-------------------------------------------------------------
Java 没有走 ``getDataTable(list)``，而是 ``new TableDataInfo()`` 之后只 ``setRows`` /
``setTotal`` —— ``code`` 保持基本类型默认值 ``0``，``msg`` 保持 ``null``。响应长这样::

    {"total": 12, "rows": [...], "code": 0, "msg": null}

同模块的 ``/list`` / ``/db/list`` / ``/getColumnList`` 走的是 ``getDataTable``，
``code`` 是 ``200``、``msg`` 是 ``"查询成功"``。**两种信封在同一个控制器里共存**，照抄。

``importTable`` / ``batchGenCode`` 的 ``tables`` 缺失 -> ``{"msg":null,"code":500}``
----------------------------------------------------------------------------------
形参 ``String tables`` **没有** ``@RequestBody``，Spring 从 ``getParameter`` 取值；
不带这个参数时是 ``null``，随后 ``Convert.toStrArray(null)`` 直接 NPE。
``NullPointerException.getMessage()`` 是 ``null``，于是 ``GlobalExceptionHandler`` 回
HTTP 200 + ``{"msg":null,"code":500}``。Python 侧由
:func:`app.common.core.text.convert.to_str_array` 抛带
``java.lang.NullPointerException`` 哨兵的 ``AttributeError`` 复刻同一个信封。

绑定范围差一处（已记入 ``COMPATIBILITY.md``）
--------------------------------------------
Java 的 ``getParameter`` 同时覆盖 query string 与
``application/x-www-form-urlencoded`` 表单体；这里只从 **query string** 取 ``tables``
（前端 ``gen/index.vue`` 这两条请求都用 ``params``，即 query）。要读表单体必须把端点写成
``async def``，而那会让 ``@Log`` 切面失去同步语义，收益不抵风险。

``getInfo`` 的 ``data`` 键序是 ``HashMap`` 桶序，不是书写序
----------------------------------------------------------
Java 用 ``Map<String, Object> map = new HashMap<>(); map.put("info", ...);
map.put("rows", ...); map.put("tables", ...);``。Jackson 按 ``HashMap`` 的**迭代序**
输出，默认容量 16 时三个键的桶位是 ``tables``=2、``rows``=12、``info``=15，于是真实响应是::

    {"msg":"操作成功","code":200,"data":{"tables":[...],"rows":[...],"info":{...}}}

``tables`` 在最前面看着别扭，但这就是 Java 逐字节交付给前端的顺序，照抄
（桶位推导见 ``scripts/audit_*`` 同目录的历史脚本，已用独立脚本核对过）。

生成 zip 的响应头
-----------------
``genCode(response, data)`` 是私有方法，两个下载端点共用：``reset()`` 之后依次
``Access-Control-Allow-Origin: *``、``Access-Control-Expose-Headers: Content-Disposition``、
``Content-Disposition: attachment; filename="ruoyi.zip"``、``Content-Length``、
``Content-Type: application/octet-stream; charset=UTF-8``。文件名是**写死**的
``ruoyi.zip``（即使批量打包多张表也一样），不是 ``表名.zip``。

``PUT /tool/gen`` 的校验排在权限点之前
-------------------------------------
``@Validated @RequestBody GenTable`` 由 Spring MVC 在进入方法代理（``@PreAuthorize``）
**之前**完成，所以"字段为空 + 没有权限"的请求回的是校验文案而不是 403。Python 侧用
``Depends`` 表达同一顺序（见 :data:`ValidGenTable`）。
``GenTable.columns`` 上有 ``@Valid``，因此**级联**校验每一列的 ``javaField``。
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import Response

from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.core.text.convert import to_str_array
from app.common.enums.business_type import BusinessType
from app.common.utils.bean_validation import validate
from app.common.utils.string_utils import is_not_empty, join
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.generator.domain.gen_table import GEN_TABLE_CONSTRAINTS, GenTable
from app.generator.domain.gen_table_column import (
    GEN_TABLE_COLUMN_CONSTRAINTS,
    GenTableColumn,
)
from app.generator.service.gen_table_column_service import (
    GenTableColumnService,
    get_gen_table_column_service,
)
from app.generator.service.gen_table_service import GenTableService, get_gen_table_service

router = APIRouter(prefix="/tool/gen", tags=["tool-gen"])

#: Java: ``com.ruoyi.generator.controller.GenController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.generator.controller.GenController"

#: Java: ``Constants.CHAR_COMMA``
CHAR_COMMA = ","

#: Java: ``genCode(response, data)`` 里的两个固定响应头.
ZIP_CONTENT_TYPE = "application/octet-stream; charset=UTF-8"
ZIP_CONTENT_DISPOSITION = 'attachment; filename="ruoyi.zip"'


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private IGenTableService genTableService`` /
# ``@Autowired private IGenTableColumnService genTableColumnService``。
# Spring 默认单例，这里用模块级缓存复刻；测试直接替换 ``_TABLE_SERVICE`` / ``_COLUMN_SERVICE``。

_TABLE_SERVICE: GenTableService | None = None
_COLUMN_SERVICE: GenTableColumnService | None = None


def _table_service() -> GenTableService:
    global _TABLE_SERVICE
    if _TABLE_SERVICE is None:
        _TABLE_SERVICE = get_gen_table_service()
    return _TABLE_SERVICE


def _column_service() -> GenTableColumnService:
    global _COLUMN_SERVICE
    if _COLUMN_SERVICE is None:
        _COLUMN_SERVICE = get_gen_table_column_service()
    return _COLUMN_SERVICE


def reset_gen_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _TABLE_SERVICE, _COLUMN_SERVICE
    _TABLE_SERVICE = None
    _COLUMN_SERVICE = None


def _query_gen_table(request: Request) -> GenTable:
    """Java: 形参 ``GenTable genTable``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(GenTable, request.query_params)


#: 查询条件实体（``?tableName=...&tableComment=...``）。
GenTableParam = Annotated[GenTable, Depends(_query_gen_table)]


def _validated_gen_table(gen_table: GenTable) -> GenTable:
    """Java: ``@Validated @RequestBody GenTable``.

    做成 ``Depends`` 而不是函数体第一行，是为了让校验排在 ``@PreAuthorize`` **之前**。
    ``columns`` 上的 ``@Valid`` 意味着级联校验 —— 先父后子（Hibernate 的级联与自身约束
    之间的先后没有对外可观测的差异：任意一条违规都是 ``AjaxResult.error(该条文案)``）。
    """
    validate(gen_table, GEN_TABLE_CONSTRAINTS)
    for column in gen_table.columns or []:
        validate(column, GEN_TABLE_COLUMN_CONSTRAINTS)
    return gen_table


#: 已校验的请求体。
ValidGenTable = Annotated[GenTable, Depends(_validated_gen_table)]


def _gen_code_response(data: bytes) -> Response:
    """Java: ``private void genCode(HttpServletResponse response, byte[] data)``.

    ``response.reset()`` 之后再逐条设头。Starlette 只在响应头里缺 ``content-length``
    时才补，所以显式带上 ``Content-Length`` 不会产生重复头。
    """
    return Response(
        content=data,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Content-Disposition": ZIP_CONTENT_DISPOSITION,
            "Content-Length": str(len(data)),
            "Content-Type": ZIP_CONTENT_TYPE,
        },
    )


# --------------------------------------------------------------------------- 查询
#
# 注册顺序不是装饰性的：``/{talble_id}`` 会吃掉所有单段 GET，所以它排在**最后**。
# Spring 的 ``AntPathMatcher`` 天生让字面量优先，FastAPI 只看注册顺序。


@router.get("/list", response_model=None)
@pre_authorize_permi("tool:gen:list")
def gen_list(gen_table: GenTableParam) -> TableDataInfo:
    """查询代码生成列表. Java: ``@GetMapping("/list") public TableDataInfo genList(GenTable genTable)``."""
    start_page()
    rows = _table_service().select_gen_table_list(gen_table)
    return get_data_table(rows)


@router.get("/all/list", response_model=None)
def get_all_generate_table_list(gen_table: GenTableParam) -> AjaxResult:
    """获取列表. Java: ``@GetMapping("/all/list") public AjaxResult getAllGenerateTableList(...)``.

    **没有** ``@PreAuthorize``（登录即可），也**没有** ``startPage()`` —— 返回全量。
    """
    return AjaxResult.success_data(_table_service().select_gen_table_list(gen_table))


@router.get("/db/list", response_model=None)
@pre_authorize_permi("tool:gen:list")
def data_list(gen_table: GenTableParam) -> TableDataInfo:
    """查询数据库列表. Java: ``@GetMapping("/db/list") public TableDataInfo dataList(GenTable genTable)``.

    查的是 ``information_schema.tables``，**排除** ``gen_table`` / ``gen_table_column``
    以及已导入的表（见 :mod:`app.generator.mapper.gen_table_mapper`）。
    """
    start_page()
    rows = _table_service().select_db_table_list(gen_table)
    return get_data_table(rows)


@router.get("/column/{talble_id}", response_model=None)
@pre_authorize_permi("tool:gen:list")
def column_list(
    talble_id: str, table_id: Optional[int] = Query(default=None, alias="tableId")
) -> TableDataInfo:
    """查询数据表字段列表. Java: ``@GetMapping("/column/{talbleId}") public TableDataInfo columnList(Long tableId)``.

    路径变量 ``talbleId``（原文拼写）在 Java 里**没有** ``@PathVariable``，所以既不做类型
    转换也不参与绑定；真正的入参是 query 上的 ``tableId``。这里原样照抄：
    ``talble_id`` 只用于让路由匹配，取值丢弃。

    手工构造 ``TableDataInfo`` -> ``code = 0``、``msg = null``（见模块 docstring）。
    """
    _ = talble_id  # Java: 路径变量未绑定，取值无意义
    rows = _column_service().select_gen_table_column_list_by_table_id(table_id)
    return TableDataInfo(rows=rows, total=len(rows))


@router.post("/getColumnList", response_model=None)
def get_column_list(gen_table_column: GenTableColumn) -> TableDataInfo:
    """分页-获取字段列表信息. Java: ``@PostMapping("/getColumnList")``.

    **没有** ``@PreAuthorize``（登录即可）。走 ``getDataTable`` -> ``code 200``。
    """
    start_page()
    rows = _column_service().select_gen_table_column_list(gen_table_column)
    return get_data_table(rows)


@router.post("/getAllColumnList", response_model=None)
def get_all_column_list(gen_table_column: GenTableColumn) -> AjaxResult:
    """获取字段列表信息. Java: ``@PostMapping("/getAllColumnList")``.

    **没有** ``@PreAuthorize``（登录即可），也**没有** ``startPage()`` —— 返回全量。
    """
    return AjaxResult.success_data(
        _column_service().select_gen_table_column_list(gen_table_column)
    )


# --------------------------------------------------------------------------- 增删改


@router.post("/importTable", response_model=None)
@pre_authorize_permi("tool:gen:list")
@log(title="代码生成", business_type=BusinessType.IMPORT, java_method="importTableSave")
def import_table_save(tables: Optional[str] = None) -> AjaxResult:
    """导入表结构（保存）. Java: ``@PostMapping("/importTable") public AjaxResult importTableSave(String tables)``.

    ``tables`` 是逗号拼接的表名。缺参数时 ``to_str_array(None)`` 抛 NPE 哨兵 ->
    HTTP 200 + ``{"msg":null,"code":500}``（见模块 docstring）。
    """
    table_names = to_str_array(tables)
    table_list = _table_service().select_db_table_list_by_names(table_names)
    _table_service().import_gen_table(table_list)
    return AjaxResult.success()


@router.put("", response_model=None)
@pre_authorize_permi("tool:gen:edit")
@log(title="代码生成", business_type=BusinessType.UPDATE, java_method="editSave")
def edit_save(gen_table: ValidGenTable) -> AjaxResult:
    """修改保存代码生成业务. Java: ``@PutMapping public AjaxResult editSave(@Validated @RequestBody GenTable genTable)``.

    ``validateEdit`` 只校验树表（主子表那两条嵌在树表分支里，永远不成立）；
    之后 ``updateGenTable`` 把 ``params`` 序列化进 ``options`` 并逐列更新。
    """
    _table_service().validate_edit(gen_table)
    _table_service().update_gen_table(gen_table)
    return AjaxResult.success()


@router.delete("/{table_ids}", response_model=None)
@pre_authorize_permi("tool:gen:remove")
@log(title="代码生成", business_type=BusinessType.DELETE, java_method="remove")
def remove(table_ids: str) -> AjaxResult:
    """删除代码生成. Java: ``@DeleteMapping("/{tableIds}") public AjaxResult remove(@PathVariable Long[] tableIds)``.

    先删 ``gen_table`` 再按 **table_id** 删 ``gen_table_column``（
    ``deleteGenTableColumnByIds`` 的名字有误导性，它删的是 table_id）。
    """
    _table_service().delete_gen_table_by_ids(parse_id_array(table_ids))
    return AjaxResult.success()


# --------------------------------------------------------------------------- 预览 / 生成


@router.get("/preview/{table_id}", response_model=None)
@pre_authorize_permi("tool:gen:preview")
def preview(table_id: int) -> AjaxResult:
    """预览代码. Java: ``@GetMapping("/preview/{tableId}") public AjaxResult preview(...)``.

    ``data`` 是 ``Map<模板路径, 渲染后的源码>``，键形如
    ``vmplus/java/domain.java.vm``（``generator-code.mybatis-plus.enable`` 为 ``true``）。
    键序 = ``VelocityUtils.getTemplateList`` 的顺序，前端按这个顺序渲染标签页。
    """
    return AjaxResult.success_data(_table_service().preview_code(table_id))


@router.get("/download/{table_name}", response_model=None)
@pre_authorize_permi("tool:gen:code")
@log(title="代码生成", business_type=BusinessType.GENCODE, java_method="download")
def download(table_name: str) -> Response:
    """生成代码（下载方式）. Java: ``@GetMapping("/download/{tableName}") public void download(...)``.

    返回 zip 字节流；文件名写死 ``ruoyi.zip``。
    """
    data = _table_service().download_code(table_name)
    return _gen_code_response(data)


@router.get("/genCode/{table_name}", response_model=None)
@pre_authorize_permi("tool:gen:code")
@log(title="代码生成", business_type=BusinessType.GENCODE, java_method="genCode")
def gen_code(table_name: str) -> AjaxResult:
    """生成代码（自定义路径）. Java: ``@GetMapping("/genCode/{tableName}")``.

    直接往 ``genPath`` 写文件，**跳过** ``sql.vm`` / ``api.js.vm`` /
    ``index.vue.vm`` / ``index-tree.vue.vm`` 四类模板。
    """
    _table_service().generator_code(table_name)
    return AjaxResult.success()


@router.get("/synchDb/{table_name}", response_model=None)
@pre_authorize_permi("tool:gen:edit")
@log(title="代码生成", business_type=BusinessType.UPDATE, java_method="synchDb")
def synch_db(table_name: str) -> AjaxResult:
    """同步数据库. Java: ``@GetMapping("/synchDb/{tableName}")``.

    补新列、删已消失的列（物理列比对 ``information_schema.columns``）。
    """
    _table_service().synch_db(table_name)
    return AjaxResult.success()


@router.get("/batchGenCode", response_model=None)
@pre_authorize_permi("tool:gen:code")
@log(title="代码生成", business_type=BusinessType.GENCODE, java_method="batchGenCode")
def batch_gen_code(tables: Optional[str] = None) -> Response:
    """批量生成代码. Java: ``@GetMapping("/batchGenCode") public void batchGenCode(..., String tables)``.

    缺 ``tables`` 时同样 NPE -> ``{"msg":null,"code":500}``（此时不会有 zip 响应头）。
    """
    table_names = to_str_array(tables)
    data = _table_service().download_code(table_names)
    return _gen_code_response(data)


# --------------------------------------------------------------------------- 详情
#
# ``/{talbleId}`` 必须留在**最后**：上面的 ``/list`` ``/all/list`` ``/db/list``
# ``/batchGenCode`` 都是单段字面量路由，先注册的赢。


@router.get("/{talble_id}", response_model=None)
@pre_authorize_permi("tool:gen:query")
def get_info(talble_id: int) -> AjaxResult:
    """修改代码生成业务（详情）. Java: ``@GetMapping(value = "/{talbleId}") public AjaxResult getInfo(@PathVariable Long talbleId)``.

    ``data`` 是 ``HashMap``，键序按桶位输出为 ``tables`` / ``rows`` / ``info``
    （见模块 docstring）。``rows`` 里每一列的 ``dialogSearchColumnNames`` /
    ``dialogListColumnNames`` 由 id 串回查列名后逗号拼接，回查为空时**保持原值**。
    """
    table = _table_service().select_gen_table_by_id(talble_id)
    tables = _table_service().select_gen_table_all()
    columns = _column_service().select_gen_table_column_list_by_table_id(talble_id)

    for data in columns:
        # 查询条件
        if is_not_empty(data.dialog_search_column_ids):
            found = _column_service().select_gen_table_column_list_by_table_column_ids(
                data.dialog_search_column_ids
            )
            if is_not_empty(found):
                names: List[Any] = [item.column_name for item in found or []]
                data.dialog_search_column_names = join(names, CHAR_COMMA)

        # 列表字段
        if is_not_empty(data.dialog_list_column_ids):
            found = _column_service().select_gen_table_column_list_by_table_column_ids(
                data.dialog_list_column_ids
            )
            if is_not_empty(found):
                names = [item.column_name for item in found or []]
                data.dialog_list_column_names = join(names, CHAR_COMMA)

    # Java: HashMap 的迭代序 —— tables(2) -> rows(12) -> info(15)
    result: Dict[str, Any] = {"tables": tables, "rows": columns, "info": table}
    return AjaxResult.success_data(result)


__all__ = [
    "router",
    "CHAR_COMMA",
    "JAVA_CONTROLLER",
    "ZIP_CONTENT_DISPOSITION",
    "ZIP_CONTENT_TYPE",
    "GenTableParam",
    "ValidGenTable",
    "batch_gen_code",
    "column_list",
    "data_list",
    "download",
    "edit_save",
    "gen_code",
    "gen_list",
    "get_all_column_list",
    "get_all_generate_table_list",
    "get_column_list",
    "get_info",
    "import_table_save",
    "preview",
    "remove",
    "reset_gen_controller",
    "synch_db",
]
