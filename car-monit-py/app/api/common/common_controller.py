"""通用请求处理 控制器.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CommonController.java

**4** 个映射，全部迁移（本类没有 `export`、没有 @PreAuthorize）
----------------------------------------------------------------
==========================  ==================================  ============================
Java                        Method / Path                       权限（SecurityConfig）
==========================  ==================================  ============================
``fileDownload``            GET ``/common/download``            ``anonymous()``
``uploadFile``              POST ``/common/upload``             ``anyRequest().authenticated()``
``uploadFiles``             POST ``/common/uploads``            ``anyRequest().authenticated()``
``resourceDownload``        GET ``/common/download/resource``   ``authenticated()``
==========================  ==================================  ============================

``/common/download`` 是 **anonymous()**
---------------------------------------
``SecurityConfig`` 里 ``.antMatchers("/common/download**").anonymous()``。``anonymous()``
是"**只**允许匿名"：**已登录**的请求反而会 403。所以这个端点只能由未登录场景调用，
或者由前端在请求时不带 token。

下一行 ``.antMatchers("/common/download/resource**").authenticated()`` **不会**被
上一行遮蔽 —— 这一点容易误判。Spring 的 ``AntPathMatcher`` 先按 ``/`` 切段：
``/common/download**`` 切出 ``["common", "download**"]``，而
``/common/download/resource`` 切出 ``["common", "download", "resource"]``。第二段
``download**`` 能匹配 ``download``，但此时**路径还有剩余段、模式已用完** -> ``doMatch``
直接 ``return false``。所以 ``resourceDownload`` 真的是 ``authenticated()``。
（这与 ``COMPATIBILITY.md`` §20 说的"静态资源规则遮蔽 denyAll"不是同一类问题：
那是模式**排序**，这里是模式**形状**。）

``fileDownload`` 的四个坑
-------------------------
1. **``fileName`` / ``delete`` 都是可选的**。Spring 对**没有注解**的简单类型参数用
   ``RequestParamNamedValueInfo()``（``required = false``），所以缺参不会 400：

   * 缺 ``fileName`` -> ``checkAllowDownload(null)`` 里 ``getFileType(null)`` NPE ->
     被 ``catch`` 吞掉 -> **200 + 空 body**；
   * 缺 ``delete``   -> 文件**正常下载**，随后 ``if (delete)`` 拆箱 NPE ->
     被 ``catch`` 吞掉 -> **文件不删除**，日志里多一条错误。

2. **文件不存在不是 404**。``FileUtils.writeBytes`` 抛 ``FileNotFoundException``，
   但它在 ``finally`` 里已经关掉了输出流 —— servlet 世界"关流 = 提交响应"，所以
   客户端拿到的是 **200 + 完整响应头 + 空 body**。

3. ``realFileName = System.currentTimeMillis() + fileName.substring(fileName.indexOf("_") + 1)``。
   文件名里**没有** ``_`` 时 ``indexOf`` 返回 ``-1``，``substring(0)`` 就是整个文件名 ——
   不会抛异常。有 ``_`` 时只保留**第一个** ``_`` 之后的部分。

4. ``delete`` 的取值走 Spring 的 ``StringToBooleanConverter``：``{true,on,yes,1}`` /
   ``{false,off,no,0}``，其它值抛异常 -> ``MethodArgumentTypeMismatchException`` ->
   ``code 500`` + 中文文案。

``resourceDownload`` 的方法体**整块被注释**
------------------------------------------
只有 ``checkAllowDownload`` 那道闸是活的，后面"读本地文件 + 写响应"四行全是注释。
所以：

* 白名单**通过** -> 什么都不做 -> **200 + 空 body + 无任何响应头**；
* 白名单**拒绝** -> 抛异常被吞 -> 同上，只是多一条日志。

这个端点在本项目里**没有任何调用方**，按迁移原则第 4 条照留。
"""

from __future__ import annotations

import logging
import time
from typing import Annotated, List, Optional

from fastapi import APIRouter, File, Query, Request, Response, UploadFile

from app.common.core.domain.ajax_result import AjaxResult
from app.common.exception.exceptions import CustomException, RuoYiBaseException, ServiceException
from app.common.utils import file_upload_utils as FileUploadUtils
from app.common.utils import file_utils as FileUtils
from app.common.utils.file_utils import set_attachment_response_header
from app.common.utils.string_utils import format as java_format
from app.framework.config import server_config as ServerConfig
from app.settings import get_settings
from app.system.service.sys_file_service import ResponseSink

logger = logging.getLogger("app.api.common.common_controller")

router = APIRouter(prefix="/common", tags=["common"])

#: Java: ``FILE_DELIMETER = ","``（Java 原文就拼错成 ``DELIMETER``，这里不改名）
FILE_DELIMETER = ","

#: Java: ``MediaType.APPLICATION_OCTET_STREAM_VALUE``
APPLICATION_OCTET_STREAM_VALUE = "application/octet-stream"

