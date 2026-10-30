"""Home page controller.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/system/SysIndexController.java

Java original
-------------
``@RestController`` + ``@RequestMapping("/")`` returning a plain ``String``. Because
``@RequestMapping`` declares no method, **every** HTTP verb is accepted -- that is
reproduced here with ``api_route``. Spring Security permits ``GET /`` anonymously
(``antMatchers(HttpMethod.GET, "/")``); other verbs on ``/`` fall through to
``anyRequest().authenticated()``.

The response is ``text/plain``, not JSON: ``String`` return values bypass ``AjaxResult``.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.settings import get_settings

router = APIRouter(tags=["system-index"])


@router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"], response_class=PlainTextResponse)
def index() -> str:
    """Java: ``SysIndexController#index()``.

    ``StringUtils.format("欢迎使用{}后台管理框架，请通过前端地址访问。", ruoyiConfig.getName())``
    """
    name = get_settings().ruoyi.name
    return f"欢迎使用{name}后台管理框架，请通过前端地址访问。"
