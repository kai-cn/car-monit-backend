"""操作日志记录处理（``@Log`` 切面的等价实现）.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/aspectj/LogAspect.java

Java 是怎么做的
---------------
三个通知方法挂同一个切点 ``@annotation(controllerLog)``::

    @Before           boBefore         -> TIME_THREADLOCAL.set(System.currentTimeMillis())
    @AfterReturning   doAfterReturning -> handleLog(joinPoint, log, null, jsonResult)
    @AfterThrowing    doAfterThrowing  -> handleLog(joinPoint, log, e, null)

``handleLog`` 组一个 ``SysOperLog``，然后交给
``AsyncManager.me().execute(AsyncFactory.recordOper(operLog))`` 异步落库 —— 审计写入
**永远不会**影响业务响应（整个方法体包在 ``try/catch`` 里）。

Python 是怎么做的
-----------------
没有 AOP，改成装饰器 :func:`log`，**放在最里面**（紧贴 ``def``）::

    @router.post("", response_model=None)
    @pre_authorize_permi("system:post:add")
    @log(title="岗位管理", business_type=BusinessType.INSERT, java_method="add")
    def add(post: ValidPost) -> AjaxResult:
        ...

一层层剥洋葱的调用顺序与 Spring 的 advisor 顺序一致：
``@PreAuthorize``（order 200）在 ``LogAspect``（``LOWEST_PRECEDENCE``）外面，所以
**被权限拒绝的请求不会留下审计记录**。反过来放（``@log`` 在最外层）就会给 403 也记一笔。

``functools.wraps`` 保留了 ``__wrapped__``，FastAPI 用 ``inspect.signature`` 取签名时
会自动跟上，所以路由注册、依赖解析（``Depends``/``Body``）看到的仍是被装饰函数的签名。
但仅有 ``wraps`` 还不够 —— 字符串注解会在``本模块``的命名空间里求值，必须由
:func:`_materialize_signature` 把签名实体化，详见踩坑记录第 7 条。

落库内容与 Java 逐字段对齐
--------------------------
.. list-table::
   :header-rows: 1

   * - ``sys_oper_log`` 列
     - 取值
   * - ``title`` / ``business_type`` / ``operator_type``
     - 注解字段，后两者写 ``ordinal()``
   * - ``method``
     - Java 控制器**全类名** + 方法名 + ``()``
   * - ``request_method``
     - ``request.method``
   * - ``oper_url``
     - 请求 URI（不含 query），截断 255
   * - ``oper_ip`` / ``oper_location``
     - ``get_ip_addr`` / 异步里的 ``get_real_address_by_ip``
   * - ``oper_name`` / ``dept_name``
     - 登录用户的名字与部门名
   * - ``oper_param``
     - 见下面"请求参数从哪来"
   * - ``json_result``
     - 返回值 JSON，截断 2000
   * - ``status``
     - ``SUCCESS(0)``；只有**抛异常**才是 ``FAIL(1)``
   * - ``error_msg``
     - 异常消息，截断 2000
   * - ``oper_time``
     - 由 INSERT 的 ``sysdate()`` 生成（mapper 里已如此）

请求参数从哪来
--------------
Java 的判据是 ``ServletUtils.getParamMap(request)`` —— 也就是
``request.getParameterMap()``：**query string + 表单字段**，**不含 JSON body**。
于是::

    paramsMap 为空 且 方法是 PUT/POST  -> 序列化 joinPoint.getArgs()
    否则                              -> 序列化 paramsMap

翻译到 Python：``query_params`` 照读；表单字段读 Starlette 已解析好的 ``request._form``
（FastAPI 处理 ``Form``/``UploadFile`` 时必定已经解析过，读缓存不阻塞）。JSON body
照 Java 走"序列化入参"分支 —— 此时入参已经是 pydantic 实体，``model_dump(by_alias=True)``
出来的正是 Java 实体字段名。

踩坑记录（全部来自 Java 原逻辑或实测，不要"修好"）
-------------------------------------------------
1. **``return AjaxResult.error(...)`` 记的是 SUCCESS**。``@AfterReturning`` 拿到了返回值，
   方法没有抛异常，所以 ``status = 0``、``error_msg = null``，错误信息只出现在
   ``json_result`` 里。已用真实请求在 Java 侧核对过（新增重名岗位 -> ``{"code":500}``，
   而日志行 ``status=0``、``errorMsg=null``）。
2. **未登录时一行都不写**。``SecurityUtils.getLoginUser()`` 在没有 principal 时抛
   ``AuthenticationCredentialsNotFoundException``，被 ``handleLog`` 的 ``catch`` 吞掉，
   直接跳到 ``finally``。Python 同样在 ``try`` 里调会抛异常的
   :func:`~app.common.utils.security_utils.get_login_user`。
3. **``oper_param`` 里的 null 是省略的**。fastjson2 默认不开 ``WriteMapNullValue``，
   实测 ``SysPost`` 的 ``remark``（null）根本不出现；``params``（空 map）反而出现。
   所以这里"去掉值为 null 的成员"，但**不**去掉空容器。
4. **``oper_param`` 的键顺序是 fastjson2 的字段顺序**（实测为字母序，见
   ``_json_for_args``），``json_result`` 则是 ``AjaxResult``（``HashMap``）的哈希顺序。
   本工程按 Python 的声明顺序输出 —— 内容一致、顺序不同，见 ``COMPATIBILITY.md`` §41.10。
5. **``MultipartFile`` 参数会被扔掉**，数组/集合/Map 只看**第一个**元素（Java 循环里
   直接 ``return``，不是 ``any()``）。
6. ``TIME_THREADLOCAL`` 只写不读 —— ``operLog.setCostTime(...)`` 在 Java 里是注释掉的，
   照搬。
7. **``functools.wraps`` 对 FastAPI 不是完全透明的**。它只复制 ``__annotations__``
   （本项目开了 ``from __future__ import annotations``，全是字符串），而 FastAPI 用
   ``wrapper.__globals__`` 去 eval 这些字符串 —— 那是**本模块**的命名空间。本模块恰好也
   导入了 ``UploadFile``，于是 ``file: UploadFile = File(...)`` 求值"成功"但绕过
   ``params.File(...)`` 分支，直接抛 ``Invalid args for response field``。解法见
   :func:`_materialize_signature`：装饰时就把注解求值好挂到 ``wrapper.__signature__``。
8. **``oper_param`` 不吃 Jackson 的 ``@JsonInclude(NON_EMPTY)``**。Java 审计用的是
   fastjson2 的 ``JSON.toJSONString``，``params`` 为空时照样写 ``"params":{}``；
   而本工程 ``model_dump`` 是按 Jackson 语义实现了 NON_EMPTY 的。:func:`_fastjson_plain`
   专门把被吃掉的那几个字段补回来 —— 别把它"简化"成 ``to_jsonable``。
"""