#: 上传 I/O 故障（磁盘满、路径不可写、S3 报错）对外的统一文案。
#: Java 返回 ``e.getMessage()``，但那会把绝对路径、容量等内部信息交给客户端；
#: 这里改为固定文案，真正的异常只进日志（COMPATIBILITY §46.3 已登记偏离）。
UPLOAD_ERROR_MESSAGE = "上传失败，请稍后重试"

#: Spring ``StringToBooleanConverter`` 的真值集合
_TRUE_LITERALS = frozenset({"true", "on", "yes", "1"})
_FALSE_LITERALS = frozenset({"false", "off", "no", "0"})


# --------------------------------------------------------------------------- 内部


def _spring_boolean(name: str, raw: Optional[str]) -> Optional[bool]:
    """Java: 形参 ``Boolean delete`` 的类型转换.

    ``raw`` 为 ``None`` 表示请求里没有这个参数 —— 直接返回 ``None``（**不要**当成
    ``false``：Java 缺参时是 ``null``，后面 ``if (delete)`` 会 NPE）。

    无法识别时抛 :class:`ServiceException`，对应 Java 的
    ``MethodArgumentTypeMismatchException`` -> ``GlobalExceptionHandler`` 的中文文案。
    用 ``ServiceException`` 而不是 ``ValueError``：``Exception`` 处理器挂在
    ``ServerErrorMiddleware`` 上，响应发完还会**重新抛**（见
    :mod:`app.config.exception_handlers`）。
    """
    if raw is None:
        return None
    value = raw.strip()
    lowered = value.lower()
    if lowered in _TRUE_LITERALS:
        return True
    if lowered in _FALSE_LITERALS:
        return False
    raise ServiceException(
        "请求参数类型不匹配，参数[%s]要求类型为：'java.lang.Boolean'，但输入值为：'%s'"
        % (name, value)
    )


def _message_of(exc: BaseException) -> Optional[str]:
    """Java: ``e.getMessage()``（NPE 之类返回 ``null``，见 ``COMPATIBILITY.md`` §36.15）."""
    message = getattr(exc, "message", None)
    if isinstance(message, str):
        return message
    return str(exc)


def _upload_error_message(exc: BaseException) -> str:
    """上传失败时的对外文案：业务校验保留原文，I/O 与未预期异常固定脱敏."""
    if isinstance(exc, (RuoYiBaseException, ServiceException, CustomException)):
        return _message_of(exc) or ""
    return UPLOAD_ERROR_MESSAGE


def _to_response(sink: ResponseSink) -> Response:
    """把 :class:`ResponseSink` 攒下来的字节 / 头变成不可变的响应.

    ``content_type`` 为 ``None`` 表示 Java 没调用过 ``setContentType``（异常路径），
    此时**不发** ``Content-Type`` 头。
    """
    headers = dict(sink.headers)
    if sink.content_type is not None:
        headers["Content-Type"] = sink.content_type
    return Response(content=sink.body, headers=headers)


# --------------------------------------------------------------------------- 下载


@router.get("/download", response_model=None)
def file_download(
    request: Request,
    file_name: Annotated[Optional[str], Query(alias="fileName")] = None,
    delete: Annotated[Optional[str], Query(alias="delete")] = None,
) -> Response:
    """通用下载请求. Java: ``@GetMapping("/download") public void fileDownload(...)``.

    该端点只有 **anonymous()** 权限（见模块 docstring）。
    """
    sink = ResponseSink()
    # 先做类型转换：Java 在**进入方法体之前**就完成绑定，转换失败时方法体一行都不执行。
    delete_flag = _spring_boolean("delete", delete)
    try:
        if not FileUtils.check_allow_download(file_name):
            raise RuntimeError(
                java_format("文件名称({})非法，不允许下载。 ", file_name)
            )
        assert file_name is not None  # checkAllowDownload 已保证非空
        # Java: fileName.substring(fileName.indexOf("_") + 1)；没有 "_" 时 indexOf == -1
        underscore = file_name.find("_")
        real_file_name = str(_current_time_millis()) + (
            file_name[underscore + 1 :] if underscore >= 0 else file_name
        )
        file_path = get_settings().ruoyi.download_path + file_name

        sink.set_content_type(APPLICATION_OCTET_STREAM_VALUE)
        set_attachment_response_header(sink, real_file_name)
        FileUtils.write_bytes(file_path, sink.get_output_stream())
        if delete_flag:
            FileUtils.delete_file(file_path)
    except Exception:  # noqa: BLE001 - Java: catch (Exception e) { log.error(...) }
        logger.error("下载文件失败", exc_info=True)
    return _to_response(sink)


