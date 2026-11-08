"""``/profile/**`` 静态资源：同源 HTML 加固.

Java 的 ``ResourcesConfig`` 只做 ``file:${ruoyi.profile}/`` → ``/profile/**``；Python
侧用 Starlette ``StaticFiles``。上传目录里可能混入 ``.html`` / ``.svg``（Java 的
``FileUploadUtils`` 默认白名单含 html/htm），``/profile/**`` 又是公开静态服务 →
同源存储型 XSS。

这里在**响应头**上统一加 ``X-Content-Type-Options: nosniff`` 与
``Content-Disposition: attachment``：直接导航到文件一律下载、不在同源执行；
``<img src>`` 渲染图片不受影响。选择响应头而不是收紧上传后缀，是因为后者会
改变通用上传的可用性，而前者对现有业务零破坏（差异见 ``COMPATIBILITY.md`` §46.2）。
"""

from __future__ import annotations

from typing import Any

from starlette.staticfiles import StaticFiles


class ProfileStaticFiles(StaticFiles):
    """``/profile`` 挂载点：统一加下载/防嗅探头."""

    async def get_response(self, path: str, scope: Any) -> Any:
        response = await super().get_response(path, scope)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.setdefault("Content-Disposition", "attachment")
        return response


__all__ = ["ProfileStaticFiles"]
