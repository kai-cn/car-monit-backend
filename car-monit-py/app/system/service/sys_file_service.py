"""文件管理 服务层实现（OSS / S3 版）.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/ISysFileService.java
# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/impl/SysFileServiceImpl.java

这是本项目**依赖最重**的一个 service：它同时用到 OSS 客户端、雪花 id、Forest 下载客户端，
以及 4 个私有"登记"方法（``fileLog`` / ``fileSupplierLog`` / ``fileLogId`` / ``fileLogUser``）。

方法对照表（``ISysFileService`` 24 个成员，全部迁移）
----------------------------------------------------
=============================================  ==============================================
Java                                            Python
=============================================  ==============================================
``selectSysFileByIds(String)``                  :meth:`select_sys_file_by_ids`
``selectSysFileById(Long)``                     :meth:`select_sys_file_by_id`
``selectSysFileList(SysFile)``                  :meth:`select_sys_file_list`
``saveSysFile(SysFile)``                        :meth:`save_sys_file`
``deleteSysFileByIds(Long[])``                  :meth:`delete_sys_file_by_ids`
``deleteSysFileById(Long)``                     :meth:`delete_sys_file_by_id`
``uploadFile(MultipartFile)``                   :meth:`upload_file`
``uploadFiles(MultipartFile[])``                :meth:`upload_files`
``uploadByUrl(List<UploadByUrlRo>)``            :meth:`upload_by_url`
``uploadFilesUser(MultipartFile[], String)``    :meth:`upload_files_user`
``uploadSupplier(MultipartFile[], String[])``   :meth:`upload_supplier`
``uploadFilesPdf(MultipartFile[], Response)``   :meth:`upload_files_pdf`
``uploadFileId(Long, MultipartFile)``           :meth:`upload_file_id`
``uploadFilesEnc(MultipartFile[])``             :meth:`upload_files_enc`
``getFile(String, String, Response)``           :meth:`get_file`
``getFile(String, String, OutputStream)``       :meth:`get_file_to_output_stream`
``getFileToUrl(String, String, String)``        :meth:`get_file_to_url`
``updateCAFile(SysFile)``                       :meth:`update_ca_file`
``getFileUrl(Long)``                            :meth:`get_file_url`
``uploadBase64Picture(String, SysFile)``        :meth:`upload_base64_picture`
``uploadBase64Picture(String)``                 :meth:`upload_base64_picture_rich_text`
``uploadFile(InputStream, SysFile)``            :meth:`upload_file_from_stream`
``getFileObject(Long)``                         :meth:`get_file_object`
``getByteObject(Long)``                         :meth:`get_byte_object`
=============================================  ==============================================

三个同名重载（``getFile`` / ``uploadFile`` / ``uploadBase64Picture``）按 Java 的"最常用者
占原名"惯例拆名，与 :mod:`app.common.utils.file_upload_utils` 的处理一致。

``AjaxResult.success(String)`` 与 ``success(Object)`` 的重载陷阱
----------------------------------------------------------------
Java 里 ``AjaxResult.success(fileId)`` 的 ``fileId`` 是 ``String``，重载解析会挑
``success(String msg)`` —— **不是** ``success(Object data)``。于是"上传 base64 图片"返回的是::

    {"code": 200, "msg": "<文件id>"}      # 没有 data 键

Python 侧照抄成 :meth:`AjaxResult.success_message`。别"修正"成 ``success_data`` —— 富文本
那半边读的就是 ``MSG_TAG``（虽然它被注释掉了）。

``count == 0`` 也返回成功
-------------------------
两个删除方法都用 ``AjaxResult.success(count)``（不是 ``toAjax``），与
``SysUpgradeInfoServiceImpl`` 一致。失败时 ``catch (Exception ex)`` 回
``error(ex.getMessage())`` —— 注意 ``msg`` 可能是 ``null``（比如 NPE 的 message）。

被注释 / 已废弃的成员（照留，见迁移原则第 4 条）
----------------------------------------------
* :meth:`upload_files_enc` —— 方法体**整块被注释**，只剩一个空循环，永远返回
  ``success([])``；
* :meth:`get_file_url` —— 方法体被注释，永远返回 ``None``；
* :meth:`upload_base64_picture_rich_text` —— 方法体被注释，非空入参返回 ``""``；
* :meth:`upload_file_from_stream` —— 方法体被注释，只返回一个**新生成的**雪花 id
  （既不写库也不上传，是"看起来成功"的假实现）；
* ``convert(String, Charset, Charset)`` —— 私有静态工具，调用点全在注释里。
* :meth:`upload_files_pdf` 里 Word->PDF 的转换与"转完再上传"整块被注释，所以非 pdf 分支
  只是**往本地临时目录写一个文件**，然后返回一个没有 ``id`` 的结果。

``fileLog`` 的 4 个变体差异（逐字照抄，别合并）
--------------------------------------------
=============================  =========  ==========  ===========  ============
方法                           写 bussName  写审计列    走 saveSysFile  支持的扩展名
=============================  =========  ==========  ===========  ============
``fileLog``                    否          是          是            17 个
``fileSupplierLog``            是          是          是            17 个
``fileLogId``                  否          是(直插)    否(先删后插)   17 个 + 1 个死条目
``fileLogUser``                否          是(直插)    否            17 个
=============================  =========  ==========  ===========  ============

四个变体里都有**重复的** ``setCreateUser(...)``（Java 的复制粘贴残留），行为无差别，照抄。
``fileLogId`` 的白名单里多了一条 ``".ppt"``（**带点**），而 ``ext`` 已经 ``toLowerCase()``
且不含点，所以这一条**永远匹配不上** —— 属于既有死代码。

``fileLogUser`` 不写 ``delFlag``
--------------------------------
它直接 ``sysFileMapper.insertSysFile``，绕过了 ``saveSysFile``，所以 ``del_flag`` 是
**NULL**。``selectSysFileList`` 过滤 ``del_flag = '0'``，于是这些记录在列表里**查不到**
（按 id 仍能查到）。`uploadFilesUser` 目前没有控制器调用，但行为照抄。
"""