from __future__ import annotations

import functools
import inspect
import json
import logging
import sys
import time
import typing
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette.responses import Response

from app.common.annotation.log import Log
from app.common.core.context.request_context import get_request
from app.common.enums.business_status import BusinessStatus
from app.common.enums.business_type import BusinessType
from app.common.enums.http_method import HttpMethod
from app.common.enums.operator_type import OperatorType
from app.common.utils.ip_utils import get_ip_addr
from app.common.utils.json_utils import to_jsonable
from app.common.utils.security_utils import get_login_user
from app.common.utils.string_utils import is_empty, substring
from app.framework.manager.async_manager import AsyncManager
from app.framework.manager.factory.async_factory import record_oper
from app.system.domain.sys_oper_log import SysOperLog

logger = logging.getLogger("app.framework.aspectj.log_aspect")

#: 排除敏感属性字段. Java: ``public static final String[] EXCLUDE_PROPERTIES``
EXCLUDE_PROPERTIES: Tuple[str, ...] = ("password", "oldPassword", "newPassword", "confirmPassword")

#: Java: ``NamedThreadLocal<Long> TIME_THREADLOCAL`` —— 只写不读，见模块 docstring 第 6 条。
_TIME_CONTEXT: ContextVar[Optional[int]] = ContextVar("log_cost_time", default=None)

