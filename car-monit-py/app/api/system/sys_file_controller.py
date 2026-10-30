"""文件管理 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysFileController.java

**17** 个映射（全部迁移，本类没有 ``export``，所以不受 ``ExcelUtil`` 缺口影响）
-------------------------------------------------------------------------------
==================================  ==================================  =============================
Java                                Method / Path                       权限点
==================================  ==================================  =============================
``list``                            GET ``/list``                       ``base:sysflie:list``
``getInfoById``                     GET ``/getInfoById/{id}``           **无**
``getInfo``                         GET ``/{ids}``                      **无**
``upload``                          POST ``/upload``                    **无**
``uploadByUrl``                     POST ``/uploadByUrl``               **无**
``uploadSupplier``                  POST ``/uploadSupplier``            **无**
``uploadPdf``                       POST ``/uploadPdf``                 **无**
``file``                            GET ``/{bucket}/{fileName}``        **无**
``fileview``                        GET ``/view/{bucket}/{fileName}``   **无**
``removeById``                      DELETE ``/del/{id}``                **无**
``remove``                          DELETE ``/{ids}``                   ``base:supplier:remove``
``uploadFileId``                    POST ``/uploadFileId``              **无**
``uploadFileEnc``                   POST ``/uploadFileEnc``             **无**
``edit``                            PUT ``""``                          **无**
``getNewCa``                        GET ``/getNewCa``                   **无**
``updateCAFile``                    POST ``/updateCAFile``              **无**
``upload``（重载，微信小程序）      POST ``/uploadFile``                **无**
==================================  ==================================  =============================

``base:sysflie:list`` 的拼写**是错的**（``sysflie`` 而不是 ``sysfile``），但 ``sys_menu``
表里那条菜单的 ``perms`` 也是这么写的 —— 改成正确拼写会让文件列表**直接 403**。照抄。

``delete end -> "-111111"`` 这个魔数
-----------------------------------
``getInfo`` 收到的是逗号串（前端把多个 id 拼起来），先 ``removeEnd`` 掉结尾那个逗号；
如果删完变成空白，就换成 ``"-111111"``：

.. code-block:: java

    ids = CommonUtil.deleteEnd(ids);
    if (CommonUtil.isBlank(ids)) { ids = "-111111"; }

``-111111`` 不是合法主键，所以 ``in ('-111111')`` 必然查空 —— 目的是**避免**拼出
``in ()`` 这种语法错误。Python 侧照抄这个字面量。

``deleteEnd`` 只删**一个**结尾逗号：``"1,2,,"`` -> ``"1,2,"``（不是 ``"1,2"``）。

``uploadFileId`` 的 ``AjaxResult.error`` 被**丢弃**
-------------------------------------------------
.. code-block:: java

    if (CommonUtil.isNull(sysFile.getId()).equals("")) {
        AjaxResult.error("主键不能为空");      // 没有 return，也没有 throw
    }

那句 ``error(...)`` 的返回值没人接、也没返回给前端，所以 ``id`` 为空时**照样**往下走，
最终由 ``uploadFileId(null, file)`` 决定结果（``fileLogId`` 里 ``deleteSysFileByIdNew(null)``
会被自己的 ``catch`` 吞掉，然后插一条 ``id = NULL`` 的记录）。**不要补 ``return``**。

``uploadPdf`` 的 ``response`` 参数是死的
---------------------------------------
Java 里 ``out = response.getOutputStream();`` 的下一行就被
``out = new FileOutputStream(new File(filePath));`` 覆盖，所以 servlet 响应**一个字节都
没写过**。Python 侧把 ``None`` 传进去即可（service 也明确忽略它），返回体仍是 JSON。

两条 ``void`` 下载路由
----------------------
``{bucket}/{fileName}`` 与 ``view/{bucket}/{fileName}`` 都是 ``void`` + ``HttpServletResponse``：
Java 直接往响应流里写字节，成功时 ``Content-Type: application/octet-stream; charset=UTF-8``，
失败时 ``getFile`` 内部把异常吞掉 —— 客户端拿到的是 **HTTP 200 + 空 body**（不是 404）。

Python 用 :class:`ResponseSink` 攒字节再构造 :class:`~starlette.responses.Response`；
异常路径下 ``content_type`` 仍是 ``None``（等于 Java "没设过"），不发 ``Content-Type``。

``uploadFile``（微信小程序）只收图片
-----------------------------------
.. code-block:: java

    String original = CharsetUtil.convert(file.getOriginalFilename(), ISO_8859_1, UTF_8);
    String ext = FileUtil.extName(original);
    if (ext.indexOf("jpg") > -1 || ext.indexOf("jpeg") > -1
            || ext.indexOf("png") > -1 || ext.indexOf("gif") > -1) { } else { return error(...); }
    if (file.getSize() > 1024 * 1024 * 15) { return error("上传失败,你上传的附件大于15M！"); }

三个必须照抄的细节：

1. **没有** ``toLowerCase()`` —— ``.JPG`` 会被拒（``indexOf`` 区分大小写）；
2. 是 ``indexOf > -1`` 的**子串**匹配，不是等值；
3. 两条失败文案不同（图片格式 / 15M），逗号是**半角**。

``CharsetUtil.convert`` 把 multipart 解析器按 latin-1 读出来的中文名还原成 UTF-8。

``@Log(...)`` 注解
-----------------------
``upload`` / ``uploadByUrl`` / ``uploadSupplier`` / ``uploadPdf`` / ``uploadFileId`` /
``uploadFileEnc`` 带 ``@Log(title = "文件", businessType = INSERT)``；
``removeById`` / ``remove`` 是 ``DELETE``；``edit`` 是 ``@Log(title = "文件管理", UPDATE)``；
``updateCAFile`` 是 ``@Log(title = "文件", UPDATE)``。全部由
:mod:`app.framework.aspectj.log_aspect` 异步写 ``sys_oper_log``。
"""

