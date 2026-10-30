"""防止重复提交拦截器（``RepeatSubmitInterceptor`` + FastAPI 装配）.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/interceptor/RepeatSubmitInterceptor.java

Java 原文
---------
``@Component`` 的**抽象**拦截器，在 ``ResourcesConfig#addInterceptors`` 里注册到
``/**``：:

    if (handler instanceof HandlerMethod) {
        RepeatSubmit annotation = method.getAnnotation(RepeatSubmit.class);
        if (annotation != null && this.isRepeatSubmit(request, annotation)) {
            AjaxResult ajaxResult = AjaxResult.error(annotation.message());
            ServletUtils.renderString(response, JSON.toJSONString(ajaxResult));
            return false;          // 短路：handler 不会被调用
        }
    }

具体规则由子类 :class:`~app.framework.interceptor.impl.same_url_data_interceptor.SameUrlDataInterceptor`
实现（URL + 请求体 + 令牌，10 秒/注解间隔内视为重复）。

Python 等价物
-------------
FastAPI 没有拦截器链，但路由装饰器支持 ``dependencies``，它在端点函数体之前、**在
``@pre_authorize_permi`` 之前**解析 —— 与 Java 的"拦截器 -> ``@PreAuthorize`` 代理"顺序
一致。因此::

    @router.post("", dependencies=[Depends(repeat_submit())])
    @pre_authorize_permi("system:config:add")
    def add(config: ValidConfig) -> AjaxResult: ...

依赖的解析时点还决定了另外两件事，都与 Java 一致：

1. **先于请求体校验**。``solve_dependencies`` 先跑子依赖、再 ``request_body_to_args``，
   所以被拦下的重复提交不会先撞校验错误（Spring 的 ``preHandle`` 同样在反序列化之前）。
2. **不进审计日志**。``@log`` 是端点上的装饰器，依赖阶段抛异常时它根本没被调用 ——
   Java 的 ``@Log`` 环绕通知同样不会触发。所以重复提交**不会**留下 ``sys_oper_log`` 行。

``renderString`` 在 Java 里把响应体直接写出去，没有异常参与；这里用
:class:`RepeatSubmitException` 短路依赖，再由 ``GlobalExceptionHandler`` 的等价物
（:func:`app.config.exception_handlers.register_exception_handlers`）渲染成**同一份**
``{"code":500,"msg":"<annotation.message>"}`` + HTTP 200。
"""

from __future__ import annotations

import logging
import time
from typing import Awaitable, Callable, Optional

from starlette.requests import Request

from app.common.annotation.repeat_submit import RepeatSubmit

logger = logging.getLogger("app.framework.interceptor.repeat_submit_interceptor")


class RepeatSubmitException(RuntimeError):
    """重复提交被拦截（Python 侧新增，Java 直接写响应体）.

    继承 ``RuntimeError`` 与其它业务异常保持一致，但**单独注册处理器**，因为它的响应体
    是注解里的 ``message``，而不是 ``str(exception)``（两者恰好相同，但语义不同）。
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class RepeatSubmitInterceptor:
    """Java: ``abstract class RepeatSubmitInterceptor implements HandlerInterceptor``."""

    async def is_repeat_submit(self, request: Request, annotation: RepeatSubmit) -> bool:
        """Java: ``public abstract boolean isRepeatSubmit(HttpServletRequest, RepeatSubmit)``."""
        raise NotImplementedError


#: 进程内单例的规则实现，等价于 Spring 里 ``@Component`` 的 ``SameUrlDataInterceptor``
#: （单例 bean，由 ``ResourcesConfig`` 注入拦截器）。放在模块级而不是每次 ``repeat_submit()``
#: 新建，是为了让"只读写同一个 Redis key 空间"这件事在 Python 侧也成立。
_default_interceptor: Optional[RepeatSubmitInterceptor] = None


def get_interceptor() -> RepeatSubmitInterceptor:
    """取（并在首次调用时构造）单例实现。Java: Spring 注入 ``RepeatSubmitInterceptor``."""
    global _default_interceptor
    if _default_interceptor is None:
        # 延迟导入：``impl`` 子模块反过来要依赖本模块的抽象类。
        from app.framework.interceptor.impl.same_url_data_interceptor import SameUrlDataInterceptor

        _default_interceptor = SameUrlDataInterceptor()
    return _default_interceptor


def reset_interceptor() -> None:
    """丢弃单例（仅测试用；等价于重建 Spring 容器）."""
    global _default_interceptor
    _default_interceptor = None


def repeat_submit(
    annotation: Optional[RepeatSubmit] = None,
    *,
    interceptor: Optional[RepeatSubmitInterceptor] = None,
) -> Callable[[Request], Awaitable[None]]:
    """构造一个可直接放进 ``dependencies=[...]`` 的守卫.

    参数与 ``@RepeatSubmit`` 的两个属性一一对应（``interval`` / ``message``）；
    ``interceptor`` 只在测试里替换成假实现。

    具体实现在**请求时**才取（:func:`get_interceptor`）：单例在首次请求时才需要连
    Redis，避免导入期就建连接（Spring 是懒加载 bean，行为一致）。
    """
    rule = annotation or RepeatSubmit()

    async def guard(request: Request) -> None:
        # Java: if (annotation != null && this.isRepeatSubmit(request, annotation)) { ... return false; }
        active = interceptor or get_interceptor()
        if await active.is_repeat_submit(request, rule):
            raise RepeatSubmitException(rule.message)

    return guard


def _now_millis() -> int:
    """Java: ``System.currentTimeMillis()``."""
    return int(time.time() * 1000)


__all__ = [
    "RepeatSubmitException",
    "RepeatSubmitInterceptor",
    "get_interceptor",
    "repeat_submit",
    "reset_interceptor",
]
