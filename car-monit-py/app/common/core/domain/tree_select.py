"""Treeselect 树结构实体类.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/TreeSelect.java

只装前端 ``el-tree-select`` / ``el-cascader`` 需要的三个字段（``id`` / ``label`` /
``children``），实体本身的其它属性一概不输出。

``children`` 是 ``@JsonInclude(NON_EMPTY)``
-------------------------------------------
和 :class:`app.common.core.domain.entity.SysDept` 的 ``children`` **不一样**：后者是
``new ArrayList<>()`` 且没有 ``@JsonInclude``，所以叶子节点也输出 ``"children": []``；
而 ``TreeSelect.children`` 为空时**整个键消失**。前端的树组件靠这个区分叶子与空目录。

Java 的两个构造器
-----------------
``TreeSelect(SysDept)`` / ``TreeSelect(SysMenu)`` 在 Python 里没有重载，拆成两个类方法
:meth:`TreeSelect.of_dept` / :meth:`TreeSelect.of_menu`。两者的语义完全相同（取 id、
取名称、递归子节点），区别只是读哪两个属性。

``dept.getChildren().stream()`` 在 Java 里不会 NPE，因为 ``SysDept.children`` 初始化为
``new ArrayList<>()``；这里的 :class:`SysDept` 用 ``default_factory=list``，同样是列表。
"""

from __future__ import annotations

from typing import ClassVar, List, Optional, Tuple

from pydantic import Field

from app.common.core.domain.domain_model import DomainModel
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_menu import SysMenu


class TreeSelect(DomainModel):
    """下拉树结构 / one tree-select node."""

    #: 节点 ID（部门 ID / 菜单 ID）
    id: Optional[int] = None
    #: 节点名称（部门名称 / 菜单名称）
    label: Optional[str] = None
    #: 子节点 —— 空列表时整个键不输出（``@JsonInclude(NON_EMPTY)``）
    children: List["TreeSelect"] = Field(default_factory=list)

    _omit_when_empty: ClassVar[Tuple[str, ...]] = ("children",)

    # Java: public TreeSelect(SysDept dept)
    @classmethod
    def of_dept(cls, dept: SysDept) -> "TreeSelect":
        """把一个（已经挂好 ``children`` 的）部门节点转成下拉节点。"""
        return cls(
            id=dept.dept_id,
            label=dept.dept_name,
            children=[cls.of_dept(child) for child in dept.children],
        )

    # Java: public TreeSelect(SysMenu menu)
    @classmethod
    def of_menu(cls, menu: SysMenu) -> "TreeSelect":
        """把一个（已经挂好 ``children`` 的）菜单节点转成下拉节点。"""
        return cls(
            id=menu.menu_id,
            label=menu.menu_name,
            children=[cls.of_menu(child) for child in menu.children],
        )


TreeSelect.model_rebuild()

__all__ = ["TreeSelect"]
