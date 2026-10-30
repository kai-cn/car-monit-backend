"""cron 表达式工具类.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/CronUtils.java

三个方法都是**薄封装**，没有任何业务判断。真正的解析/计算在
:mod:`app.quartz.util.cron_expression`（Quartz 2.3.2 的逐行移植）。

控制器的调用点
--------------
``SysJobController#add`` / ``#edit`` 只调用 :meth:`CronUtils.is_valid`：表达式不合法时
直接 ``AjaxResult.error("cron表达式不正确")``，**在落库之前**就返回。所以
``POST /monitor/job`` 的 500 文案对非法表达式永远是这一句，而不是 Quartz 的原始报错 ——
见 ``evidence/_probe_job_err_out.txt`` 第 20 行。

``getInvalidMessage`` 在 RuoYi 里**没有任何调用方**（前端也不读），照搬不删。

``getNextExecution`` 的异常转换
-------------------------------
Java 把 ``ParseException`` 包成 ``IllegalArgumentException(e.getMessage())``，
于是最终由 ``@ExceptionHandler(Exception.class)`` 回 ``{"code":500,"msg":"<Quartz 原文>"}``。
Python 侧用 ``ValueError`` 承担 ``IllegalArgumentException`` 的角色，文案保持原样。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.quartz.util.cron_expression import CronExpression, CronParseException

__all__ = ["CronUtils"]


class CronUtils:
    """Java: ``public class CronUtils``（全是 static 方法）."""

    # Java: public static boolean isValid(String cronExpression)
    @staticmethod
    def is_valid(cron_expression: Optional[str]) -> bool:
        """表达式是否合法.

        注意 ``None`` **不会**返回 ``False``：Java 的 ``CronExpression`` 构造器对 null
        抛的是 ``IllegalArgumentException``（不是 ``ParseException``），
        ``isValidExpression`` 不捕获它，于是一路冒到全局处理器，回
        ``{"code":500,"msg":"cronExpression cannot be null"}``。本实现同样让
        ``ValueError`` 穿过。
        """
        return CronExpression.is_valid_expression(cron_expression)

    # Java: public static String getInvalidMessage(String cronExpression)
    @staticmethod
    def get_invalid_message(cron_expression: Optional[str]) -> Optional[str]:
        """非法时返回解析器的报错文案，合法时返回 ``None``.

        Java 只捕获 ``ParseException``；``null`` 输入会让 ``IllegalArgumentException``
        穿透（与 :meth:`is_valid` 同源）。**没有调用方**，照搬。
        """
        try:
            CronExpression(cron_expression)
            return None
        except CronParseException as pe:
            return str(pe)

    # Java: public static Date getNextExecution(String cronExpression)
    @staticmethod
    def get_next_execution(cron_expression: Optional[str]) -> Optional[datetime]:
        """下一次执行时间；表达式耗尽年份（或永不命中）时返回 ``None``."""
        try:
            cron = CronExpression(cron_expression)
            return cron.get_next_valid_time_after(datetime.now())
        except CronParseException as exc:
            # Java: throw new IllegalArgumentException(e.getMessage());
            raise ValueError(str(exc)) from None
