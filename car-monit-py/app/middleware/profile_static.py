"""``/profile/**`` 静态资源：Windows 跨盘 404 与同源 HTML 加固.

Java 的 ``ResourcesConfig`` 只做 ``file:${ruoyi.profile}/`` → ``/profile/**``；Python
侧用 Starlette ``StaticFiles``。两处差异必须自己补：

1. ``StaticFiles.lookup_path`` 用 ``os.path.commonpath`` 防目录穿越；Windows 上路径
   落在另一个盘符时它会抛 ``ValueError``（``path is on mount 'C:', start on mount
   'D:'``），未捕获就是 500。这里把跨盘等同于"越界"，返回 ``("", None)`` → 404。
2. 上传目录里可能混入 ``.html`` / ``.svg``（Java 的 ``FileUploadUtils`` 默认白名单
   含 html/htm），``/profile/**`` 又是公开静态服务 → 同源存储型 XSS。
   这里在**响应头**上统一加 ``X-Content-Type-Options: nosniff`` 与
   ``Content-Disposition: attachment``：直接导航到文件一律下载、不在同源执行；
   ``<img src>`` 渲染图片不受影响。选择响应头而不是收紧上传后缀，是因为后者会
   改变通用上传的可用性，而前者对现有业务零破坏（差异见 ``COMPATIBILITY.md`` §46.2）。
"""

from __future__ import annotations

import os
from typing import Any, Optional, Tuple

from starlette.staticfiles import StaticFiles


class ProfileStaticFiles(StaticFiles):
    """``/profile`` 挂载点：跨盘按 404 处理，并统一加下载/防嗅探头."""

    async def check_config(self) -> None:
        """跳过 Starlette 的目录存在性检查。

        ``check_dir=False`` 只关掉 ``__init__`` 里的检查；Starlette 在首次请求时
        仍会调用 ``check_config``。Java 的资源处理器在目录缺失时只在请求上返回
        404，不会抛异常，这里保持同样语义。
        """

    def lookup_path(self, path: str) -> Tuple[str, Optional[os.stat_result]]:
        try:
            return super().lookup_path(path)
        except ValueError:
            # Windows 跨盘：``commonpath`` 无法比较不同盘符，按"越界"处理。
            return "", None

    async def get_response(self, path: str, scope: Any) -> Any:
        response = await super().get_response(path, scope)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.setdefault("Content-Disposition", "attachment")
        return response


__all__ = ["ProfileStaticFiles"]