from __future__ import annotations

from typing import Annotated, Any, List, Optional

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from starlette.responses import Response

from app.api.util.base64_decode_multipart_file import base64_convert
from app.api.util.common_util import delete_end, is_blank, is_null
from app.common.core.controller.base_controller import (
    bind_query_params,
    get_data_table,
    parse_id_array,
    start_page,
)
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.page.table_data_info import TableDataInfo
from app.common.enums.business_type import BusinessType
from app.common.utils import charset_util as CharsetUtil
from app.common.utils import file_util as FileUtil
from app.framework.aspectj.log_aspect import log
from app.framework.web.service.permission_service import pre_authorize_permi
from app.system.domain.ro.upload_ro import UploadRo
from app.system.domain.sys_file import SysFile
from app.system.service.sys_file_service import (
    ResponseSink,
    SysFileService,
    get_file_service,
)

router = APIRouter(prefix="/system/file", tags=["system-file"])

#: Java: ``com.ruoyi.web.controller.system.SysFileController`` —— 审计日志 ``method`` 列需要全类名
#: （``LogAspect`` 用 ``joinPoint.getTarget().getClass().getName()`` 取）。
JAVA_CONTROLLER = "com.ruoyi.web.controller.system.SysFileController"

#: 微信小程序上传的体积上限：``1024 * 1024 * 15``
WECHAT_MAX_FILE_SIZE = 1024 * 1024 * 15

#: 微信小程序上传允许的扩展名（**区分大小写**，见模块 docstring）
WECHAT_ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "gif")

#: ``getInfo`` 在 ids 为空白时替换成的魔数
EMPTY_IDS_PLACEHOLDER = "-111111"

NOT_PICTURE_MESSAGE = "上传失败,请上传照片格式的附件！"
FILE_TOO_LARGE_MESSAGE = "上传失败,你上传的附件大于15M！"
CA_NOT_FOUND_MESSAGE = "未找到CA驱动程序"


# --------------------------------------------------------------------------- 依赖
#
# Java: ``@Autowired private ISysFileService sysFileService``。Spring 默认单例，这里用
# 模块级缓存复刻；测试直接替换 ``controller._FILE_SERVICE``。

_FILE_SERVICE: Optional[SysFileService] = None


def _file_service() -> SysFileService:
    global _FILE_SERVICE
    if _FILE_SERVICE is None:
        _FILE_SERVICE = get_file_service()
    return _FILE_SERVICE


def reset_file_controller() -> None:
    """Test helper: drop the cached service so a fake can be injected."""
    global _FILE_SERVICE
    _FILE_SERVICE = None


