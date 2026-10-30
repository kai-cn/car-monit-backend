# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysMenu.java
"""菜单权限表 sys_menu / menu item.

``MENU_CONSTRAINTS``
--------------------
Java 把 ``@NotBlank`` / ``@Size`` 挂在 **getter** 上，由 ``SysMenuController`` 的
``@Validated @RequestBody`` 触发（``add`` / ``edit`` 两个端点）。Python 侧把同一组约束
放在实体旁边（同位置、同顺序），由端点显式调用
:func:`app.common.utils.bean_validation.validate`。

**只有 6 个字段有约束**：``parentName`` / ``parentId`` / ``isFrame`` / ``isCache`` /
``visible`` / ``status`` / ``icon`` 在 Java 上**没有任何注解**，所以它们可以随便空着 ——
不要看到 ``@NotBlank`` 就"补全"到所有字段。

``component`` 的文案与上限对不上
--------------------------------
``@Size(min = 0, max = 200, message = "组件路径不能超过255个字符")`` —— 上限是 **200**，
文案写的是 255。这是 Java 原文，照抄（§29）。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import Field

from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.domain_model import JavaString
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysMenu(BaseEntity):
    """Java: ``SysMenu extends BaseEntity``.

    ``children``
        Java initialises it to ``new ArrayList<>()``, so ``getChildren()`` is **never**
        ``null``. ``SysMenuServiceImpl#buildMenus`` relies on that (``cMenus.isEmpty()``
        would NPE otherwise), hence ``default_factory=list`` rather than ``None``.

    No ``@JsonInclude``
        Unlike ``RouterVo`` / ``TreeSelect``, this class carries no inclusion annotation,
        so every field is serialized -- ``null`` included, and ``children`` is always
        present (an empty list on a leaf). ``GET /getRouters`` converts each row into a
        ``RouterVo``, but ``/system/menu/list`` / ``treeselect`` / ``roleMenuTreeselect``
        hand the entity to the client **as is**, so the fat payload is what the Vue side
        actually receives.

    Ordering
        The two tree queries end with ``order by parent_id, order_num``. The ORDER BY is
        what makes ``getChildPerms`` produce a stable child order -- do not sort again in
        Python, that would reorder siblings.
    """

    #: 菜单ID
    menu_id: Optional[int] = None
    #: 菜单名称
    menu_name: Optional[str] = None
    #: 父菜单名称 -- never selected by the tree queries, so always ``None`` there
    parent_name: Optional[str] = None
    #: 父菜单ID
    parent_id: Optional[int] = None
    #: 显示顺序 -- a varchar column despite the name
    order_num: JavaString = None
    #: 路由地址
    path: Optional[str] = None
    #: 组件路径
    component: Optional[str] = None
    #: 是否为外链（0是 1否）
    is_frame: Optional[str] = None
    #: 是否缓存（0缓存 1不缓存）
    is_cache: Optional[str] = None
    #: 类型（M目录 C菜单 F按钮）
    menu_type: Optional[str] = None
    #: 显示状态（0显示 1隐藏）
    visible: Optional[str] = None
    #: 菜单状态（0显示 1隐藏）
    status: Optional[str] = None
    #: 权限字符串
    perms: Optional[str] = None
    #: 菜单图标
    icon: Optional[str] = None
    #: 子菜单 -- never ``None``, matching ``new ArrayList<SysMenu>()``
    children: List["SysMenu"] = Field(default_factory=list)


#: ``@Validated @RequestBody SysMenu`` 的校验项，顺序与 Java 里 getter 的声明顺序一致。
MENU_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "菜单名称不能为空") @Size(min = 0, max = 50, ...)
    NotBlank("menu_name", "菜单名称不能为空"),
    Size("menu_name", max=50, message="菜单名称长度不能超过50个字符"),
    # Java: @NotBlank(message = "显示顺序不能为空") —— 没有 @Size
    NotBlank("order_num", "显示顺序不能为空"),
    # Java: @Size(min = 0, max = 200, message = "路由地址不能超过200个字符")
    Size("path", max=200, message="路由地址不能超过200个字符"),
    # Java: @Size(min = 0, max = 200, message = "组件路径不能超过255个字符") —— 200 vs 255 是原文
    Size("component", max=200, message="组件路径不能超过255个字符"),
    # Java: @NotBlank(message = "菜单类型不能为空")
    NotBlank("menu_type", "菜单类型不能为空"),
    # Java: @Size(min = 0, max = 100, message = "权限标识长度不能超过100个字符")
    Size("perms", max=100, message="权限标识长度不能超过100个字符"),
)


__all__ = ["SysMenu", "MENU_CONSTRAINTS"]