from __future__ import annotations

import logging
import os
from io import BytesIO
from typing import Any, BinaryIO, Dict, List, Optional, Sequence

from app.common.core.domain.ajax_result import AjaxResult
from app.common.utils import base64_utils
from app.common.utils import file_util as FileUtil
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.date_utils import get_timestamp
from app.common.utils.file_upload_utils import size_of
from app.common.utils.multipart_file_util import MockMultipartFile, convert_byte_to_multipart_file
from app.common.utils.oss_template import OssTemplate, S3Object
from app.common.utils.snowflake_id_worker import get_id_worker
from app.common.utils.string_utils import get_uuid, is_blank
from app.common.utils.uuid_utils import simple_uuid
from app.settings import get_settings
from app.system.domain.ro.upload_by_url_ro import UploadByUrlRo
from app.system.domain.sys_file import SysFile
from app.system.mapper.sys_file_mapper import SysFileMapper
from app.system.service.forest.file_api import FileApi, get_file_api
from app.config.database import transactional

logger = logging.getLogger("app.system.service.sys_file_service")

#: Java: ``FileUtil.extName`` 白名单（``fileLog`` / ``fileSupplierLog`` / ``fileLogUser``）。
_SUPPORTED_EXTENSIONS: tuple = (
    "doc", "docx", "pdf", "xls", "xlsx", "pptx", "txt", "zip", "rar",
    "jpg", "jpeg", "png", "gif", "mp3", "mp4", "flv", "3gp",
)

#: ``fileLogId`` 的白名单：与上面同集合，但写了 ``".ppt"``（带点，**永远不匹配**）。
_SUPPORTED_EXTENSIONS_FOR_ID: tuple = (
    "doc", "docx", "pdf", "xls", "txt", "xlsx", ".ppt", "pptx", "zip", "rar",
    "jpg", "jpeg", "png", "gif", "mp3", "mp4", "flv", "3gp",
)

#: Java: ``@RequestParam("files")`` 的结果里，``url`` 的模板。
#: ``String.format("/system/file/%s/%s", bucketName, fileName)``
FILE_URL_TEMPLATE = "/system/file/{}/{}"


class _CloseTolerantStream:
    """包住 :class:`BytesIO`，让 ``close()`` 变成无操作.

    Java 里 ``FileUtils.writeBytes`` 在 ``finally`` 里 ``IOUtils.close(os)`` ——
    关掉 servlet 输出流就等于**提交响应**，之后再写也没用了。FastAPI 的响应对象要等
    控制器 ``return`` 之后才由框架构造，所以缓冲区必须在"已关流"之后仍然可读。

    对外行为无差别：字节只在关流前写进去，关流后不再接受写入（``write`` 直接抛
    ``ValueError``，与真实流一致）。
    """

    def __init__(self, buffer: BytesIO) -> None:
        self._buffer = buffer
        self._closed = False

    def write(self, data: bytes) -> int:
        if self._closed:
            raise ValueError("I/O operation on closed file")
        return self._buffer.write(data)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self._closed = True

    def __getattr__(self, item: str) -> Any:
        return getattr(self._buffer, item)


