"""服务相关配置 / server URL helper.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/ServerConfig.java

Java 里 ``ServerConfig`` 是 ``@Component``，靠 ``ServletUtils.getRequest()`` 从
``RequestContextHolder`` 取当前请求；``CommonController.uploadFile`` 用它拼完整 url。

Python 侧不注入、不取全局请求 —— 直接把 ``Request`` 传进来（``get_url(request)``）。
语义相同，而且测试不需要伪造 ``RequestContextHolder``。
"""

from __future__ import annotations

from fastapi import Request

from app.settings import get_settings


def get_domain(request: Request) -> str:
    """获取完整的请求路径（域名 + 端口 + 上下文路径）. Java: ``ServerConfig.getDomain``.

    Java::

        StringBuffer url = request.getRequestURL();               // http://h:9989/common/upload
        String contextPath = request.getServletContext().getContextPath();
        return url.delete(url.length() - request.getRequestURI().length(), url.length())
                  .append(contextPath).toString();

    也就是"把 URI 部分砍掉，换成 contextPath"。等价于 ``request.base_url`` 去掉末尾那个
    ``/`` 再拼 ``contextPath``：

    * ``context-path: /``   -> ``""``   -> ``http://h:9989``
    * ``context-path: /api`` -> ``"/api"`` -> ``http://h:9989/api``
    """
    #: Starlette 的 ``base_url`` 形如 ``http://testserver/``（**带**尾斜杠）
    base = str(request.base_url)
    if base.endswith("/"):
        base = base[:-1]
    return base + get_settings().context_path


def get_url(request: Request) -> str:
    """获取服务地址. Java: ``ServerConfig#getUrl()``."""
    return get_domain(request)


__all__ = ["get_domain", "get_url"]