@router.get("/download/resource", response_model=None)
def resource_download(
    request: Request,
    resource: Annotated[Optional[str], Query()] = None,
) -> Response:
    """本地资源通用下载（**方法体整块被注释**）. Java: ``@GetMapping("/download/resource")``.

    活着的只有 ``checkAllowDownload`` 那道闸；通过与否的响应完全一样（200 + 空 body）。
    """
    try:
        if not FileUtils.check_allow_download(resource):
            raise RuntimeError(
                java_format("资源文件({})非法，不允许下载。 ", resource)
            )
        # Java: 以下全部被注释掉 —— 本地资源路径 / 数据库资源地址 / 下载名称 / 写字节
        #   String localPath = RuoYiConfig.getProfile();
        #   String downloadPath = localPath + StringUtils.substringAfter(resource, Constants.RESOURCE_PREFIX);
        #   String downloadName = StringUtils.substringAfterLast(downloadPath, "/");
        #   response.setContentType(MediaType.APPLICATION_OCTET_STREAM_VALUE);
        #   FileUtils.setAttachmentResponseHeader(response, downloadName);
        #   FileUtils.writeBytes(downloadPath, response.getOutputStream());
    except Exception:  # noqa: BLE001 - Java: catch (Exception e) { log.error(...) }
        logger.error("下载文件失败", exc_info=True)
    return Response(content=b"")


# --------------------------------------------------------------------------- 上传


@router.post("/upload", response_model=None)
def upload_file(request: Request, file: Annotated[UploadFile, File()]) -> AjaxResult:
    """通用上传请求（单个）. Java: ``@PostMapping("/upload") public AjaxResult uploadFile(MultipartFile file)``.

    返回体在 ``code`` / ``msg`` 之后依次追加 ``url`` / ``fileName`` / ``newFileName`` /
    ``originalFilename``（顺序与 Java 的 4 次 ``ajax.put`` 一致）。
    """
    try:
        # 上传文件路径
        file_path = get_settings().ruoyi.upload_path
        # 上传并返回新文件名称
        file_name = FileUploadUtils.upload(file_path, file)
        url = ServerConfig.get_url(request) + file_name
        ajax = AjaxResult.success()
        ajax.put_chain("url", url)
        ajax.put_chain("fileName", file_name)
        ajax.put_chain("newFileName", FileUtils.get_name(file_name))
        ajax.put_chain("originalFilename", file.filename)
        return ajax
    except Exception as exc:  # noqa: BLE001 - Java: catch (Exception e)
        logger.error("上传文件失败: %s", exc, exc_info=True)
        return AjaxResult.error_message(_upload_error_message(exc))


@router.post("/uploads", response_model=None)
def upload_files(
    request: Request, files: Annotated[List[UploadFile], File()]
) -> AjaxResult:
    """通用上传请求（多个）. Java: ``@PostMapping("/uploads") public AjaxResult uploadFiles(List<MultipartFile> files)``.

    Java 的形参 ``List<MultipartFile>`` **没有** ``@RequestParam``，但 Spring 的
    ``MultipartResolutionDelegate.isMultipartArgument`` 认这种"泛型是 MultipartFile 的
    集合"，按参数名 ``files`` 取所有同名部件 —— 所以前端是把多个文件都放在 **同一个**
    ``files`` 字段里重复提交。

    四个返回值都是**逗号拼接**的字符串（不是数组）：``urls`` / ``fileNames`` /
    ``newFileNames`` / ``originalFilenames``。

    一个失败就整体 ``error`` —— 前面已经落盘的文件**不会**被清理。
    """
    try:
        file_path = get_settings().ruoyi.upload_path
        urls: List[str] = []
        file_names: List[str] = []
        new_file_names: List[str] = []
        original_filenames: List[str] = []
        for file in files:
            # 上传并返回新文件名称
            file_name = FileUploadUtils.upload(file_path, file)
            url = ServerConfig.get_url(request) + file_name
            urls.append(url)
            file_names.append(file_name)
            new_file_names.append(FileUtils.get_name(file_name) or "")
            original_filenames.append(file.filename or "")
        ajax = AjaxResult.success()
        ajax.put_chain("urls", FILE_DELIMETER.join(urls))
        ajax.put_chain("fileNames", FILE_DELIMETER.join(file_names))
        ajax.put_chain("newFileNames", FILE_DELIMETER.join(new_file_names))
        ajax.put_chain("originalFilenames", FILE_DELIMETER.join(original_filenames))
        return ajax
    except Exception as exc:  # noqa: BLE001 - Java: catch (Exception e)
        logger.error("批量上传文件失败: %s", exc, exc_info=True)
        return AjaxResult.error_message(_upload_error_message(exc))


def _current_time_millis() -> int:
    """Java: ``System.currentTimeMillis()``."""
    return int(time.time() * 1000)


__all__ = [
    "APPLICATION_OCTET_STREAM_VALUE",
    "FILE_DELIMETER",
    "router",
    "file_download",
    "upload_file",
    "upload_files",
    "resource_download",
]
