"""Spring 工具类（Bean 服务定位器）.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/spring/SpringUtils.java

Java 侧 ``SpringUtils`` 实现 ``ApplicationContextAware``，把 ``ApplicationContext``
存成静态字段，于是"普通工具类/抽象类"也能按名字或类型拿到 Bean::

    SpringUtils.getBean(beanName)               // 按名字（JobInvokeUtil 用）
    SpringUtils.getBean(ISysJobLogService.class)// 按类型（AbstractQuartzJob 用）
    SpringUtils.containsBean(beanName)
    SpringUtils.isSingleton(beanName)
    SpringUtils.getType(beanName)
    SpringUtils.getAopProxy(bean)               // 取某个 Bean 的 AOP 代理

Python 没有容器，本模块用一个**显式注册表**复刻同一个服务定位器的语义：

* :func:`register_bean` / :func:`register_named` 由各模块在定义处调用，等价于
  ``@Component("ryTask")`` —— 名字就是注解里的 value；
* :func:`get_bean` 同时接受**名字**（``"ryTask"``）和**类型**（``RyTask``），
  与 Java 的两个重载一一对应；查不到时抛 :class:`NoSuchBeanDefinitionException`
  （Spring 抛 ``NoSuchBeanDefinitionException``，它的 ``getMessage`` 就是
  ``No bean named 'xxx' available``，这里照抄这句文案，因为
  ``JobInvokeUtil.invokeMethod`` 的异常最终会进 ``sys_job_log.exception_info``）。

``getAopProxy``
---------------
Java 里 ``SpringUtils.getAopProxy(this)`` 用 ``AopContext.currentProxy()`` 拿到**代理**，
目的是让自调用也走 ``@Transactional`` / ``@DataScope`` 切面。Python 没有代理，
本项目把需要切面的调用点显式写成两次调用（见
:mod:`app.system.service.sys_role_service` 的说明），所以这里只保留
``get_aop_proxy`` 这个"原样返回"的壳，供调用点保持可读的对应关系。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

#: 名字 -> Bean 实例。
_BEANS: Dict[str, Any] = {}


class NoSuchBeanDefinitionException(LookupError):
    """Java: ``org.springframework.beans.factory.NoSuchBeanDefinitionException``."""

    def __init__(self, name: str) -> None:
        super().__init__(f"No bean named '{name}' available")
        self.bean_name = name


def register_named(name: str, bean: Any) -> Any:
    """Java: ``@Component("name")`` —— 以显式名字注册（返回入参，便于写成装饰器结果）。"""
    _BEANS[name] = bean
    return bean


def register_bean(bean: Any, name: Optional[str] = None) -> Any:
    """Java: ``@Component`` / ``@Service`` —— 不给名字时用类名首字母小写（Spring 默认规则）。"""
    _BEANS[name or _default_bean_name(bean)] = bean
    return bean


def _default_bean_name(bean: Any) -> str:
    """Spring 的 ``AnnotationBeanNameGenerator``：简单类名首字母小写。"""
    class_name = type(bean).__name__
    return class_name[:1].lower() + class_name[1:]


def get_bean(name_or_type: Any) -> Any:
    """Java: ``getBean(String)`` / ``getBean(Class)``.

    ``str`` 按名字查；其它对象按**类型**查（``isinstance``），与
    ``getBean(ISysJobLogService.class)`` 的重载语义一致。
    """
    if isinstance(name_or_type, str):
        bean = _BEANS.get(name_or_type)
        if bean is None:
            raise NoSuchBeanDefinitionException(name_or_type)
        return bean

    wanted = name_or_type
    # 按类型查时，Java 找不到会抛 NoSuchBeanDefinitionException；这里给出类型名。
    for bean in _BEANS.values():
        if isinstance(bean, wanted):
            return bean
    raise NoSuchBeanDefinitionException(getattr(wanted, "__name__", str(wanted)))


def contains_bean(name: str) -> bool:
    """Java: ``containsBean(String)``. Python 侧只支持按名字。"""
    return name in _BEANS


def is_singleton(name: str) -> bool:
    """Java: ``isSingleton(String)``. 注册表里的 Bean 全部是单例。"""
    return name in _BEANS


def get_type(name: str) -> Optional[type]:
    """Java: ``getType(String)``."""
    bean = _BEANS.get(name)
    return type(bean) if bean is not None else None


def get_aop_proxy(bean: Any) -> Any:
    """Java: ``getAopProxy(Object)`` —— Python 无代理，原样返回。

    见模块 docstring：需要切面的自调用在 Python 侧是**显式多写一次调用**，
    所以这个函数只会出现在"为了保持一一对应"的位置上。
    """
    return bean


def clear_beans() -> None:
    """Test helper: 清空注册表（测试之间互不影响）。"""
    _BEANS.clear()


def unregister_bean(name: str) -> None:
    """Test helper: 摘掉一个 Bean（Spring 没有对应 API，容器销毁时整体丢弃）。"""
    _BEANS.pop(name, None)


__all__ = [
    "NoSuchBeanDefinitionException",
    "register_named",
    "register_bean",
    "get_bean",
    "contains_bean",
    "is_singleton",
    "get_type",
    "get_aop_proxy",
    "clear_beans",
    "unregister_bean",
]
