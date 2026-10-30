"""``com.ruoyi.framework.interceptor.impl`` 包 —— 拦截规则的具体实现."""

from __future__ import annotations

from app.framework.interceptor.impl.same_url_data_interceptor import (
    REPEAT_PARAMS,
    REPEAT_TIME,
    SameUrlDataInterceptor,
)

__all__ = ["REPEAT_PARAMS", "REPEAT_TIME", "SameUrlDataInterceptor"]
