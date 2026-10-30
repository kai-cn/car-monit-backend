"""web层通用数据处理 / web-layer helpers shared by every controller.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/controller/BaseController.java

Java 的 ``BaseController`` 是一个被所有控制器 ``extends`` 的基类，提供
``startPage()`` / ``getDataTable()`` / ``toAjax()`` 等。Python 的控制器是模块级函数，
没有继承关系，所以这些方法按"职责"分散到各自的模块，本模块只做两件事：

1. **转出**（re-export）已经实现好的那几个，保证调用点仍然读作 ``base_controller.xxx``；
2. 提供 Java 里由 **Spring MVC 自动完成**、Python 必须手写的那部分：
   ``@InitBinder`` 的日期转换和 ``SysUser user`` 形态的**请求参数绑定**。

方法对照表
----------
    ==========================================  =========================================
    Java (BaseController)                        Python
    ==========================================  =========================================
    ``startPage()``                              :func:`start_page` (page_helper)
    ``startOrderBy()``                           ``page_helper`` 的 ``orderBy`` 分支
    ``clearPage()``                              :func:`clear_page`
    ``getDataTable(List<?>)``                    :func:`get_data_table`
    ``toAjax(int)`` / ``toAjax(boolean)``        :func:`to_ajax`
    ``success()`` / ``error()`` / ``warn(...)``  ``AjaxResult.success()`` 等
    ``getLoginUser()``                           ``SecurityUtils.get_login_user()``
    ``getUserId()`` / ``getDeptId()``            同名函数
    ``getUsername()``                            ``SecurityUtils.get_username()``
    ``@InitBinder`` 的 ``Date`` 编辑器            :func:`bind_query_params`
    ==========================================  =========================================

为什么需要 ``bind_query_params``
--------------------------------
Java 的 ``@GetMapping("/list") public TableDataInfo list(SysUser user)`` 里，
``SysUser`` **没有** ``@RequestBody``，于是 Spring 的 ``ServletModelAttributeMethodProcessor``
把 **query string** 上的同名字段逐个 setter 进去：

* 参数名是 Java 属性名（``userName`` / ``deptId`` / ``excludeSelf``）；
* ``params[beginTime]=...`` 会写进 ``BaseEntity.params`` 这个 Map
  （``BeanWrapperImpl`` 的 ``params[key]`` 自动扩容语义）；
* ``String`` 属性原样保留（含空串）；包装类型 ``Long``/``Integer``/``Boolean``
  收到空串时得到 ``null``（``StringToNumberConverterFactory`` / ``CustomBooleanEditor``）；
* ``Date`` 属性走 ``@InitBinder`` 注册的编辑器 -> ``DateUtils.parseDate``；
* 无法识别的参数名直接忽略（``WebDataBinder.setIgnoreUnknownFields(true)`` 是默认值）。

FastAPI 的查询参数绑定要求逐个参数声明，没法"整个对象"绑定，所以这里复刻一遍上述规则。

类型转换失败时的差异（已记录在 COMPATIBILITY.md）
------------------------------------------------
Spring 会抛 ``BindException``，被 ``GlobalExceptionHandler`` 接住，回
**HTTP 200** + ``{"code":500,"msg":"Failed to convert property value of type ..."}``。
这里抛 ``ValueError``，由通用 ``Exception`` 处理器接住，也是 **HTTP 200** + ``code 500``，
只有文案不同（没有客户端解析这段文案）。
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from app.common.core.page.page_helper import clear_page, start_page
from app.common.core.page.table_data_info import get_data_table
from app.common.core.domain.ajax_result import AjaxResult, to_ajax
from app.common.exception.exceptions import ServiceException
from app.common.utils import security_utils as SecurityUtils
from app.common.utils.json_utils import parse_date_time

logger = logging.getLogger("app.common.core.controller.base_controller")

#: Java: ``params[beginTime]`` -> ``BaseEntity.params.put("beginTime", ...)``.
_PARAMS_MAP_PATTERN = re.compile(r"^params\[(.+)\]$")

#: Java: ``CustomBooleanEditor`` 认识的字符串（大小写不敏感）。
_TRUE_WORDS = frozenset({"true", "on", "yes", "1"})
_FALSE_WORDS = frozenset({"false", "off", "no", "0"})

M = TypeVar("M", bound=BaseModel)

_NONE_TYPE = type(None)


# --------------------------------------------------------------------------- 参数绑定


def bind_query_params(model_cls: Type[M], values: Mapping[str, str]) -> M:
    """把 query string 绑定到实体上，等价于 Spring 的"无注解实体参数"。

    参数
    ----
    model_cls
        目标实体（``SysUser`` / ``SysRole`` / ``SysDept`` ... 均为 ``DomainModel`` 子类，
        字段名是 ``snake_case``、别名是 Java 的 ``camelCase``）。
    values
        ``request.query_params``。用 ``multi_items()`` 而不是 ``items()``：
        Spring 的 ``getParameter`` 取**第一个**值，这里同样只认第一个。
    """
    fields = model_cls.model_fields
    by_alias = {_alias_of(name, info): (name, info) for name, info in fields.items()}

    data: Dict[str, Any] = {}
    params_map: Dict[str, Any] = {}

    multi_items = getattr(values, "multi_items", None)
    pairs = multi_items() if callable(multi_items) else list(dict(values).items())

    for raw_key, raw_value in pairs:
        map_match = _PARAMS_MAP_PATTERN.match(raw_key)
        if map_match is not None:
            params_map[map_match.group(1)] = raw_value
            continue
        target = by_alias.get(raw_key)
        if target is None:
            # Java: WebDataBinder 默认 ignoreUnknownFields=true
            continue
        name, field_info = target
        if name in data:
            # Java: request.getParameter(name) 只返回第一个值
            continue
        data[name] = _convert_value(raw_key, field_info, raw_value)

    if params_map:
        data["params"] = params_map

    try:
        return model_cls(**data)
    except Exception:  # noqa: BLE001 - 交给通用处理器，见模块 docstring
        logger.error("[参数绑定失败] %s <- %s", model_cls.__name__, raw_data_repr(data))
        raise


def raw_data_repr(data: Mapping[str, Any]) -> str:
    """Omit ``password``-style fields from bind-failure logs."""
    return str({k: v for k, v in data.items() if "password" not in k.lower()})


def _alias_of(name: str, info: FieldInfo) -> str:
    return info.alias or name


def _unwrap(annotation: Any) -> tuple:
    """Flatten ``Optional[X]`` / ``Union[...]`` into its member types."""
    origin = get_origin(annotation)
    if origin is Union:  # includes ``Optional[X]``
        members = []
        for arg in get_args(annotation):
            members.extend(_unwrap(arg))
        return tuple(members)
    return (annotation,)


def _accepts(annotation: Any, wanted: type) -> bool:
    return any(member is wanted or (isinstance(member, type) and issubclass(member, wanted)) for member in _unwrap(annotation))


def _accepts_none(annotation: Any) -> bool:
    return _NONE_TYPE in _unwrap(annotation)


def _convert_value(key: str, info: FieldInfo, raw_value: Any) -> Any:
    """一个字段的类型转换，规则见模块 docstring。"""
    annotation = info.annotation

    # String 属性原样保留，包括空串（Spring 没有注册 StringTrimmerEditor）
    if _accepts(annotation, str):
        return raw_value

    if raw_value == "":
        # StringToNumberConverterFactory / CustomBooleanEditor(allowEmpty=true) -> null
        return None

    if _accepts(annotation, bool):
        return _to_boolean(key, raw_value)
    if _accepts(annotation, int):
        return _to_integer(key, raw_value)
    if _accepts(annotation, datetime):
        # Java: BaseController#initBinder -> DateUtils.parseDate(text)
        return parse_date_time(raw_value)

    # 其余类型交给 pydantic（本项目里没有：实体字段只有上面四类）
    return raw_value


def _to_boolean(key: str, raw_value: str) -> bool:
    word = str(raw_value).strip().lower()
    if word in _TRUE_WORDS:
        return True
    if word in _FALSE_WORDS:
        return False
    # Java: CustomBooleanEditor -> setValue 失败 -> BindException
    raise ValueError(
        f"Failed to convert property value of type 'java.lang.String' to required type "
        f"'java.lang.Boolean' for property '{key}'; nested exception is "
        f"java.lang.IllegalArgumentException: Invalid boolean value [{raw_value}]"
    )


def _to_integer(key: str, raw_value: str) -> int:
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        raise ValueError(
            f"Failed to convert property value of type 'java.lang.String' to required type "
            f"'java.lang.Long' for property '{key}'; nested exception is "
            f"java.lang.NumberFormatException: For input string: \"{raw_value}\""
        ) from None


def parse_id_array(raw: str) -> List[int]:
    """Java: ``@PathVariable Long[] userIds`` —— 逗号串 -> ``Long[]``.

    Spring 的 ``StringToArrayConverter`` 先按 ``,`` 切分再逐个转 ``Long``：

    * ``"1,2,3"`` -> ``[1, 2, 3]``；
    * 空串 -> 长度为 1 的数组，元素转换失败 -> ``MethodArgumentTypeMismatchException``；
    * 非数字 -> 同上，回 HTTP 200 + ``code 500``。

    这里用 ``int(part)`` 抛 ``ValueError``，落到的通用处理器与前者一致。
    """
    return [int(part) for part in raw.split(",")]


def parse_long_array(raw: str, param_name: str) -> List[int]:
    """Java: ``@PathVariable Long[] xxx`` —— 与 :func:`parse_id_array` 等价，但**文案对齐 Java**.

    ``parse_id_array`` 抛的是 Python 自己的 ``ValueError``
    （``invalid literal for int() with base 10: 'abc'``）；而 Spring 抛的是
    ``MethodArgumentTypeMismatchException``，由 ``GlobalExceptionHandler`` 翻成中文本地化文案::

        请求参数类型不匹配，参数[jobIds]要求类型为：'[Ljava.lang.Long;'，但输入值为：'abc'

    ``[Ljava.lang.Long;`` 是 ``Long[].class.getName()`` 的原样输出，不是笔误。

    为什么抛 :class:`~app.common.exception.exceptions.ServiceException` 而不是
    ``ValueError``：``Exception`` 处理器挂在 ``ServerErrorMiddleware`` 上，响应发完还会
    **重新抛**；``ServiceException`` 走 ``ExceptionMiddleware``，只发一次。两者对客户端
    的响应体完全相同（``{"code":500,"msg":...}``），见 :mod:`app.config.exception_handlers`。
    """
    try:
        return [int(part) for part in raw.split(",")]
    except ValueError:
        raise ServiceException(
            "请求参数类型不匹配，参数[%s]要求类型为：'[Ljava.lang.Long;'，但输入值为：'%s'"
            % (param_name, raw)
        ) from None


def parse_str_array(raw: str) -> List[str]:
    """Java: ``@PathVariable String[] ids`` —— 逗号串 -> ``String[]``，**不做**类型转换。

    与 :func:`parse_id_array` 的唯一区别：目标元素类型是 ``String``，Spring 的
    ``StringToArrayConverter`` 碰到 ``String`` 会直接透传，所以：

    * ``"a,b"`` -> ``["a", "b"]``；非 UUID 字符串、中文、空格都照收；
    * 空串 -> ``[""]``（长度 1 的数组，**不会**报错）；
    * ``"a,,b"`` -> ``["a", "", "b"]``。

    ``sys_upgrade_info`` 的主键是 UUID 字符串，它的 ``remove`` 用的是 ``String[]``
    （其它模块都是 ``Long[]``），所以不能复用 :func:`parse_id_array`。
    """
    return raw.split(",")


# --------------------------------------------------------------------------- 转出


def get_login_user():
    """Java: ``BaseController#getLoginUser()``."""
    return SecurityUtils.get_login_user()


def get_user_id() -> Optional[int]:
    """Java: ``BaseController#getUserId()``."""
    return SecurityUtils.get_user_id()


def get_dept_id() -> int:
    """Java: ``BaseController#getDeptId()`` -> ``SecurityUtils.getEpsId()``."""
    return SecurityUtils.get_eps_id()


def get_username() -> str:
    """Java: ``BaseController#getUsername()``."""
    return SecurityUtils.get_username()


def success() -> AjaxResult:
    """Java: ``BaseController#success()``."""
    return AjaxResult.success()


def error() -> AjaxResult:
    """Java: ``BaseController#error()``."""
    return AjaxResult.error()


def warn(message: str) -> AjaxResult:
    """Java: ``BaseController#warn(String)``."""
    return AjaxResult.warn(message)


__all__ = [
    "bind_query_params",
    "raw_data_repr",
    "parse_id_array",
    "parse_long_array",
    "parse_str_array",
    "start_page",
    "clear_page",
    "get_data_table",
    "to_ajax",
    "success",
    "error",
    "warn",
    "get_login_user",
    "get_user_id",
    "get_dept_id",
    "get_username",
]
