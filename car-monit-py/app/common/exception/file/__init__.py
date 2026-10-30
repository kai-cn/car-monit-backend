"""文件相关异常类 / file exceptions.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileUploadException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileSizeLimitExceededException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/file/FileNameLengthLimitExceededException.java
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/file/InvalidExtensionException.java

Java 把这一组异常放在 ``com.ruoyi.common.exception.file`` 子包里，Python 侧同样
落成子包 ``app.common.exception.file``（与 ``app.common.exception.user`` 一致）。

两个互不相干的族
----------------
::

    java.lang.RuntimeException
      +-- BaseException
            +-- FileException                  <- 本包
                  +-- FileSizeLimitExceededException
                  +-- FileNameLengthLimitExceededException

    java.lang.Exception       (checked)
      +-- FileUploadException                  <- 本包
            +-- InvalidExtensionException
                  +-- InvalidImageExtensionException
                  +-- InvalidFlashExtensionException
                  +-- InvalidMediaExtensionException
                  +-- InvalidVideoExtensionException

**这个分裂是有意义的，不要合并**：它决定客户端看到的响应形态。

* ``FileException`` 族继承 :class:`RuoYiBaseException`（即 ``RuntimeError``），消息
  由 i18n 解析，落到 ``GlobalExceptionHandler`` 的 ``RuntimeException`` 分支
  -> ``AjaxResult.error_message(...)`` -> HTTP 200 + ``code 500``。
* ``FileUploadException`` 族继承 ``Exception``（对应 Java 的 checked 异常），落到
  ``Exception`` 分支。文案里的文件名/后缀是**拼出来的**，不走 i18n。

``FileUploadUtils.upload(baseDir, file)``（2 参重载）会把这两族统统包成
``IOException``，所以从 ``SysProfileController`` 出去的永远是"IOException 的 message
= 原异常的 message"，HTTP 200 + ``code 500``。
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from app.common.exception.exceptions import RuoYiBaseException


def _java_str(value: Any) -> str:
    """Java 的 ``String + null`` 拼出 ``"null"``，Python 的 ``str(None)`` 是 ``"None"``。"""
    return "null" if value is None else str(value)


def _arrays_to_string(values: Optional[Sequence[str]]) -> str:
    """Java: ``Arrays.toString(String[])`` -> ``[bmp, gif, png]``；``null`` 数组 -> ``"null"``。"""
    if values is None:
        return "null"
    return "[" + ", ".join(_java_str(value) for value in values) + "]"


class FileException(RuoYiBaseException):
    """文件信息异常类.

    Java: ``public class FileException extends BaseException`` ->
    ``super("file", code, args, null)``：模块固定为 ``"file"``，没有 defaultMessage，
    所以消息一定来自 ``config/i18n/messages.properties``。
    """

    # Java: public FileException(String code, Object[] args)
    def __init__(self, code: str, args: Optional[List[Any]] = None) -> None:
        super().__init__(default_message=None, module="file", code=code, args=args)


class FileSizeLimitExceededException(FileException):
    """文件大小超限。Java: ``super("upload.exceed.maxSize", new Object[] { defaultMaxSize })``.

    注意 ``defaultMaxSize`` 是**调用方除过的 MB 数**（``50``），不是字节数 ——
    看 ``FileUploadUtils.assertAllowed`` 的 ``DEFAULT_MAX_SIZE / 1024 / 1024``。
    """

    def __init__(self, default_max_size: int) -> None:
        super().__init__("upload.exceed.maxSize", [default_max_size])


class FileNameLengthLimitExceededException(FileException):
    """文件名超长. Java: ``super("upload.filename.exceed.length", new Object[] { ... })``."""

    def __init__(self, default_file_name_length: int) -> None:
        super().__init__("upload.filename.exceed.length", [default_file_name_length])


class FileUploadException(Exception):
    """文件上传异常类 (checked).

    Java 原版自己实现了一遍 ``printStackTrace`` / ``getCause``（因为 JDK 1.4 之前的
    习惯写法）。Python 的 ``raise ... from cause`` 已经承担了这部分职责，所以只保留
    ``cause`` 字段与 :meth:`get_cause`，让调用点仍然读作 ``e.getCause()``。
    """

    # Java: public FileUploadException() / (String msg) / (String msg, Throwable cause)
    def __init__(self, message: Optional[str] = None, cause: Optional[BaseException] = None) -> None:
        self.message: Optional[str] = message
        self.cause: Optional[BaseException] = cause
        super().__init__(message)

    # Java: @Override public Throwable getCause()
    def get_cause(self) -> Optional[BaseException]:
        """Java: ``getCause()``."""
        return self.cause

    def __str__(self) -> str:
        return self.message or ""


class InvalidExtensionException(FileUploadException):
    """文件后缀不合法.

    Java 的四个 ``static`` 内部类是**同一段文案**的不同类型，只为让 ``catch`` 能区分
    （本项目的代码从不 catch，所以实际观察不到差别）。这里原样保留嵌套类的层次与名字，
    调用点仍然读作 ``InvalidExtensionException.InvalidImageExtensionException``。
    """

    # Java: public InvalidExtensionException(String[] allowedExtension, String extension, String filename)
    def __init__(
        self,
        allowed_extension: Optional[Sequence[str]],
        extension: Optional[str],
        filename: Optional[str],
    ) -> None:
        self.allowed_extension: Optional[Sequence[str]] = allowed_extension
        self.extension: Optional[str] = extension
        self.filename: Optional[str] = filename
        super().__init__(
            "文件["
            + _java_str(filename)
            + "]后缀["
            + _java_str(extension)
            + "]不正确，请上传"
            + _arrays_to_string(allowed_extension)
            + "格式",
            None,
        )

    # Java: public String[] getAllowedExtension()
    def get_allowed_extension(self) -> Optional[Sequence[str]]:
        return self.allowed_extension

    # Java: public String getExtension()
    def get_extension(self) -> Optional[str]:
        return self.extension

    # Java: public String getFilename()
    def get_filename(self) -> Optional[str]:
        return self.filename


# Python 的类体作用域里看不到"正在定义的那个类"，所以 Java 的 4 个 static 内部类只能
# 先定义成模块级类、再挂回父类，建成与 Java 相同的 ``InvalidExtensionException.Xxx``
# 访问路径。
class InvalidImageExtensionException(InvalidExtensionException):
    """图片后缀不合法（Java: ``static class``，行为与父类完全一致）。"""


class InvalidFlashExtensionException(InvalidExtensionException):
    """flash 后缀不合法."""


class InvalidMediaExtensionException(InvalidExtensionException):
    """媒体后缀不合法."""


class InvalidVideoExtensionException(InvalidExtensionException):
    """视频后缀不合法."""


# Java: ``InvalidExtensionException.InvalidImageExtensionException`` 等四个内部类
InvalidExtensionException.InvalidImageExtensionException = InvalidImageExtensionException  # type: ignore[attr-defined]
InvalidExtensionException.InvalidFlashExtensionException = InvalidFlashExtensionException  # type: ignore[attr-defined]
InvalidExtensionException.InvalidMediaExtensionException = InvalidMediaExtensionException  # type: ignore[attr-defined]
InvalidExtensionException.InvalidVideoExtensionException = InvalidVideoExtensionException  # type: ignore[attr-defined]


__all__ = [
    "FileException",
    "FileSizeLimitExceededException",
    "FileNameLengthLimitExceededException",
    "FileUploadException",
    "InvalidExtensionException",
    "InvalidImageExtensionException",
    "InvalidFlashExtensionException",
    "InvalidMediaExtensionException",
    "InvalidVideoExtensionException",
]
