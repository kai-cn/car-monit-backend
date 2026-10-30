"""Forest 声明式 HTTP 客户端：下载远端文件.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/service/forest/FileApi.java

Java 侧是 Forest 的注解接口：

.. code-block:: java

    @GetRequest(url = "{URL}")
    byte[] downloadImageToByteArray(@Var("URL") String URL);

    @GetRequest(url = "{URL}")
    InputStream downloadImageToInputStream(@Var("URL") String URL);

Forest 在运行时生成代理。Python 侧没有注解，直接用 ``httpx`` 发出同样的 GET。差异与
对齐点逐条列在下面。

对齐点
------
* **跟随重定向**：Forest 默认跟随，``httpx`` 默认**不**跟随，所以显式
  ``follow_redirects=True``；
* **超时**：取 ``forest.timeout`` / ``forest.connect-timeout``（yml 里都是 60000ms）。
  Forest 的 ``timeout`` 是"读超时"，``httpx.Timeout`` 把两者分开传；
* **重试**：``forest.retry-count: 2`` + ``BackOffRetryer`` + ``max-retry-interval: 1000``
  => 首发 + 最多 2 次重试，退避上限 1s。这里用同一个循环实现；
* **失败形态**：Forest 抛 ``ForestRuntimeException``（``RuntimeException``）。Python 抛
  ``RuntimeError``，两者都落到通用处理器；而且唯一的调用点
  （``SysFileServiceImpl.uploadByUrl``）自己 ``catch (Exception e) { log.error(...) }``
  **吞掉**异常、跳过这一条，所以客户端永远看不到这个错误。

``downloadImageToInputStream`` 没有调用者
----------------------------------------
本项目的 ``uploadByUrl`` 只用 ``byte[]`` 那一个。按迁移原则第 4 条照留，返回
``BytesIO``（Java 返回 ``InputStream``）。
"""

from __future__ import annotations

import logging
import time
from io import BytesIO
from typing import BinaryIO, Optional

import httpx

from app.settings import get_settings

logger = logging.getLogger("app.system.service.forest.file_api")

#: Forest 的 ``@GetRequest`` 默认方法。
_HTTP_METHOD = "GET"


class FileApi:
    """Java: ``interface FileApi``（Forest 运行时生成的代理的等价物）。"""

    def __init__(self, timeout_ms: Optional[int] = None, connect_timeout_ms: Optional[int] = None) -> None:
        forest = get_settings().forest
        self.timeout_ms = forest.timeout if timeout_ms is None else timeout_ms
        self.connect_timeout_ms = (
            forest.connect_timeout if connect_timeout_ms is None else connect_timeout_ms
        )
        self.retry_count = forest.retry_count
        self.max_retry_interval = forest.max_retry_interval

    # Java: byte[] downloadImageToByteArray(@Var("URL") String URL)
    def download_image_to_byte_array(self, url: str) -> bytes:
        return self._download(url, "byte array")

    # Java: InputStream downloadImageToInputStream(@Var("URL") String URL)
    def download_image_to_input_stream(self, url: str) -> BinaryIO:
        return BytesIO(self._download(url, "input stream"))

    # ------------------------------------------------------------------ 内部

    def _download(self, url: str, kind: str) -> bytes:
        last_error: Optional[BaseException] = None
        # Forest: retry-count = 2 -> 共 3 次（首次 + 2 次重试）
        for attempt in range(self.retry_count + 1):
            try:
                with httpx.Client(
                    timeout=httpx.Timeout(
                        self.timeout_ms / 1000.0, connect=self.connect_timeout_ms / 1000.0
                    ),
                    follow_redirects=True,
                ) as client:
                    response = client.request(_HTTP_METHOD, url)
                    # Forest 的默认反序列化对本项目的 byte[] 不做状态码判断（
                    # ``ResponseProcessor`` 直接把 body 交出去）；这里同样只取 body，
                    # 不因 4xx/5xx 抛错 —— 下载到一张 404 页面时后端行为与 Java 一致
                    # （把页面当图片存进 OSS）。
                    return response.content
            except Exception as exc:  # noqa: BLE001 - Forest 会重试所有传输层异常
                last_error = exc
                logger.warning(
                    "[文件下载失败] %s (第 %s/%s 次) url=%s error=%s",
                    kind,
                    attempt + 1,
                    self.retry_count + 1,
                    url,
                    exc,
                )
                if attempt < self.retry_count:
                    time.sleep(self._backoff(attempt))

        raise RuntimeError(f"文件下载失败: {url}") from last_error

    def _backoff(self, attempt: int) -> float:
        """``BackOffRetryer`` 的退避：指数增长，封顶 ``max-retry-interval``（毫秒）。"""
        delay_ms = min(self.max_retry_interval, 1000 * (2**attempt))
        return delay_ms / 1000.0


#: Java: ``@Resource private FileApi fileApi`` —— Spring 单例。
_FILE_API: Optional[FileApi] = None


def get_file_api() -> FileApi:
    global _FILE_API
    if _FILE_API is None:
        _FILE_API = FileApi()
    return _FILE_API


def reset_file_api() -> None:
    """Test helper: 丢掉单例。"""
    global _FILE_API
    _FILE_API = None


__all__ = ["FileApi", "get_file_api", "reset_file_api"]
