"""路由配置信息 / one entry of the Vue router tree.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/RouterVo.java

Java original
-------------
``@JsonInclude(JsonInclude.Include.NON_EMPTY)`` -- keys whose value is ``null``, ``""``,
an empty array or an empty map are **omitted**, not written as ``null``. Consequences a
client actually sees:

* ``name`` disappears for a top-level menu item (``getRouteName`` returns ``""``);
* ``meta`` disappears for the same case (``setMeta(null)``);
* ``redirect`` / ``alwaysShow`` only appear for a directory with children;
* ``query`` never appears (nothing in ``buildMenus`` sets it).

``hidden`` is the exception
    It is a **primitive** ``boolean`` in Java. Jackson's ``NON_EMPTY`` only suppresses
    ``null``, ``""`` and empty containers, and a primitive can be none of those, so
    ``"hidden": false`` is **always** written. Listing ``hidden`` in
    ``_omit_when_empty`` would therefore be a real behavioural difference -- that is why
    it is absent from the tuple below.

``alwaysShow`` is boxed
    ``Boolean``, hence ``null`` when unset. ``buildMenus`` only ever calls
    ``setAlwaysShow(true)``, so the reachable values are ``null`` (omitted) and ``true``
    (emitted); ``false`` cannot occur.
"""

from __future__ import annotations

from typing import ClassVar, List, Optional, Tuple

from app.common.core.domain.domain_model import DomainModel
from app.system.domain.vo.meta_vo import MetaVo


class RouterVo(DomainModel):
    """Java: ``@JsonInclude(NON_EMPTY) class RouterVo``."""

    #: 路由名字
    name: Optional[str] = None

    #: 路由地址
    path: Optional[str] = None

    #: 是否隐藏路由，当设置 true 的时候该路由不会再侧边栏出现 -- primitive, always emitted
    hidden: bool = False

    #: 重定向地址，当设置 noRedirect 的时候该路由在面包屑导航中不可被点击
    redirect: Optional[str] = None

    #: 组件地址
    component: Optional[str] = None

    #: 路由参数：如 {"id": 1, "name": "ry"} -- never set by ``buildMenus``
    query: Optional[str] = None

    #: 当你一个路由下面的 children 声明的路由大于1个时，自动会变成嵌套的模式
    always_show: Optional[bool] = None

    #: 其他元素
    meta: Optional[MetaVo] = None

    #: 子路由
    children: Optional[List["RouterVo"]] = None

    #: Java ``@JsonInclude(NON_EMPTY)``. ``hidden`` is deliberately missing -- see the
    #: module docstring: a primitive ``boolean`` is never suppressed by ``NON_EMPTY``.
    _omit_when_empty: ClassVar[Tuple[str, ...]] = (
        "name",
        "path",
        "redirect",
        "component",
        "query",
        "always_show",
        "meta",
        "children",
    )


__all__ = ["RouterVo"]