def _bind_file_query(request: Request) -> SysFile:
    """Java: 形参 ``SysFile sysFile``（**没有** ``@RequestBody``）—— query string 绑定。"""
    return bind_query_params(SysFile, request.query_params)


#: ``list`` / ``getNewCa`` 的查询条件（``?fileName=...&bussType=...``）。
FileQueryParam = Annotated[SysFile, Depends(_bind_file_query)]


def _to_response(sink: ResponseSink) -> Response:
    """把 :class:`ResponseSink` 攒下来的字节变成不可变的响应。

    ``content_type`` 为 ``None`` 表示 Java 没调用过 ``setContentType``（异常路径），
    此时**不发** ``Content-Type`` 头。
    """
    if sink.content_type is None:
        return Response(content=sink.body)
    return Response(content=sink.body, headers={"Content-Type": sink.content_type})


# --------------------------------------------------------------------------- 查询


@router.get("/list", response_model=None)
@pre_authorize_permi("base:sysflie:list")
def list_files(query: FileQueryParam) -> TableDataInfo:
    """查询文件管理列表. Java: ``@GetMapping("/list") public TableDataInfo list(SysFile sysFile)``.

    权限点是 ``base:sysflie:list``（**音近拼错**），与 ``sys_menu.perms`` 一致。
    """
    start_page()
    rows = _file_service().select_sys_file_list(query)
    return get_data_table(rows)


@router.get("/getInfoById/{id}", response_model=None)
def get_info_by_id(id: int) -> AjaxResult:
    """获取文件详细信息. Java: ``@GetMapping(value = "/getInfoById/{id}")``.

    查不到时响应里**没有** ``data`` 键（``AjaxResult.success(null)`` 不 put ``data``）。
    """
    return AjaxResult.success_data(_file_service().select_sys_file_by_id(id))


@router.get("/getNewCa", response_model=None)
def get_new_ca(query: FileQueryParam) -> AjaxResult:
    """获取最新的CA驱动程序. Java: ``@GetMapping("/getNewCa") public AjaxResult getNewCa(SysFile sysFile)``.

    ``startPage()`` 之后只取分页结果的**第一条**（所以 ``pageSize`` 传 1 时才是"最新"）。
    列表非空回 ``success(list.get(0))``，否则 ``error("未找到CA驱动程序")``。
    """
    start_page()
    rows = _file_service().select_sys_file_list(query)
    if len(rows) > 0:
        return AjaxResult.success_data(rows[0])
    return AjaxResult.error_message(CA_NOT_FOUND_MESSAGE)


@router.get("/{ids}", response_model=None)
def get_info(ids: str) -> AjaxResult:
    """获取文件详细信息. Java: ``@GetMapping(value = "/{ids}") public AjaxResult getInfo(@PathVariable String ids)``.

    ``delete_end`` 只删**一个**结尾逗号；删完为空白就换成 ``"-111111"``，避免拼出
    ``in ()``。**没有** ``@PreAuthorize``。
    """
    ids = delete_end(ids)
    if is_blank(ids):
        ids = EMPTY_IDS_PLACEHOLDER
    return AjaxResult.success_data(_file_service().select_sys_file_by_ids(ids))


# --------------------------------------------------------------------------- 上传


@router.post("/upload", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="upload")
def upload(files: Annotated[List[UploadFile], File()]) -> AjaxResult:
    """上传文件. Java: ``@PostMapping("/upload") public AjaxResult upload(@RequestParam("files") MultipartFile[] files)``.

    **先登记再 putObject**，扩展名不在白名单时 ``fileLog`` 回 ``-1`` 并**跳过**上传，
    但结果数组里仍然有这一条（``id`` 为 ``"-1"``）。
    """
    return _file_service().upload_files(files)


@router.post("/uploadByUrl", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="uploadByUrl")
def upload_by_url(upload_ro: UploadRo) -> AjaxResult:
    """url上传文件. Java: ``@PostMapping("/uploadByUrl") public AjaxResult uploadByUrl(@RequestBody UploadRo uploadRo)``.

    只读 ``uploadRo.list``；单条失败只记日志并**跳过**（不中断整批、不回 error）。
    """
    return _file_service().upload_by_url(upload_ro.list)


