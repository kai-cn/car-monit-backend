"""异步工厂（产生任务用） / asynchronous task factory.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/manager/factory/AsyncFactory.java

Java original
-------------
Static factory methods returning a ``TimerTask`` that is handed to
``AsyncManager.me().execute(...)``. The task runs on the ``schedule-pool`` thread, ~10 ms
later, i.e. **after** the HTTP response has been produced.

The reason for the split -- and the trap it hides
-------------------------------------------------
``recordLogininfor`` reads *two* request-scoped values: the ``User-Agent`` header and the
client IP. Both are read **before** the ``TimerTask`` is created:

    final UserAgent userAgent = UserAgent.parseUserAgentString(ServletUtils.getRequest().getHeader("User-Agent"));
    final String ip = IpUtils.getIpAddr();

They have to be, because on the worker thread ``RequestContextHolder`` is empty and
``ServletUtils.getRequest()`` returns ``null`` -> NPE. ``AddressUtils.getRealAddressByIP(ip)``
(the slow HTTP lookup) is inside ``run()`` for the opposite reason: it must not block the
login response.

The Python port keeps that split exactly: the header and the IP are captured eagerly, the
address lookup and the INSERT happen on the worker thread.

``AsyncManager`` swallows exceptions from the task, so a failing audit insert can never fail a
login. Do not add ``await``-like error handling that would change that.

``recordOper``
--------------
Same shape as ``recordLogininfor``, but it needs nothing from the request: the caller
(``LogAspect``) has already captured the IP and built the entity on the request thread, so
this task only does the slow address lookup plus the INSERT. ``oper_time`` is left to the
database (``sysdate()`` in ``SysOperLogMapper.insertOperlog``), exactly as in Java.

Reached from :func:`app.framework.aspectj.log_aspect.log` -- every ``@Log``-decorated
controller action ends up here.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional, Sequence

from app.common.constant.constants import FAIL, LOGIN_FAIL, LOGIN_SUCCESS, LOGOUT, REGISTER, SUCCESS
from app.common.core.context.request_context import get_request
from app.common.utils.address_utils import get_real_address_by_ip
from app.common.utils.ip_utils import get_ip_addr
from app.common.utils.log_utils import get_block
from app.common.utils.user_agent_utils import browser_name, operating_system_name
from app.system.domain.sys_logininfor import SysLogininfor
from app.system.domain.sys_oper_log import SysOperLog
from app.system.service.sys_logininfor_service import get_logininfor_service
from app.system.service.sys_oper_log_service import get_oper_log_service

#: Java: ``LoggerFactory.getLogger("sys-user")``. ``logback.xml`` routes that name to
#: ``sys-user.log``; ``app.logging_config`` already maps the Java name to this Python logger.
sys_user_logger = logging.getLogger("app.user_access")

#: Header read eagerly, before the task leaves the request thread.
USER_AGENT_HEADER = "User-Agent"

#: Statuses that mean "the attempt succeeded"; everything else falls through to the
#: ``LOGIN_FAIL`` branch and leaves ``SysLogininfor.status`` at ``None`` (see the docstring of
#: :func:`record_logininfor`).
_SUCCESS_STATUSES = (LOGIN_SUCCESS, LOGOUT, REGISTER)


def _slf4j_format(template: str, args: Sequence[Any]) -> str:
    """Java: SLF4J's ``{}`` substitution performed by ``logger.info(msg, args...)``.

    ``sys_user_logger.info(s.toString(), args)`` passes the already-built line as the *format*
    and the caller's varargs as *arguments*, so any ``{}`` pair inside the bracketed fields
    would be substituted. No current call site passes ``args``, but the semantics are
    reproduced so that a future ``recordLogininfor(u, s, "{} 次失败", 3)`` behaves as in Java.

    SLF4J rules kept: ``{}`` consumes one argument in order; ``\\{}`` is an escaped literal;
    surplus arguments are appended in brackets; a surplus *last* argument that is a
    ``Throwable`` becomes the stack trace. Python format strings with ``{0}`` are **not**
    involved -- this is SLF4J, not ``str.format``.
    """
    if not args:
        return template

    remaining = list(args)
    parts = []
    index = 0
    length = len(template)
    while index < length:
        if template.startswith("\\{}", index):
            parts.append("{}")
            index += 3
            continue
        if template.startswith("{}", index) and remaining:
            parts.append(str(remaining.pop(0)))
            index += 2
            continue
        parts.append(template[index])
        index += 1
    text = "".join(parts)

    if remaining:
        # SLF4J: "more arguments than placeholders" -> append them in an array-like tail.
        suffix = " ".join(str(item) for item in remaining)
        text = f"{text} {suffix}"
    return text


def record_logininfor(
    username: Optional[str],
    status: Optional[str],
    message: Optional[str],
    *args: Any,
) -> Callable[[], None]:
    """记录登录信息 -- build the audit task for one login/logout/register event.

    Java: ``AsyncFactory.recordLogininfor(String username, String status, String message,
    Object... args)``.

    Returns a zero-argument callable: ``AsyncManager.me().execute(record_logininfor(...))``.

    Two ``status`` vocabularies meet here and must not be conflated:

    =========================  ==========================================
    ``status`` argument         ``sys_logininfor.status`` written
    =========================  ==========================================
    ``LOGIN_SUCCESS``/``LOGOUT``/``REGISTER``   ``"0"`` (``Constants.SUCCESS``)
    ``LOGIN_FAIL`` (``"Error"``)                ``"1"`` (``Constants.FAIL``)
    anything else                               ``None`` -- neither branch runs
    =========================  ==========================================

    That last row is Java behaviour, not an oversight: ``setStatus`` lives inside the
    ``if``/``else if`` chain, so an unrecognised status leaves the field null.
    """
    request = get_request()
    if request is None:
        # Java: ServletUtils.getRequest() is null -> NPE on getHeader("User-Agent"); the
        # exception escapes the caller because this part runs synchronously.
        raise RuntimeError(
            "AsyncFactory.recordLogininfor requires a bound request "
            "(Java: NullPointerException in ServletUtils.getRequest().getHeader())"
        )

    user_agent_string = request.headers.get(USER_AGENT_HEADER)
    ip = get_ip_addr(request)

    def task() -> None:
        # 远程查询操作地点 -- deliberately inside the task: a slow HTTP lookup must not delay
        # the response. ``get_real_address_by_ip`` already swallows network errors.
        address = get_real_address_by_ip(ip)
        line = (
            get_block(ip)
            + (address or "")
            + get_block(username)
            + get_block(status)
            + get_block(message)
        )
        # 打印信息到日志
        sys_user_logger.info(_slf4j_format(line, args))

        # 获取客户端操作系统 / 浏览器 -- parsed from the eagerly captured header.
        os_name = operating_system_name(user_agent_string)
        browser = browser_name(user_agent_string)

        logininfor = SysLogininfor(
            user_name=username,
            ipaddr=ip,
            login_location=address,
            browser=browser,
            os=os_name,
            msg=message,
            # login_time is intentionally absent: the INSERT uses MySQL's sysdate().
        )
        # 日志状态
        if status in _SUCCESS_STATUSES:
            logininfor.status = SUCCESS
        elif status == LOGIN_FAIL:
            logininfor.status = FAIL

        # 插入数据
        get_logininfor_service().insert_logininfor(logininfor)

    return task


def record_oper(oper_log: SysOperLog) -> Callable[[], None]:
    """操作日志记录（异步任务） -- build the audit task for one controller action.

    Java: ``AsyncFactory.recordOper(final SysOperLog operLog)``::

        return new TimerTask() {
            public void run() {
                // 远程查询操作地点
                operLog.setOperLocation(AddressUtils.getRealAddressByIP(operLog.getOperIp()));
                SpringUtils.getBean(ISysOperLogService.class).insertOperlog(operLog);
            }
        };

    The entity is fully populated by the caller; this task must not depend on the request
    context, because it runs on a ``schedule-pool`` thread after the response was returned
    (``RequestContextHolder`` is empty there -- see the module docstring).
    """
    def task() -> None:
        # 远程查询操作地点
        oper_log.oper_location = get_real_address_by_ip(oper_log.oper_ip or "")
        # 插入数据
        get_oper_log_service().insert_operlog(oper_log)

    return task


__all__ = ["AsyncFactory", "record_logininfor", "record_oper", "sys_user_logger"]


class AsyncFactory:
    """Java: ``class AsyncFactory`` -- a namespace for static factory methods.

    Java groups these under one class; the module-level function above is the direct
    translation, and this class keeps the Java call sites -- ``AsyncFactory.recordLogininfor``
    -- working verbatim. Both names refer to the same function.
    """

    #: Java: ``AsyncFactory.recordLogininfor(...)``
    record_logininfor = staticmethod(record_logininfor)

    #: Java: ``AsyncFactory.recordOper(SysOperLog)``
    record_oper = staticmethod(record_oper)