class ResponseSink:
    """``HttpServletResponse`` 的最小替身，只给 :meth:`SysFileService.get_file` 用.

    Java 直接往 servlet 的响应流里写字节；FastAPI 的响应对象是不可变的，所以这里先攒到
    一个缓冲区里，再由控制器一次性构造成 ``Response``。

    三个字段的语义与 servlet 一致：

    * :attr:`content_type` —— :meth:`set_content_type` 之前是 ``None``（对应"没设过"）；
    * :attr:`headers`      —— ``add_header`` / ``set_header`` 攒下来的头（**有序**）；
    * :attr:`body`         —— 攒下来的字节。
    """

    def __init__(self) -> None:
        self.content_type: Optional[str] = None
        self._buffer = BytesIO()
        self._stream = _CloseTolerantStream(self._buffer)
        #: ``(name, value)`` 列表 —— 保序，且允许同名多个（``addHeader`` 语义）
        self._headers: List[tuple] = []

    # Java: response.setContentType(String)
    def set_content_type(self, content_type: str) -> None:
        self.content_type = content_type

    # Java: response.addHeader(String, String)
    def add_header(self, name: str, value: str) -> None:
        self._headers.append((name, value))

    # Java: response.setHeader(String, String)
    def set_header(self, name: str, value: str) -> None:
        lowered = name.lower()
        self._headers = [pair for pair in self._headers if pair[0].lower() != lowered]
        self._headers.append((name, value))

    @property
    def headers(self) -> Dict[str, str]:
        """去重后的响应头（**后者覆盖前者**），交给 ``starlette.Response``."""
        merged: Dict[str, str] = {}
        for name, value in self._headers:
            merged[name] = value
        return merged

    # Java: response.getOutputStream()
    def get_output_stream(self) -> BinaryIO:
        return self._stream

    @property
    def body(self) -> bytes:
        return self._buffer.getvalue()


