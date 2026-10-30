"""任务执行工具.

# Migrated from: ruoyi-quartz/src/main/java/com/ruoyi/quartz/util/JobInvokeUtil.java

``invokeTarget`` 是 ``sys_job.invoke_target`` 里的字符串，形如::

    ryTask.ryNoParams
    ryTask.ryParams('ry')
    ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)
    vehicleMonitoringTask.syncOrgInfo

解析规则与 Java 完全一致（见各函数 docstring），最终

* ``isValidClassName(beanName) == False`` -> ``SpringUtils.getBean(beanName)`` 取单例；
* ``isValidClassName(beanName) == True``  -> ``Class.forName(beanName).newInstance()``。

参数类型推断的**顺序**不能换
--------------------------
``getMethodParams`` 是 ``if/else if`` 链：

1. 含 ``'`` -> String（并把**所有**引号删掉）；
2. ``equals(str,"true") || equalsIgnoreCase(str,"false")`` -> Boolean；
3. 忽略大小写含 ``L`` -> Long；
4. 忽略大小写含 ``D`` -> Double；
5. 其余 -> Integer。

第 2 步必须排在第 3 步之前：``"false"`` 小写含 ``l``，若先判 ``L`` 会去
``Long.valueOf("fase")`` 抛 ``NumberFormatException``。线上
``ryTask.ryMultipleParams('ry', true, 2000L, 316.50D, 100)`` 能跑通就是因为这个顺序。

``getDeclaredMethod`` 与 ``getattr`` 的差异
----------------------------------------
Java 的 ``getDeclaredMethod`` **只找本类声明的方法**，不找父类继承的；``getattr``
会连同基类的 public 属性一起找。本工程 6 个任务类都是 ``@Component`` 的叶子类
（没有继承），所以两种情况等价 —— 已登记到 ``COMPATIBILITY.md``。

另有一处**必须**的差异：``sys_job.invoke_target`` 里存的是 Java 的方法名
（``ryNoParams`` / ``syncOrgInfo`` / ``getTollBoothInfoList`` ...，线上 18 条记录
一字不差），而迁移后的 Python 方法名是 ``snake_case``（``ry_no_params``）。所以
:func:`_declared_method` 先按原名取，取不到再按
:func:`~app.common.utils.string_utils.to_under_score_case` 转换后取一次 ——
这就是 :data:`sys_job.invoke_target` 与 Python 方法名之间的**唯一**桥。
名字对不上时报的仍是 Java 原文名（``NoSuchMethodException: ...ryNoParams()``）。
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from app.common.utils import spring_utils as SpringUtils
from app.common.utils.string_utils import (
    contains as string_contains,
    contains_ignore_case,
    count_matches,
    equals as string_equals,
    equals_ignore_case,
    is_empty,
    is_not_null,
    replace,
    replace_ignore_case,
    substring_after_last,
    substring_before,
    substring_before_last,
    substring_between,
    to_under_score_case,
    trim_to_empty,
)
from app.quartz.domain.sys_job import SysJob

#: Java 的 ``Object[]{value, Class}`` —— ``(值, Java 类型名)``。
#: 类型名只是**记录**，Python 侧按位置传参，不做分派。
JAVA_STRING = "java.lang.String"
JAVA_BOOLEAN = "java.lang.Boolean"
JAVA_LONG = "java.lang.Long"
JAVA_DOUBLE = "java.lang.Double"
JAVA_INTEGER = "java.lang.Integer"


# Java: public static void invokeMethod(SysJob sysJob) throws Exception
def invoke_method(sys_job: SysJob) -> None:
    """按 ``invokeTarget`` 反射调用目标方法."""
    invoke_target = sys_job.invoke_target
    bean_name = get_bean_name(invoke_target)
    method_name = get_method_name(invoke_target)
    method_params = get_method_params(invoke_target)

    if not is_valid_class_name(bean_name):
        # Java: Object bean = SpringUtils.getBean(beanName);
        bean = SpringUtils.get_bean(bean_name)
        _invoke(bean, method_name, method_params)
    else:
        # Java: Object bean = Class.forName(beanName).newInstance();
        bean = _instantiate_class(bean_name)
        _invoke(bean, method_name, method_params)


# Java: private static void invokeMethod(Object bean, String methodName, List<Object[]> methodParams)
def _invoke(bean: Any, method_name: str, method_params: Optional[List[Tuple[Any, str]]]) -> None:
    """Java: ``bean.getClass().getDeclaredMethod(name[, types]).invoke(bean[, values])``."""
    if is_not_null(method_params) and len(method_params) > 0:
        # Java 用参数类型做精确查找；Python 只能按名字，参数类型由调用方保证。
        method = _declared_method(bean, method_name, expected=len(method_params))
        method(*get_method_params_value(method_params))
    else:
        method = _declared_method(bean, method_name, expected=0)
        method()


def _declared_method(bean: Any, method_name: str, expected: int) -> Any:
    """Java: ``getDeclaredMethod`` —— 找不到时抛 ``NoSuchMethodException``.

    ``method_name`` 是 ``invoke_target`` 里的 **Java 名**（``ryNoParams``），
    所以原名取不到时再试一次 ``snake_case`` 形态（``ry_no_params``）；
    报错文案仍用 Java 原名，与 ``getDeclaredMethod`` 的异常信息一致。
    ``expected`` 只用于文档化"按几个参数查找"，Python 侧无法按类型分派。
    """
    method = getattr(bean, method_name, None)
    if method is None or not callable(method):
        # ``to_under_score_case`` 与 Java 的 StringUtils 同名方法逐字一致，
        # 所以 ``ryNoParams`` -> ``ry_no_params``、``getTollBoothInfoList`` 同名不变。
        snake_name = to_under_score_case(method_name)
        if snake_name and snake_name != method_name:
            method = getattr(bean, snake_name, None)
    if method is None or not callable(method):
        # Java: java.lang.NoSuchMethodException: com.xxx.RyTask.ryNoParams()
        raise AttributeError(
            f"java.lang.NoSuchMethodException: {type(bean).__name__}.{method_name}()"
        )
    return method


def _instantiate_class(class_name: str) -> Any:
    """Java: ``Class.forName(beanName).newInstance()``.

    本工程没有以"全类名"形式配置的 ``invoke_target``（18 条记录全是 bean 名），
    所以这里只支持 Python 模块路径 / 已注册的类名两种形态。找不到时抛
    ``ClassNotFoundException`` 的等价错误，文案保持 Java 的样子。
    """
    module_path, _, class_name_short = class_name.rpartition(".")
    if not module_path:
        raise LookupError(f"java.lang.ClassNotFoundException: {class_name}")
    try:
        import importlib

        module = importlib.import_module(module_path)
        target = getattr(module, class_name_short)
    except (ImportError, AttributeError) as exc:
        raise LookupError(f"java.lang.ClassNotFoundException: {class_name}") from exc
    return target()


# Java: public static boolean isValidClassName(String invokeTarget)
def is_valid_class_name(invoke_target: Optional[str]) -> bool:
    """是不是"全类名"（点号多于 1 个）。"""
    return count_matches(invoke_target, ".") > 1


# Java: public static String getBeanName(String invokeTarget)
def get_bean_name(invoke_target: Optional[str]) -> Optional[str]:
    """``"ryTask.ryParams('ry')"`` -> ``"ryTask"``."""
    bean_name = substring_before(invoke_target, "(")
    return substring_before_last(bean_name, ".")


# Java: public static String getMethodName(String invokeTarget)
def get_method_name(invoke_target: Optional[str]) -> Optional[str]:
    """``"ryTask.ryParams('ry')"`` -> ``"ryParams"``."""
    method_name = substring_before(invoke_target, "(")
    return substring_after_last(method_name, ".")


# Java: public static List<Object[]> getMethodParams(String invokeTarget)
def get_method_params(invoke_target: Optional[str]) -> Optional[List[Tuple[Any, str]]]:
    """解析括号内的参数串；没有参数时返回 ``None``（Java 返回 ``null``）."""
    method_str = substring_between(invoke_target, "(", ")")
    if is_empty(method_str):
        return None
    assert method_str is not None
    # Java: methodStr.split(",") —— 注意这是**正则** split，这里按字面量 "," 切分；
    # 两者的差异只出现在参数里含 "," 正则元字符的情况，业务上不会发生。
    params: List[Tuple[Any, str]] = []
    for raw in method_str.split(","):
        text = trim_to_empty(raw)
        if string_contains(text, "'"):
            # String 字符串类型，包含 '
            params.append((replace(text, "'", ""), JAVA_STRING))
        elif string_equals(text, "true") or equals_ignore_case(text, "false"):
            # boolean 布尔类型，等于 true 或者 false（**必须**排在 L / D 之前）
            params.append((text.lower() == "true", JAVA_BOOLEAN))
        elif contains_ignore_case(text, "L"):
            # long 长整形，包含 L
            params.append((_parse_long(replace_ignore_case(text, "L", "")), JAVA_LONG))
        elif contains_ignore_case(text, "D"):
            # double 浮点类型，包含 D
            params.append((_parse_double(replace_ignore_case(text, "D", "")), JAVA_DOUBLE))
        else:
            # 其他类型归类为整形
            params.append((_parse_int(text), JAVA_INTEGER))
    return params


def _parse_int(text: Optional[str]) -> int:
    """Java: ``Integer.valueOf(String)``."""
    try:
        return int(_require(text))
    except (TypeError, ValueError):
        raise ValueError(
            f'java.lang.NumberFormatException: For input string: "{text}"'
        ) from None


def _parse_long(text: Optional[str]) -> int:
    """Java: ``Long.valueOf(String)`` —— Python 只有一个 ``int``."""
    try:
        return int(_require(text))
    except (TypeError, ValueError):
        raise ValueError(
            f'java.lang.NumberFormatException: For input string: "{text}"'
        ) from None


def _parse_double(text: Optional[str]) -> float:
    """Java: ``Double.valueOf(String)``."""
    try:
        return float(_require(text))
    except (TypeError, ValueError):
        raise ValueError(
            f'java.lang.NumberFormatException: For input string: "{text}"'
        ) from None


def _require(text: Optional[str]) -> str:
    if text is None:
        raise ValueError('java.lang.NumberFormatException: null')
    return text


# Java: public static Class<?>[] getMethodParamsType(List<Object[]> methodParams)
def get_method_params_type(method_params: List[Tuple[Any, str]]) -> List[str]:
    """Java 返回 ``Class<?>[]``；本工程返回 Java 类型名列表（见模块常量）."""
    return [java_type for _value, java_type in method_params]


# Java: public static Object[] getMethodParamsValue(List<Object[]> methodParams)
def get_method_params_value(method_params: List[Tuple[Any, str]]) -> List[Any]:
    """Java 返回 ``Object[]``."""
    return [value for value, _java_type in method_params]


__all__ = [
    "invoke_method",
    "is_valid_class_name",
    "get_bean_name",
    "get_method_name",
    "get_method_params",
    "get_method_params_type",
    "get_method_params_value",
]
