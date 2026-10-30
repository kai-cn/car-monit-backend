"""Bean 工具类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/bean/BeanUtils.java

Java 侧 ``BeanUtils extends org.springframework.beans.BeanUtils``，本项目实际**只用到**
``copyBeanProp``（``AbstractQuartzJob#execute`` 用它把 ``JobDataMap`` 里的 ``SysJob``
复制进一个新的 ``SysJob``）。另外三个反射方法（``getSetterMethods`` /
``getGetterMethods`` / ``isMethodPropEquals``）在 Java 侧**没有任何调用点**，
而且它们的返回值是 ``java.lang.reflect.Method`` 列表 —— Python 没有对应概念，
强行造一个"方法名列表"只会让调用方误以为可以做反射调用。

``copyBeanProp` 的 Python 实现
------------------------------
Spring 的 ``copyProperties(src, dest)`` 按**属性名**逐个 ``get``/``set``：
同名同类型才复制，``null`` 也会复制过去（它不做非空判断），并且**忽略**
``class`` 属性。本工程全部实体都是 pydantic ``BaseModel``，所以：

* 只在 ``dest`` 已有该字段时才写（``model_fields``），等价于"仅当 setter 存在"；
* 不做类型转换 —— Spring 会尝试 ``TypeConverter``，但本项目两边永远是同一个类
  （``SysJob`` -> ``SysJob``），不需要；
* ``model_config.extra="ignore"`` 让多出来的键自然被丢弃。

``copyBeanProp`` 的 Java 实现把异常**吞掉**（``catch (Exception e) { e.printStackTrace(); }``），
这里同样不抛 —— 复制失败只记日志。
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, List

from pydantic import BaseModel

logger = logging.getLogger("app.common.utils.bean_utils")

#: Java: ``private static final int BEAN_METHOD_PROP_INDEX = 3`` —— ``get``/``set`` 前缀长度。
BEAN_METHOD_PROP_INDEX = 3


def copy_bean_prop(dest: Any, src: Any) -> None:
    """Java: ``copyBeanProp(Object dest, Object src)`` —— 按属性名把 ``src`` 拷到 ``dest``.

    异常被吞掉（Java 原文 ``catch (Exception e) { e.printStackTrace(); }``）。
    """
    if dest is None or src is None:
        return
    try:
        if isinstance(dest, BaseModel):
            _copy_into_model(dest, src)
            return
        _copy_into_object(dest, src)
    except Exception:  # noqa: BLE001 - Java 原文吞异常，只打印堆栈
        logger.exception("[Bean 属性复制失败] %s <- %s", type(dest).__name__, type(src).__name__)


def _copy_into_model(dest: BaseModel, src: Any) -> None:
    """``BaseModel`` 目标：只写目标已有的字段（等价于"仅当 setter 存在"）。"""
    if isinstance(src, BaseModel):
        values = {name: getattr(src, name) for name in type(src).model_fields}
    elif isinstance(src, dict):
        values = dict(src)
    else:
        values = {
            name: getattr(src, name)
            for name in dir(src)
            if not name.startswith("_") and not callable(getattr(src, name, None))
        }

    for name in type(dest).model_fields:
        if name not in values:
            continue
        try:
            setattr(dest, name, values[name])
        except (ValueError, TypeError):
            # pydantic 的校验失败：Spring 侧同样会抛，然后被上层 catch 吞掉。
            # 这里只跳过该字段，保证其余字段仍被复制 —— 与 Spring 逐属性复制的粒度一致。
            logger.debug("[Bean 属性复制] 跳过字段 %s（类型不匹配）", name)


def _copy_into_object(dest: Any, src: Any) -> None:
    """普通对象目标：有同名属性且不是方法才写。"""
    source_values = (
        src.model_dump() if isinstance(src, BaseModel) else getattr(src, "__dict__", {})
    )
    for name, value in source_values.items():
        if not hasattr(dest, name):
            continue
        if callable(getattr(dest, name, None)):
            continue
        setattr(dest, name, value)


def is_method_prop_equals(method1: str, method2: str) -> bool:
    """Java: ``isMethodPropEquals(String m1, String m2)`` —— 去掉 ``get``/``set`` 前缀后比较.

    例：``"getName"`` 与 ``"setName"`` -> ``True``；``"getName"`` 与 ``"setAge"`` -> ``False``。
    Java 侧没有调用点，按原则第 4 条照搬。
    """
    return method1[BEAN_METHOD_PROP_INDEX:] == method2[BEAN_METHOD_PROP_INDEX:]


def get_setter_methods(obj: Any) -> List[str]:
    """Java: ``getSetterMethods(Object)`` —— 可写属性名，按 ``setXxx`` 形式给出.

    Java 返回 ``List<Method>``（只收"一个参数 + 名字匹配 ``set(\\p{javaUpperCase}\\w*)``"）。
    Python 没有可调用的反射句柄，所以退化成**名字**列表：

    * ``BaseModel`` —— 可写字段名转 ``setXxx``（pydantic 没有生成 setter，字段本身就是入口）；
    * 普通对象 —— 真实的 ``set_xxx`` 方法。

    Java 侧没有调用点，按原则第 4 条照搬。
    """
    if isinstance(obj, BaseModel):
        return [_setter_name(name) for name in type(obj).model_fields]
    return [name for name in _method_names(obj, "set") if _takes_one_argument(obj, name)]


def get_getter_methods(obj: Any) -> List[str]:
    """Java: ``getGetterMethods(Object)`` —— 无参 ``getXxx`` 方法名列表."""
    return _method_names(obj, "get")


def _setter_name(attribute: str) -> str:
    """``job_name`` -> ``"setJobName"``（与 Java 的 ``setJobName`` 一一对应）。"""
    head, *rest = attribute.split("_")
    return "set" + head[:1].upper() + head[1:] + "".join(part.capitalize() for part in rest)


def _takes_one_argument(obj: Any, name: str) -> bool:
    attribute = getattr(obj, name, None)
    if not callable(attribute):
        return False
    try:
        return len(inspect.signature(attribute).parameters) == 1
    except (TypeError, ValueError):  # pragma: no cover - 内建函数
        return False


def _method_names(obj: Any, prefix: str) -> List[str]:
    names: List[str] = []
    for name in dir(type(obj)):
        if not name.startswith(prefix) or len(name) <= len(prefix):
            continue
        if not name[len(prefix)].isupper():
            # Java 的正则 ``get(\p{javaUpperCase}\w*)`` 要求前缀后第一个字符大写
            continue
        if not callable(getattr(obj, name, None)):
            continue
        names.append(name)
    return names


__all__ = [
    "BEAN_METHOD_PROP_INDEX",
    "copy_bean_prop",
    "is_method_prop_equals",
    "get_setter_methods",
    "get_getter_methods",
]