class SysFileService:
    """Java: ``ISysFileService`` (impl: ``SysFileServiceImpl``)."""

    def __init__(
        self,
        file_mapper: Optional[SysFileMapper] = None,
        oss_template: Optional[OssTemplate] = None,
        file_api: Optional[FileApi] = None,
    ) -> None:
        self._file_mapper = file_mapper or SysFileMapper()
        self._oss_template = oss_template or OssTemplate()
        self._file_api = file_api

    # ------------------------------------------------------------------ 依赖访问器

    @property
    def file_mapper(self) -> SysFileMapper:
        return self._file_mapper

    @property
    def oss_template(self) -> OssTemplate:
        return self._oss_template

    @property
    def oss_properties(self):
        """Java: ``private final OssProperties ossProperties``."""
        return get_settings().oss

    @property
    def id_worker(self):
        """Java: ``@Autowired private SnowflakeIdWorker idWorker``."""
        return get_id_worker()

    @property
    def file_api(self) -> FileApi:
        """Java: ``@Resource private FileApi fileApi``."""
        if self._file_api is None:
            self._file_api = get_file_api()
        return self._file_api

    # ------------------------------------------------------------------ 查询

    # Java: List<SysFile> selectSysFileByIds(String ids)
    def select_sys_file_by_ids(self, ids: Any) -> List[SysFile]:
        """``ids.split(",")`` —— **不 trim**，也不过滤空串（``"1,,2"`` -> ``["1","","2"]``）。"""
        return self._file_mapper.select_sys_file_by_ids(str(ids).split(","))

    # Java: SysFile selectSysFileById(Long id)
    def select_sys_file_by_id(self, id: Any) -> Optional[SysFile]:
        return self._file_mapper.select_sys_file_by_id(id)

    # Java: List<SysFile> selectSysFileList(SysFile sysFile)
    def select_sys_file_list(self, entity: SysFile) -> List[SysFile]:
        return self._file_mapper.select_sys_file_list(entity)

    # ------------------------------------------------------------------ 增改

    # Java: AjaxResult saveSysFile(SysFile sysFile)
    def save_sys_file(self, entity: SysFile) -> AjaxResult:
        """有 ``id`` 就改、没 ``id`` 就新增（新增时补雪花 id 与四个审计列）。"""
        user_id = SecurityUtils.get_user_id()
        cur_date = get_timestamp()
        # Java: if (sysFile.getId() != null) —— **只判 null**，不是 isNotEmpty
        if entity.id is not None:
            entity.update_user = _to_java_string(user_id)
            entity.update_time = cur_date
            self._file_mapper.update_sys_file(entity)
        else:
            entity.del_flag = "0"
            entity.create_user = _to_java_string(user_id)
            entity.create_time = cur_date
            entity.update_user = _to_java_string(user_id)
            entity.update_time = cur_date
            # Java: sysFile.setId(idWorker.nextId()); —— 主键手动赋值
            entity.id = self.id_worker.next_id()
            self._file_mapper.insert_sys_file(entity)
        # Java: AjaxResult.success("操作成功！", sysFile.getId()) —— 全角叹号
        return AjaxResult.success_message_data("操作成功！", entity.id)

    # ------------------------------------------------------------------ 删除

    # Java: AjaxResult deleteSysFileByIds(Long[] ids)
    def delete_sys_file_by_ids(self, ids: Sequence[Any]) -> AjaxResult:
        """先逐个删 OSS 对象，再一次性软删除；任一环节抛错都回 ``error(msg)``。"""
        try:
            for id_value in ids:
                file = self._file_mapper.select_sys_file_by_id(id_value)
                # Java: file.getFileName() —— file 为 null 时 NPE，被下面的 catch 吃掉
                OssTemplate.remove_object(self.oss_properties.bucket_name, file.file_name)  # type: ignore[union-attr]
            count = self._file_mapper.delete_sys_file_by_ids(ids)
            return AjaxResult.success_data(count)
        except Exception as exc:  # noqa: BLE001 - Java: catch (Exception ex)
            return AjaxResult.error_message(_message_of(exc))

    # Java: AjaxResult deleteSysFileById(Long id)
    def delete_sys_file_by_id(self, id: Any) -> AjaxResult:
        try:
            file = self._file_mapper.select_sys_file_by_id(id)
            OssTemplate.remove_object(self.oss_properties.bucket_name, file.file_name)  # type: ignore[union-attr]
            count = self._file_mapper.delete_sys_file_by_id(id)
            return AjaxResult.success_data(count)
        except Exception as exc:  # noqa: BLE001 - Java: catch (Exception ex)
            return AjaxResult.error_message(_message_of(exc))

    # ------------------------------------------------------------------ 上传

    # Java: AjaxResult uploadFile(MultipartFile file)
    @transactional
    def upload_file(self, file: Any) -> AjaxResult:
        """单文件上传。**先 putObject 再读库**（与 ``upload_files`` 的顺序**相反**）。"""
        file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
        result_map = _new_result_map(file_name)
        try:
            OssTemplate.put_object(self.oss_properties.bucket_name, file_name, file.file)
            # 文件管理数据记录
            file_id = self._file_log(file, file_name)
            result_map["id"] = str(file_id)
        except Exception as exc:  # noqa: BLE001 - Java: catch (Exception e)
            return AjaxResult.error_message(_message_of(exc))
        return AjaxResult.success_data(result_map)

    # Java: AjaxResult uploadFiles(MultipartFile[] files)
    def upload_files(self, files: Sequence[Any]) -> AjaxResult:
        """多文件上传。**先登记再 putObject**，且扩展名不支持时**跳过**上传但仍返回该条。"""
        result_maps: List[Dict[str, str]] = []
        for file in files:
            file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
            result_map = _new_result_map(file_name)
            try:
                file_id = self._file_log(file, file_name)
                result_map["id"] = str(file_id)
                if file_id != -1:
                    OssTemplate.put_object(self.oss_properties.bucket_name, file_name, file.file)
            except Exception as exc:  # noqa: BLE001
                return AjaxResult.error_message(_message_of(exc))
            result_maps.append(result_map)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadByUrl(List<UploadByUrlRo> roList)
    def upload_by_url(self, ro_list: Optional[Sequence[UploadByUrlRo]]) -> AjaxResult:
        """按 url 下载再上传。单条失败只记日志、**跳过**（不中断整批、不回 error）。"""
        result_maps: List[Dict[str, str]] = []
        # Java: for (UploadByUrlRo ro : roList) —— roList 为 null 时 NPE
        for ro in ro_list:  # type: ignore[union-attr]
            # Java: ro.setFileName(CommonUtil.isNull(ro.getFileName()) + ".jpg")
            ro.file_name = _is_null(ro.file_name) + ".jpg"
            if _is_not_blank(ro.url):
                try:
                    image_bytes = self.file_api.download_image_to_byte_array(ro.url)  # type: ignore[arg-type]
                    file = convert_byte_to_multipart_file(image_bytes, ro.file_name)
                    file_name = simple_uuid() + FileUtil.DOT + _to_java_string(
                        FileUtil.ext_name(file.filename)
                    )
                    result_map = _new_result_map(file_name)

                    file_id = self._file_log(file, file_name)
                    result_map["id"] = str(file_id)
                    if file_id != -1:
                        OssTemplate.put_object(
                            self.oss_properties.bucket_name, file_name, file.file
                        )
                    result_maps.append(result_map)
                except Exception as exc:  # noqa: BLE001 - Java: catch -> log.error, 不 return
                    logger.error("上传失败", exc_info=exc)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadFilesUser(MultipartFile[] files, String userId)
    def upload_files_user(self, files: Sequence[Any], user_id: str) -> AjaxResult:
        """指定创建人的批量上传。**没有控制器调用**，照留。"""
        result_maps: List[Dict[str, str]] = []
        for file in files:
            file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
            result_map = _new_result_map(file_name)
            try:
                file_id = self._file_log_user(file, file_name, user_id)
                result_map["id"] = str(file_id)
                if file_id != -1:
                    OssTemplate.put_object(self.oss_properties.bucket_name, file_name, file.file)
            except Exception as exc:  # noqa: BLE001
                return AjaxResult.error_message(_message_of(exc))
            result_maps.append(result_map)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadSupplier(MultipartFile[] files, String[] bussNames)
    def upload_supplier(self, files: Sequence[Any], buss_names: Sequence[str]) -> AjaxResult:
        """按位置把 ``bussNames[i]`` 配给 ``files[i]``（**没有长度校验**）。"""
        result_maps: List[Dict[str, str]] = []
        # Java: for (int i = 0; i < files.length; i++) —— bussNames 更短时 AIOOBE
        for index in range(len(files)):
            file = files[index]
            buss_name = buss_names[index]
            file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
            result_map = _new_result_map(file_name)
            try:
                file_id = self._file_supplier_log(file, file_name, buss_name)
                result_map["id"] = str(file_id)
                if file_id != -1:
                    OssTemplate.put_object(self.oss_properties.bucket_name, file_name, file.file)
            except Exception as exc:  # noqa: BLE001
                return AjaxResult.error_message(_message_of(exc))
            result_maps.append(result_map)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadFilesPdf(MultipartFile[] files, HttpServletResponse response)
    def upload_files_pdf(self, files: Sequence[Any], response: Any = None) -> AjaxResult:
        """pdf 直传；其它类型**只落本地临时文件**（Word->PDF 转换被注释掉了）。

        ``response`` 参数在 Java 里虽然有，但唯一的使用是
        ``out = response.getOutputStream()``，下一行就被 ``new FileOutputStream(...)``
        覆盖 —— 也就是说**从来没有往响应里写过任何东西**。Python 侧保留参数、忽略它。
        """
        result_maps: List[Dict[str, str]] = []
        for file in files:
            file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
            result_map = _new_result_map(file_name)

            original = file.filename
            ext = FileUtil.ext_name(original)
            if ext is not None and ext == "pdf":
                try:
                    file_id = self._file_log(file, file_name)
                    result_map["id"] = str(file_id)
                    if file_id != -1:
                        OssTemplate.put_object(
                            self.oss_properties.bucket_name, file_name, file.file
                        )
                except Exception as exc:  # noqa: BLE001
                    return AjaxResult.error_message(_message_of(exc))
            else:
                try:
                    uuid_value = get_uuid()
                    urls = get_settings().ruoyi.upload_path + "/" + uuid_value
                    # Java: out = response.getOutputStream();  —— 没有任何输出，见 docstring
                    os.makedirs(urls, exist_ok=True)

                    file_path = urls + "/" + file_name
                    # 下面两个变量在 Java 里算完就没人用了（转换逻辑被注释）
                    _pdf_name = _replace_all(_replace_all(original or "", ".docx", ".pdf"), ".doc", ".pdf")
                    _pdf_file_path = _replace_all(
                        _replace_all(file_name, ".docx", ".pdf"), ".doc", ".pdf"
                    )

                    input_stream = file.file
                    with open(file_path, "wb") as out:
                        # Java: 1024 字节一块地拷
                        while True:
                            chunk = input_stream.read(1024)
                            if not chunk:
                                break
                            out.write(chunk)
                    # 转换 + 上传 + 清理临时文件：整块被注释，见模块 docstring
                except Exception as exc:  # noqa: BLE001
                    return AjaxResult.error_message(_message_of(exc))
            result_maps.append(result_map)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadFileId(Long fileId, MultipartFile files)
    @transactional
    def upload_file_id(self, file_id: Optional[int], file: Any) -> AjaxResult:
        """按指定主键"先删后插"再上传。``file_log_id`` 失败也不影响上传判断。"""
        result_maps: List[Dict[str, str]] = []
        file_name = simple_uuid() + FileUtil.DOT + _to_java_string(FileUtil.ext_name(file.filename))
        result_map = _new_result_map(file_name)
        try:
            self._file_log_id(file, file_name, file_id)
            result_map["id"] = _to_java_string(file_id)
            if file_id != -1:
                OssTemplate.put_object(self.oss_properties.bucket_name, file_name, file.file)
        except Exception as exc:  # noqa: BLE001
            return AjaxResult.error_message(_message_of(exc))
        result_maps.append(result_map)
        return AjaxResult.success_data(result_maps)

    # Java: AjaxResult uploadFilesEnc(MultipartFile[] files)
    def upload_files_enc(self, files: Sequence[Any]) -> AjaxResult:
        """**整块方法体被注释**，永远返回 ``success([])``（CA 加密未启用）。"""
        result_maps: List[Dict[str, str]] = []
        for _file in files:
            # Java: 这里是 /* ... */ 注释块，循环体是空的
            pass
        return AjaxResult.success_data(result_maps)

    # ------------------------------------------------------------------ 读取

    # Java: void getFile(String bucket, String fileName, HttpServletResponse response)
    def get_file(self, bucket: str, file_name: str, response: ResponseSink) -> None:
        """把 OSS 对象写进"响应"。异常**全部吞掉**（客户端拿到空 body + HTTP 200）。"""
        try:
            s3_object = self.oss_template.get_object(bucket, file_name)
            try:
                response.set_content_type("application/octet-stream; charset=UTF-8")
                FileUtil.io_copy(s3_object.get_object_content(), response.get_output_stream())
            finally:
                s3_object.close()
        except Exception:  # noqa: BLE001 - 响应已开始，客户端拿空 body；异常只进日志
            logger.exception("[文件下载失败] bucket=%s file=%s", bucket, file_name)

    # Java: void getFile(String bucket, String fileName, OutputStream os)
    def get_file_to_output_stream(self, bucket: str, file_name: str, output_stream: BinaryIO) -> None:
        """不设 content type，只拷字节。**没有控制器调用**，照留。"""
        try:
            s3_object = self.oss_template.get_object(bucket, file_name)
            try:
                FileUtil.io_copy(s3_object.get_object_content(), output_stream)
            finally:
                s3_object.close()
        except Exception:  # noqa: BLE001 - 输出流由调用方管理，这里只记录
            logger.exception(
                "[文件下载失败] bucket=%s file=%s (output stream)", bucket, file_name
            )

    # Java: void getFileToUrl(String bucket, String fileName, String fileUrl)
    def get_file_to_url(self, bucket: str, file_name: str, file_url: str) -> None:
        """把对象落成本地文件；异常只记日志。**没有控制器调用**，照留。"""
        try:
            s3_object = self.oss_template.get_object(bucket, file_name)
            object_content = s3_object.get_object_content()
            with open(file_url + "/" + file_name, "wb") as fos:
                while True:
                    chunk = object_content.read(1024)
                    if not chunk:
                        break
                    fos.write(chunk)
            object_content.close()
        except Exception:  # noqa: BLE001 - Java: log.error(...) 后吞掉
            logger.exception("[文件读取失败] bucket=%s file=%s url=%s", bucket, file_name, file_url)

    # Java: S3Object getFileObject(Long sysFileId)
    def get_file_object(self, sys_file_id: Any) -> Optional[S3Object]:
        sys_file = self.select_sys_file_by_id(sys_file_id)
        if sys_file is not None:
            try:
                return self.oss_template.get_object_info(sys_file.bucket_name, sys_file.file_name)  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001 - Java: e.printStackTrace()
                logger.exception("读取 OSS 对象失败: id=%s", sys_file_id)
        return None

    # Java: byte[] getByteObject(Long sysFileId)
    def get_byte_object(self, sys_file_id: Any) -> Optional[bytes]:
        sys_file = self.select_sys_file_by_id(sys_file_id)
        if sys_file is not None:
            try:
                s3_object = self.oss_template.get_object_info(
                    sys_file.bucket_name,  # type: ignore[arg-type]
                    sys_file.file_name,  # type: ignore[arg-type]
                )
                input_stream = s3_object.get_object_content()
                buffer = BytesIO()
                while True:
                    chunk = input_stream.read(1024)
                    if not chunk:
                        break
                    buffer.write(chunk)
                input_stream.close()
                return buffer.getvalue()
            except Exception:  # noqa: BLE001 - Java: e.printStackTrace()
                logger.exception("读取 OSS 对象失败: id=%s", sys_file_id)
        return None

    # ------------------------------------------------------------------ CA / base64

    # Java: AjaxResult updateCAFile(SysFile sysFile)
    def update_ca_file(self, entity: SysFile) -> AjaxResult:
        """先物理删除 id=3001 的旧记录（连同 OSS 对象），再把本条的主键改成 3001。"""
        user_id = SecurityUtils.get_user_id()
        cur_date = get_timestamp()
        entity.update_user = _to_java_string(user_id)
        entity.update_time = cur_date

        # Java: this.deleteSysFileByIdNew(3001L);
        self.delete_sys_file_by_id_new(3001)

        self._file_mapper.update_ca_file(entity)

        # Java: AjaxResult.success("操作成功！", sysFile.getId()) —— 返回的是**原 id**
        return AjaxResult.success_message_data("操作成功！", entity.id)

    # Java: public void deleteSysFileByIdNew(Long id)（**不是**接口方法）
    def delete_sys_file_by_id_new(self, id: Any) -> None:
        """物理删除 + 删 OSS 对象。异常**全部吞掉**、不回任何东西。"""
        try:
            file = self._file_mapper.select_sys_file_by_id(id)
            OssTemplate.remove_object(self.oss_properties.bucket_name, file.file_name)  # type: ignore[union-attr]
            self._file_mapper.delete_sys_file_by_id_new(id)
        except Exception:  # noqa: BLE001 - Java: catch (Exception ex) {}
            pass

    # Java: String getFileUrl(Long fileId)
    def get_file_url(self, file_id: Any) -> Optional[str]:
        """**方法体被注释**，永远返回 ``None``。照留。"""
        return None

    # Java: AjaxResult uploadBase64Picture(String base64Picture, SysFile sysFile)
    @transactional
    def upload_base64_picture(self, base64_picture: Optional[str], entity: SysFile) -> AjaxResult:
        """base64 图片上传：**先写库再上传**，失败回 ``error()``（默认文案「操作失败」）。"""
        # Java: byte[] decode = Base64.decode(base64Picture);  —— 非法输入返回 null
        decoded = base64_utils.decode(base64_picture)
        file_name = simple_uuid() + FileUtil.DOT + _to_java_string(entity.type)
        byte_array_input_stream: Optional[BytesIO] = None
        try:
            # Java: ``new ByteArrayInputStream(decode)`` —— ``decode`` 为 ``null`` 时 NPE。
            # 注意 ``BytesIO(None)`` 在 CPython 里等价于空缓冲区、**不会**报错，所以必须
            # 显式判空；否则非法 base64 会被"成功"上传成一个 0 字节对象。
            if decoded is None:
                raise ValueError("Base64 解码结果为空")
            byte_array_input_stream = BytesIO(decoded)

            entity.file_name = file_name
            ajax_result = self.save_sys_file(entity)
            # Java: if (!"200".equals(String.valueOf(ajaxResult.get(CODE_TAG))))
            if str(ajax_result.get(AjaxResult.CODE_TAG)) != "200":
                return AjaxResult.error_message("上传图片失败!")
            file_id = str(ajax_result.get(AjaxResult.DATA_TAG))

            OssTemplate.put_object(
                self.oss_properties.bucket_name, file_name, byte_array_input_stream
            )
            # Java: AjaxResult.success(fileId) -> success(String msg) —— 没有 data 键
            return AjaxResult.success_message(file_id)
        except Exception:  # noqa: BLE001 - Java: e.printStackTrace()
            logger.exception("上传 base64 图片失败")
        finally:
            if byte_array_input_stream is not None:
                byte_array_input_stream.close()
        return AjaxResult.error()

    # Java: String uploadBase64Picture(String richText)
    def upload_base64_picture_rich_text(self, rich_text: Optional[str]) -> Optional[str]:
        """**方法体被注释**：空白入参原样返回，其余返回 ``""``。照留。"""
        if is_blank(rich_text):
            return rich_text
        return ""

    # Java: Long uploadFile(InputStream is, SysFile sysFile)
    def upload_file_from_stream(self, input_stream: BinaryIO, entity: SysFile) -> Optional[int]:
        """**方法体被注释**：只返回一个新生成的雪花 id（不写库、不上传）。照留。"""
        try:
            return self.id_worker.next_id()
        except Exception as exc:  # noqa: BLE001 - Java: log.error(...)
            logger.error("上传失败：%s", exc)
        return None

    # ------------------------------------------------------------------ 登记（私有）

    def _file_log(self, file: Any, file_name: str) -> int:
        """Java: ``private Long fileLog(MultipartFile, String)``."""
        sys_file = SysFile()
        original = file.filename
        sys_file.file_name = file_name
        sys_file.original = original
        sys_file.file_size = size_of(file)
        ext = FileUtil.ext_name(original)
        if ext is not None and ext != "":
            ext = ext.lower()
            if _matches_any(ext, _SUPPORTED_EXTENSIONS):
                sys_file.type = ext
                sys_file.bucket_name = self.oss_properties.bucket_name
                # Java 里这两行是重复的（复制粘贴残留），行为无差别，照抄一次即可
                sys_file.create_user = _to_java_string(SecurityUtils.get_user_id())
                self.save_sys_file(sys_file)
            else:
                sys_file.id = -1
        else:
            sys_file.id = -1
        return sys_file.id  # type: ignore[return-value]

    def _file_supplier_log(self, file: Any, file_name: str, buss_name: str) -> int:
        """Java: ``private Long fileSupplierLog(MultipartFile, String, String)``."""
        sys_file = SysFile()
        original = file.filename
        sys_file.file_name = file_name
        sys_file.buss_name = buss_name
        sys_file.original = original
        sys_file.file_size = size_of(file)
        ext = FileUtil.ext_name(original)
        if ext is not None and ext != "":
            ext = ext.lower()
            if _matches_any(ext, _SUPPORTED_EXTENSIONS):
                sys_file.type = ext
                sys_file.bucket_name = self.oss_properties.bucket_name
                sys_file.create_user = _to_java_string(SecurityUtils.get_user_id())
                self.save_sys_file(sys_file)
            else:
                sys_file.id = -1
        else:
            sys_file.id = -1
        return sys_file.id  # type: ignore[return-value]

    def _file_log_id(self, file: Any, file_name: str, file_id: Optional[int]) -> Optional[int]:
        """Java: ``private Long fileLogId(MultipartFile, String, Long)`` —— 先删后插。"""
        sys_file = SysFile()
        original = file.filename
        sys_file.file_name = file_name
        sys_file.original = original
        sys_file.file_size = size_of(file)
        ext = FileUtil.ext_name(original)
        if ext is not None and ext != "":
            ext = ext.lower()
            if _matches_any(ext, _SUPPORTED_EXTENSIONS_FOR_ID):
                # 先删除 后新增
                self.delete_sys_file_by_id_new(file_id)

                sys_file.id = file_id
                sys_file.type = ext
                sys_file.bucket_name = self.oss_properties.bucket_name

                user_id = SecurityUtils.get_user_id()
                cur_date = get_timestamp()
                sys_file.del_flag = "0"
                sys_file.create_user = _to_java_string(user_id)
                sys_file.create_time = cur_date
                sys_file.update_user = _to_java_string(user_id)
                sys_file.update_time = cur_date
                self._file_mapper.insert_sys_file(sys_file)
            else:
                sys_file.id = -1
        else:
            sys_file.id = -1
        return sys_file.id

    def _file_log_user(self, file: Any, file_name: str, user_id: str) -> int:
        """Java: ``private Long fileLogUser(MultipartFile, String, String)``.

        注意它**不写** ``del_flag``（绕过了 ``saveSysFile``），所以插入的行
        ``del_flag`` 为 NULL，列表查不到。
        """
        sys_file = SysFile()
        cur_date = get_timestamp()
        original = file.filename
        sys_file.file_name = file_name
        sys_file.original = original
        sys_file.file_size = size_of(file)
        ext = FileUtil.ext_name(original)
        if ext is not None and ext != "":
            ext = ext.lower()
            if _matches_any(ext, _SUPPORTED_EXTENSIONS):
                sys_file.type = ext
                sys_file.bucket_name = self.oss_properties.bucket_name
                sys_file.create_user = user_id
                sys_file.create_time = cur_date
                sys_file.update_time = cur_date
                sys_file.id = self.id_worker.next_id()
                self._file_mapper.insert_sys_file(sys_file)
            else:
                sys_file.id = -1
        else:
            sys_file.id = -1
        return sys_file.id  # type: ignore[return-value]