@router.post("/uploadSupplier", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="uploadSupplier")
def upload_supplier(
    files: Annotated[List[UploadFile], File()],
    buss_names: Annotated[List[str], Form(alias="bussNames")],
) -> AjaxResult:
    """上传文件（带业务名）. Java: ``@PostMapping("/uploadSupplier")``.

    按**位置**把 ``bussNames[i]`` 配给 ``files[i]``，**没有长度校验** ——
    ``bussNames`` 更短时越界（Java ``ArrayIndexOutOfBoundsException`` / Python
    ``IndexError``），回 HTTP 200 + ``code 500``。
    """
    return _file_service().upload_supplier(files, buss_names)


@router.post("/uploadPdf", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="uploadPdf")
def upload_pdf(files: Annotated[List[UploadFile], File()]) -> AjaxResult:
    """上传文件（PDF）. Java: ``@PostMapping("/uploadPdf")``.

    pdf 直传 OSS；其它类型**只往本地临时目录写一个文件**（Word->PDF 转换整块被注释），
    结果里**没有** ``id`` 键。第二个 ``HttpServletResponse`` 参数从未被写过，故省略。
    """
    # Java: uploadFilesPdf(files, response) —— 那个 response 一次都没写，见模块 docstring
    return _file_service().upload_files_pdf(files, None)


@router.post("/uploadFileId", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="uploadFileId")
def upload_file_id(entity: SysFile) -> AjaxResult:
    """按指定主键上传文件. Java: ``@PostMapping("/uploadFileId") public AjaxResult uploadFileId(@RequestBody SysFile sysFile)``.

    ``if (CommonUtil.isNull(id).equals("")) { AjaxResult.error("主键不能为空"); }`` ——
    **返回值被丢弃**，代码继续往下走（见模块 docstring）。
    """
    # Java: if (CommonUtil.isNull(sysFile.getId()).equals("")) { AjaxResult.error(...); }
    if is_null(entity.id) == "":
        pass  # 结果被丢弃，既不 return 也不 throw

    temp_file = base64_convert(entity.files)
    return _file_service().upload_file_id(entity.id, temp_file)


@router.post("/uploadFileEnc", response_model=None)
@log(title="文件", business_type=BusinessType.INSERT, java_method="uploadFileEnc")
def upload_file_enc(files: Annotated[List[UploadFile], File()]) -> AjaxResult:
    """上传文件（加密）. Java: ``@PostMapping("/uploadFileEnc")``.

    服务端方法体**整块被注释**，永远回 ``success([])`` —— CA 加密未启用。
    """
    return _file_service().upload_files_enc(files)


@router.post("/updateCAFile", response_model=None)
@log(title="文件", business_type=BusinessType.UPDATE, java_method="updateCAFile")
def update_ca_file(entity: SysFile) -> AjaxResult:
    """更新CA驱动程序. Java: ``@PostMapping("/updateCAFile") public AjaxResult updateCAFile(@RequestBody SysFile sysFile)``.

    先物理删除 ``id = 3001`` 的旧记录（连同 OSS 对象），再把本条主键改成 3001；
    返回的是**改之前**的那个 ``id``。
    """
    return _file_service().update_ca_file(entity)


@router.post("/uploadFile", response_model=None)
def upload_wechat(file: Annotated[UploadFile, File()]) -> AjaxResult:
    """微信小程序文件上传. Java: ``@PostMapping("/uploadFile") public AjaxResult upload(HttpServletRequest request)``.

    Java 走的是 ``((MultipartHttpServletRequest) request).getFile("file")``，等价于
    表单里的**单个** ``file`` 字段。只收图片（``jpg`` / ``jpeg`` / ``png`` / ``gif``，
    区分大小写），且不能超过 15M；两条失败文案不同。
    """
    files = [file]
    for current in files:
        # Java: CharsetUtil.convert(originalFilename, ISO_8859_1, UTF_8)
        original = CharsetUtil.convert(
            current.filename, CharsetUtil.ISO_8859_1, CharsetUtil.UTF_8
        )
        ext = FileUtil.ext_name(original)
        if ext is not None and ext != "":
            # Java: ext.indexOf("jpg") > -1 || ... —— 子串匹配，且**没有** toLowerCase
            if any(item in ext for item in WECHAT_ALLOWED_EXTENSIONS):
                pass
            else:
                return AjaxResult.error_message(NOT_PICTURE_MESSAGE)
        else:
            return AjaxResult.error_message(NOT_PICTURE_MESSAGE)

        file_size = _size_of(current)
        if file_size > WECHAT_MAX_FILE_SIZE:
            return AjaxResult.error_message(FILE_TOO_LARGE_MESSAGE)
    return _file_service().upload_files(files)