#: ``oper_url`` / ``oper_param`` / ``json_result`` / ``error_msg`` 的截断长度。
#: 前三个和其他两处 Java 用的是同一个 ``StringUtils.substring(x, 0, n)``。
URL_MAX = 255
CONTENT_MAX = 2000

#: ``sys_oper_log.method`` 需要 Java 控制器全类名；各控制器模块用这个常量声明。
JAVA_CONTROLLER_ATTRIBUTE = "JAVA_CONTROLLER"


def log(
    *,
    title: str = "",
    business_type: BusinessType = BusinessType.OTHER,
    operator_type: OperatorType = OperatorType.MANAGE,
    is_save_request_data: bool = True,
    is_save_response_data: bool = True,
    exclude_param_names: Sequence[str] = (),
    java_method: str = "",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Java: ``@Log(title = ..., businessType = ...)`` —— 装饰器等价的注解.

    参数名用 snake_case，与 Java 的注解属性一一对应（``businessType`` ->
    ``business_type``）。``java_method`` 是本工程新增的，见 :mod:`app.common.annotation.log`。

    被装饰函数所在模块**必须**声明 ``JAVA_CONTROLLER``（Java 控制器全类名）。缺了会在
    导入期直接报错而不是悄悄记一行错误的 ``method`` —— 审计数据的价值全在可追溯。
    """
    excludes = tuple(exclude_param_names)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        controller = _resolve_java_controller(func)
        controller_log = Log(
            title=title,
            business_type=business_type,
            operator_type=operator_type,
            is_save_request_data=is_save_request_data,
            is_save_response_data=is_save_response_data,
            exclude_param_names=excludes,
            java_method=java_method or func.__name__,
        )
        # Java: className + "." + methodName + "()"
        method_name = f"{controller}.{controller_log.java_method}()"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Java: @Before -> TIME_THREADLOCAL.set(System.currentTimeMillis())
            # 只写不读（setCostTime 在 Java 里被注释掉了），保留是为了结构一致。
            _TIME_CONTEXT.set(int(time.time() * 1000))
            try:
                try:
                    result = func(*args, **kwargs)
                except Exception as error:  # Java: @AfterThrowing
                    _handle_log(controller_log, method_name, error, None, func, args, kwargs)
                    raise
                # Java: @AfterReturning
                _handle_log(controller_log, method_name, None, result, func, args, kwargs)
                return result
            finally:
                _TIME_CONTEXT.set(None)

        _materialize_signature(wrapper, func)
        return wrapper

    return decorator


def _materialize_signature(wrapper: Callable[..., Any], func: Callable[..., Any]) -> None:
    """把被装饰函数的签名（含已求值的注解）挂到 ``wrapper.__signature__`` 上.

    为什么需要这一手 —— ``functools.wraps`` 只复制 ``__annotations__``（可能是**字符串**），
    而 FastAPI 的 ``get_typed_signature`` 是拿 ``getattr(call, "__globals__", {})`` 去 eval
    这些字符串的：``call`` 是 ``wrapper``，它的 ``__globals__`` 是**本模块**的全局命名空间，
    不是控制器模块的。控制器里写了 ``from __future__ import annotations``，注解全是字符串，
    于是 ``file: UploadFile = File(...)`` 里的 ``UploadFile`` 会在本模块求值 —— 本模块恰好
    也 ``from starlette.datastructures import UploadFile``，求值"成功"但拿到的是裸类型，
    ``analyze_param`` 认为它已经有 ``FieldInfo``（默认值 ``File(...)``），跳过
    ``params.File(...)`` 分支，直接进 ``create_model_field`` 并抛
    ``FastAPIError: Invalid args for response field``。

    这里在**装饰时**就用 ``get_type_hints`` 在被装饰函数自己的命名空间里把注解求值成真实
    对象，再以 ``__signature__`` 显式交给 FastAPI，字符串求值这一步就不会发生。
    ``include_extras=True`` 不能省：否则 ``Annotated[X, Depends(...)]`` 会被拆掉，
    各控制器的 ``ValidXxx`` 依赖会**静默消失**。

    解析失败（例如注解引用了只在 TYPE_CHECKING 下导入的名字）就退回原始签名 ——
    与不加这一手时的行为一致，不会让本可用的控制器起不来。
    """
    try:
        hints = typing.get_type_hints(func, include_extras=True)
    except Exception:  # noqa: BLE001 - 求值失败即放弃改写，保持原本的宽松行为
        return
    try:
        signature = inspect.signature(func)
    except (TypeError, ValueError):
        return
    parameters = [
        parameter.replace(annotation=hints.get(parameter.name, parameter.annotation))
        for parameter in signature.parameters.values()
    ]
    wrapper.__signature__ = signature.replace(  # type: ignore[attr-defined]
        parameters=parameters,
        return_annotation=hints.get("return", signature.return_annotation),
    )


def _handle_log(
    controller_log: Log,
    method_name: str,
    error: Optional[Exception],
    json_result: Any,
    func: Callable[..., Any],
    call_args: Tuple[Any, ...],
    call_kwargs: Dict[str, Any],
) -> None:
    """Java: ``LogAspect#handleLog(JoinPoint, Log, Exception, Object)``.

    整个方法体包在 ``try/except`` 里：审计失败只记本地日志，绝不冒泡到业务
    （Java 里是 ``log.error("异常信息:{}", exp.getMessage()); exp.printStackTrace();``）。
    """
    try:
        # 获取当前的用户 —— 未登录会在这里抛异常，整行日志都不写（见模块 docstring 第 2 条）
        login_user = get_login_user()
        request = get_request()

        oper_log = SysOperLog()
        oper_log.status = BusinessStatus.SUCCESS.ordinal()
        oper_log.oper_ip = get_ip_addr(request)
        oper_log.oper_url = substring(_request_uri(request), 0, URL_MAX)
        if login_user is not None:
            oper_log.oper_name = login_user.username
            current_user = login_user.user
            if current_user is not None and current_user.dept is not None:
                oper_log.dept_name = current_user.dept.dept_name

        if error is not None:
            oper_log.status = BusinessStatus.FAIL.ordinal()
            oper_log.error_msg = substring(str(error), 0, CONTENT_MAX)

        oper_log.method = method_name
        oper_log.request_method = request.method
        _get_controller_method_description(
            controller_log, oper_log, json_result, request,
            _ordered_arguments(func, call_args, call_kwargs),
        )
        # 设置消耗时间 -- Java 里是注释掉的，照搬
        # oper_log.cost_time = int(time.time() * 1000) - _TIME_CONTEXT.get()
        AsyncManager.me().execute(record_oper(oper_log))
    except Exception as exp:  # noqa: BLE001 - 审计写入失败不能影响业务
        logger.error("异常信息:%s", exp)
        logger.exception("操作日志记录失败")


def _get_controller_method_description(
    controller_log: Log,
    oper_log: SysOperLog,
    json_result: Any,
    request: Request,
    ordered_args: List[Any],
) -> None:
    """Java: ``getControllerMethodDescription(JoinPoint, Log, SysOperLog, Object)``."""
    oper_log.business_type = controller_log.business_type.ordinal()
    oper_log.title = controller_log.title
    oper_log.operator_type = controller_log.operator_type.ordinal()
    if controller_log.is_save_request_data:
        _set_request_value(controller_log, oper_log, request, ordered_args)
    # Java: StringUtils.isNotNull(jsonResult)
    if controller_log.is_save_response_data and json_result is not None:
        oper_log.json_result = substring(_json_for_result(json_result), 0, CONTENT_MAX)


def _set_request_value(
    controller_log: Log,
    oper_log: SysOperLog,
    request: Request,
    ordered_args: List[Any],
) -> None:
    """Java: ``setRequestValue(JoinPoint, SysOperLog, String[])``."""
    params_map = _param_map(request)
    request_method = oper_log.request_method
    if is_empty(params_map) and (
        HttpMethod.PUT.name == request_method or HttpMethod.POST.name == request_method
    ):
        params = _args_array_to_string(ordered_args, controller_log.exclude_param_names)
        oper_log.oper_param = substring(params, 0, CONTENT_MAX)
    else:
        oper_log.oper_param = substring(
            _json_for_params(params_map, controller_log.exclude_param_names), 0, CONTENT_MAX
        )


def _args_array_to_string(
    params_array: Sequence[Any], exclude_param_names: Tuple[str, ...]
) -> str:
    """Java: ``argsArrayToString(Object[], String[])`` —— 每个非过滤参数序列化后以空格拼接.

    单个对象序列化失败时 Java 静默跳过（``catch (Exception e) {}``），照搬。
    """
    params = ""
    for item in params_array:
        if item is not None and not _is_filter_object(item):
            try:
                params += _json_for_args(item, exclude_param_names) + " "
            except Exception:  # noqa: BLE001 - Java swallows this too
                logger.debug("参数序列化失败: %r", type(item))
    return params.strip()


def _is_filter_object(item: Any) -> bool:
    """Java: ``isFilterObject(Object)``.

    Java 的数组/集合/Map 分支在循环体第一轮就 ``return``，所以只看**第一个**元素 ——
    这不是笔误，照搬。
    """
    if isinstance(item, (list, tuple, set, frozenset)):
        for value in item:
            return isinstance(value, UploadFile)
        return False
    if isinstance(item, dict):
        for value in item.values():
            return isinstance(value, UploadFile)
        return False
    return isinstance(item, (UploadFile, Request, Response))


def _param_map(request: Request) -> Dict[str, str]:
    """Java: ``ServletUtils.getParamMap(ServletRequest)`` -> ``Map<String, String>``.

    同名多值用逗号拼接（Java 是 ``StringUtils.join(values, ",")``）。文件字段在 Java
    里是原始文件名，这里映射 ``UploadFile.filename``。
    """
    collected: Dict[str, List[Any]] = {}
    for key, value in request.query_params.multi_items():
        collected.setdefault(key, []).append(value)
    form = getattr(request, "_form", None)  # Starlette 解析后的缓存；未解析则为 None
    if form is not None and not isinstance(form, dict):
        for key, value in form.multi_items():
            collected.setdefault(key, []).append(value)
    return {key: ",".join(_param_text(value) for value in values) for key, values in collected.items()}


def _param_text(value: Any) -> str:
    """Java: ``getParameter()`` 对文件字段返回原始文件名."""
    if isinstance(value, UploadFile):
        return value.filename or ""
    return value if isinstance(value, str) else str(value)


def _request_uri(request: Request) -> str:
    """Java: ``HttpServletRequest.getRequestURI()`` —— 不含 query，百分号编码保持原样.

    ASGI 的 ``raw_path`` 就是请求行里那段原始字节，语义与 ``getRequestURI()`` 一致；
    测试里若没有 ``raw_path``（手工构造的 scope）则退回 ``url.path``。
    """
    raw_path = request.scope.get("raw_path")
    if raw_path:
        return raw_path.decode("latin-1")
    return request.url.path


def _json_for_args(value: Any, exclude_param_names: Tuple[str, ...]) -> str:
    """序列化一个方法入参. Java: ``JSON.toJSONString(o, excludePropertyPreFilter(names))``.

    ``sort_keys=True``：fastjson2 在装了 ``PropertyPreFilter`` 时按**名字字母序**输出实体
    字段（实测 ``SysPost`` -> ``createBy, flag, params, postCode, postId, postName,
    postSort, status``）。Python 的 ``model_dump`` 是声明顺序，所以这里显式排序才能让
    ``oper_param`` 与 Java 逐字节相同。
    """
    return _dumps(value, exclude_param_names, sort_keys=True)


def _json_for_params(params_map: Dict[str, str], exclude_param_names: Tuple[str, ...]) -> str:
    """序列化参数表. Java: ``JSON.toJSONString(paramsMap, excludePropertyPreFilter(names))``.

    **不排序**：Java 侧是 ``HashMap`` 的哈希顺序，没有可复现的规律，保持请求里的先后顺序
    更有信息量（见 ``COMPATIBILITY.md`` §41.10）。
    """
    return _dumps(params_map, exclude_param_names, sort_keys=False)


def _json_for_result(json_result: Any) -> str:
    """序列化返回值. Java: ``JSON.toJSONString(Object)``.

    ``AjaxResult`` 在 Java 里是 ``HashMap``（``msg`` 先于 ``code`` 出现是哈希顺序使然），
    Python 的 ``dict`` 保持插入顺序，因此这一步不做排序 —— 排序只会让两边更不像。
    """
    return _dumps(json_result, (), sort_keys=False)


def _dumps(value: Any, exclude_param_names: Tuple[str, ...], sort_keys: bool) -> str:
    """fastjson2 的默认输出：紧凑分隔符、不转义非 ASCII、**省略 null 成员**."""
    excluded = set(EXCLUDE_PROPERTIES) | set(exclude_param_names)
    return json.dumps(
        _prune(_fastjson_plain(value), excluded),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=sort_keys,
    )


def _fastjson_plain(value: Any) -> Any:
    """按 **fastjson2** 的口径把领域对象摊平成 JSON-ready 结构.

    Java 的审计日志走 ``JSON.toJSONString(...)``（fastjson2），它**不认** Jackson 注解：
    ``BaseEntity.params`` 上的 ``@JsonInclude(NON_EMPTY)`` 只作用于 MVC 的响应体，
    ``oper_param`` 里 ``"params":{}`` 是照写的（已用真实 Java 请求核对）。

    本工程的 :class:`~app.common.core.domain.domain_model.DomainModel` 用
    ``model_serializer`` 实现了 NON_EMPTY，``model_dump`` 因此会吃掉空 ``params`` ——
    这里按 ``_omit_when_empty`` 补回来，值取自实例本身而不是重新造一个空 dict。
    """
    if isinstance(value, BaseModel):
        data = value.model_dump(by_alias=True, mode="json")
        for name in getattr(type(value), "_omit_when_empty", ()):
            field = type(value).model_fields.get(name)
            if field is None or getattr(value, name, None) is None:
                continue
            data.setdefault(field.alias or name, to_jsonable(getattr(value, name)))
        return {key: _fastjson_plain(item) for key, item in data.items()}
    if isinstance(value, dict):
        return {key: _fastjson_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_fastjson_plain(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return to_jsonable(value)


def _prune(value: Any, excluded: set) -> Any:
    """递归去掉敏感属性与值为 ``None`` 的成员（空容器保留，见模块 docstring 第 3 条）."""
    if isinstance(value, dict):
        return {
            key: _prune(item, excluded)
            for key, item in value.items()
            if key not in excluded and item is not None
        }
    if isinstance(value, (list, tuple)):
        return [_prune(item, excluded) for item in value]
    if isinstance(value, BaseModel):  # pragma: no cover - to_jsonable 已展开
        return _prune(to_jsonable(value), excluded)
    return value


def _ordered_arguments(
    func: Callable[..., Any], call_args: Tuple[Any, ...], call_kwargs: Dict[str, Any]
) -> List[Any]:
    """按**声明顺序**取出本次调用的实参.

    Java 的 ``joinPoint.getArgs()`` 是形参声明顺序；FastAPI 调端点时全部用关键字实参，
    ``Signature.bind(...).arguments`` 正好按形参顺序返回。绑定失败时退化成
    "位置实参 + 关键字实参"，至少不会丢信息。
    """
    try:
        bound = inspect.signature(func).bind(*call_args, **call_kwargs)
    except TypeError:
        return list(call_args) + list(call_kwargs.values())
    return list(bound.arguments.values())


def _resolve_java_controller(func: Callable[..., Any]) -> str:
    """取被装饰函数所在模块声明的 ``JAVA_CONTROLLER``（Java 控制器全类名）."""
    module = sys.modules.get(func.__module__)
    controller = getattr(module, JAVA_CONTROLLER_ATTRIBUTE, None)
    if not controller:
        raise RuntimeError(
            f"{func.__module__} 缺少 {JAVA_CONTROLLER_ATTRIBUTE} 常量："
            f"sys_oper_log.method 需要 Java 控制器全类名（见 COMPATIBILITY.md）"
        )
    return str(controller)


__all__ = [
    "CONTENT_MAX",
    "EXCLUDE_PROPERTIES",
    "JAVA_CONTROLLER_ATTRIBUTE",
    "URL_MAX",
    "log",
]