# --------------------------------------------------------------------------- 内部


def _new_result_map(file_name: str) -> Dict[str, str]:
    """Java: ``new HashMap<>(4)`` + 三个固定键（``id`` 之后按需补）。"""
    return {
        "bucketName": _bucket_name(),
        "fileName": file_name,
        "url": FILE_URL_TEMPLATE.format(_bucket_name(), file_name),
    }


def _bucket_name() -> str:
    return get_settings().oss.bucket_name


def _matches_any(ext: str, whitelist: Sequence[str]) -> bool:
    """Java: ``ext.indexOf(x) > -1 || ...`` —— **子串**匹配，不是等值。"""
    return any(item in ext for item in whitelist)


def _to_java_string(value: Any) -> str:
    """Java 的字符串拼接：``null`` 变成字面量 ``"null"``。

    ``IdUtil.simpleUUID() + StrUtil.DOT + file.getType()`` 里 ``getType()`` 为 null 时，
    Java 得到的是 ``"...null"`` 而**不是** ``"..."``。文件名后缀因此变成一个不存在的
    扩展名 —— 既有行为，照抄。
    """
    return "null" if value is None else str(value)


def _message_of(exc: BaseException) -> str:
    """Java: ``ex.getMessage()``（可能为 ``null``）。"""
    message = getattr(exc, "message", None)
    if isinstance(message, str):
        return message
    return str(exc)


def _is_null(names: Any) -> str:
    """Java: ``com.ruoyi.web.util.CommonUtil.isNull(Object)``."""
    from app.api.util.common_util import is_null

    return is_null(names)


def _is_not_blank(value: Optional[str]) -> bool:
    from app.api.util.common_util import is_not_blank

    return is_not_blank(value)


def _replace_all(source: str, target: str, replacement: str) -> str:
    """Java ``String.replaceAll`` —— 参数是**正则**，``.`` 匹配任意字符。"""
    import re

    return re.sub(target, replacement, source)


_SERVICE: Optional[SysFileService] = None


def get_file_service() -> SysFileService:
    """Process-wide service (Spring's default singleton scope)."""
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = SysFileService()
    return _SERVICE


def reset_file_service() -> None:
    """Test helper: drop the cached service so fakes can be injected."""
    global _SERVICE
    _SERVICE = None


__all__ = [
    "SysFileService",
    "ResponseSink",
    "get_file_service",
    "reset_file_service",
    "MockMultipartFile",
    "FILE_URL_TEMPLATE",
]