# --------------------------------------------------------------------------- 下载


@router.get("/{bucket}/{file_name}", response_model=None)
def file(bucket: str, file_name: str) -> Response:
    """下载文件. Java: ``@GetMapping(value = "/{bucket}/{fileName}") public void file(...)``.

    异常被 ``getFile`` 吞掉 -> **HTTP 200 + 空 body**（不是 404）。
    """
    sink = ResponseSink()
    _file_service().get_file(bucket, file_name, sink)
    return _to_response(sink)


@router.get("/view/{bucket}/{file_name}", response_model=None)
def file_view(bucket: str, file_name: str) -> Response:
    """预览文件. Java: ``@GetMapping(value = "/view/{bucket}/{fileName}") public void fileview(...)``.

    与 :func:`file` 完全同一实现（两套 URL 只是前端习惯不同）。
    """
    sink = ResponseSink()
    _file_service().get_file(bucket, file_name, sink)
    return _to_response(sink)


# --------------------------------------------------------------------------- 增删改


@router.put("", response_model=None)
@log(title="文件管理", business_type=BusinessType.UPDATE, java_method="edit")
def edit(entity: SysFile) -> AjaxResult:
    """修改文件管理. Java: ``@PutMapping public AjaxResult edit(@RequestBody SysFile sysFile)``.

    有 ``id`` 就改、没有就新增（新增时补雪花 id）。成功文案 ``"操作成功！"``（全角叹号），
    ``data`` 是 ``id``。
    """
    return _file_service().save_sys_file(entity)


@router.delete("/del/{id}", response_model=None)
@log(title="文件", business_type=BusinessType.DELETE, java_method="removeById")
def remove_by_id(id: int) -> AjaxResult:
    """删除单个文件. Java: ``@DeleteMapping("/del/{id}") public AjaxResult removeById(@PathVariable Long id)``.

    先删 OSS 对象再**软删除**；异常回 ``error(ex.getMessage())``（``msg`` 可能是 ``null``）。
    """
    return _file_service().delete_sys_file_by_id(id)


@router.delete("/{ids}", response_model=None)
@pre_authorize_permi("base:supplier:remove")
@log(title="文件", business_type=BusinessType.DELETE, java_method="remove")
def remove(ids: str) -> AjaxResult:
    """删除多个文件. Java: ``@DeleteMapping("/{ids}") public AjaxResult remove(@PathVariable Long[] ids)``.

    权限点写的是 ``base:supplier:remove``（供应商模块的），**不是** ``volume:file:remove``。
    ``count == 0`` 也回 200。
    """
    return _file_service().delete_sys_file_by_ids(parse_id_array(ids))


def _size_of(file: Any) -> int:
    """Java: ``MultipartFile#getSize()`` —— 复用 ``FileUploadUtils`` 的同一实现。"""
    from app.common.utils.file_upload_utils import size_of

    return size_of(file)


__all__ = [
    "router",
    "FileQueryParam",
    "WECHAT_MAX_FILE_SIZE",
    "WECHAT_ALLOWED_EXTENSIONS",
    "EMPTY_IDS_PLACEHOLDER",
    "NOT_PICTURE_MESSAGE",
    "FILE_TOO_LARGE_MESSAGE",
    "CA_NOT_FOUND_MESSAGE",
    "list_files",
    "get_info_by_id",
    "get_new_ca",
    "get_info",
    "upload",
    "upload_by_url",
    "upload_supplier",
    "upload_pdf",
    "upload_file_id",
    "upload_file_enc",
    "update_ca_file",
    "upload_wechat",
    "file",
    "file_view",
    "edit",
    "remove_by_id",
    "remove",
    "reset_file_controller",
]
