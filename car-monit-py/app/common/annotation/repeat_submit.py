"""``@RepeatSubmit`` 注解的 Python 等价物（frozen dataclass）.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/annotation/RepeatSubmit.java

Java 原文
---------
::

    @Inherited @Target(METHOD) @Retention(RUNTIME) @Documented
    public @interface RepeatSubmit {
        int interval() default 5000;                       // 间隔(ms)，小于此时间视为重复提交
        String message() default "不允许重复提交，请稍候再试";
    }

Python 等价物
-------------
Python 没有方法级注解，改成一个数据类，由 :mod:`app.framework.interceptor` 里的拦截器
消费 —— 用法是把它交给路由的 ``dependencies``::

    @router.post("", dependencies=[Depends(repeat_submit(RepeatSubmit()))])

整个 Java 工程只有 ``SysConfigController#add`` 一处用到它。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepeatSubmit:
    """防重复提交注解. Java: ``@RepeatSubmit``."""

    #: 间隔时间(ms)，小于此时间视为重复提交
    interval: int = 5000
    #: 提示消息
    message: str = "不允许重复提交，请稍候再试"


__all__ = ["RepeatSubmit"]
