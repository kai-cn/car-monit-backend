"""计划策略异常.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/exception/job/TaskException.java

Java 是受检异常 ``extends Exception``（``new TaskException(msg, Code.CONFIG_ERROR)``），
由 ``ScheduleUtils.handleCronScheduleMisfirePolicy`` 在 ``misfirePolicy`` 不认识的
时候抛出。它**不是** ``CustomException``，所以 ``GlobalExceptionHandler`` 里
没有专门的处理器 —— 落在 ``@ExceptionHandler(Exception.class)``，照样是
HTTP 200 + ``code 500`` + ``msg`` = 异常消息。

``code`` 目前**没有**任何读取方（Java 侧也没有，只有 ``getCode()`` 的定义）。
照留，别删。
"""

from __future__ import annotations

from enum import Enum


class TaskException(Exception):
    """Java: ``public class TaskException extends Exception``."""

    class Code(Enum):
        """Java: ``public enum Code { TASK_EXISTS, NO_TASK_EXISTS, ... }``."""

        TASK_EXISTS = "TASK_EXISTS"
        NO_TASK_EXISTS = "NO_TASK_EXISTS"
        TASK_ALREADY_STARTED = "TASK_ALREADY_STARTED"
        UNKNOWN = "UNKNOWN"
        CONFIG_ERROR = "CONFIG_ERROR"
        TASK_NODE_NOT_AVAILABLE = "TASK_NODE_NOT_AVAILABLE"

    def __init__(
        self,
        message: str,
        code: "TaskException.Code",
        nested: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self._code = code
        self._nested = nested

    @property
    def code(self) -> "TaskException.Code":
        """Java: ``public Code getCode()``."""
        return self._code

    @property
    def nested(self) -> BaseException | None:
        """Java: ``getCause()`` —— 构造函数第三个参数."""
        return self._nested


__all__ = ["TaskException"]
