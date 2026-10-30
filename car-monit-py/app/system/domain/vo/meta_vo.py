"""路由显示信息 / the ``meta`` block of a Vue router entry.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/vo/MetaVo.java

Java original
-------------
Four constructors (``title,icon`` / ``title,icon,noCache`` / ``title,icon,link`` /
``title,icon,noCache,link``). ``SysMenuServiceImpl#buildMenus`` only uses the three-argument
``MetaVo(String title, String icon, boolean noCache)`` form, so ``link`` is **always null**
in ``GET /getRouters`` -- it is still emitted (``"link": null``) because this class carries
no ``@JsonInclude``.

Inclusion rule
--------------
The absence of ``@JsonInclude`` matters: ``title``/``icon`` may be ``null`` and Jackson
still writes the key. That is the opposite of :class:`~app.system.domain.vo.router_vo.RouterVo`,
so this model deliberately has **no** ``_omit_when_empty``.

``noCache`` is a primitive ``boolean`` in Java, so it is never ``null``: it defaults to
``false`` and always appears in the payload.
"""

from __future__ import annotations

from typing import Optional

from app.common.core.domain.domain_model import DomainModel


class MetaVo(DomainModel):
    """Java: ``MetaVo``."""

    #: 设置该路由在侧边栏和面包屑中展示的名字
    title: Optional[str] = None

    #: 设置该路由的图标，对应路径 src/assets/icons/svg
    icon: Optional[str] = None

    #: 设置为 true，则不会被 <keep-alive> 缓存 -- Java primitive ``boolean``
    no_cache: bool = False

    #: 内链地址（http(s):// 开头）-- always ``None`` from ``buildMenus``
    link: Optional[str] = None


__all__ = ["MetaVo"]
