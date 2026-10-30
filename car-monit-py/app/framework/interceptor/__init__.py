"""``com.ruoyi.framework.interceptor`` 包 —— 处理器拦截器（Python 侧以路由依赖实现）.

已迁移：

* ``RepeatSubmitInterceptor`` -> :mod:`app.framework.interceptor.repeat_submit_interceptor`
  （抽象基类 + ``repeat_submit()`` 依赖工厂；用 ``dependencies=[...]`` 挂在路由上）
* ``impl.SameUrlDataInterceptor`` -> :mod:`app.framework.interceptor.impl.same_url_data_interceptor`

Java 用 ``ResourcesConfig#addInterceptors`` 把拦截器注册到 ``/**``，再由
``method.getAnnotation(RepeatSubmit.class)`` 决定是否生效；FastAPI 没有这一层，改成
"哪个路由带 ``@RepeatSubmit`` 就给哪个路由加依赖"，可观察行为相同。
"""

from __future__ import annotations

from app.framework.interceptor.repeat_submit_interceptor import (
    RepeatSubmitException,
    RepeatSubmitInterceptor,
    get_interceptor,
    repeat_submit,
    reset_interceptor,
)

__all__ = [
    "RepeatSubmitException",
    "RepeatSubmitInterceptor",
    "get_interceptor",
    "repeat_submit",
    "reset_interceptor",
]
