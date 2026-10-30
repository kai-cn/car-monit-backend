# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysRole.java
"""角色对象 sys_role / role."""

from __future__ import annotations

from typing import ClassVar, List, Optional, Tuple

from pydantic import computed_field

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.domain_model import JavaString
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysRole(BaseEntity):
    """Java: ``SysRole extends BaseEntity``.

    ``menuCheckStrictly`` / ``deptCheckStrictly`` / ``flag`` are **primitive** ``boolean``
    in Java, so they are never ``null`` and always appear in the JSON
    (``{"flag":false,"menuCheckStrictly":false}`` -- measured). Declaring them
    ``Optional[bool]`` here would add ``null`` values Java never emits.
    """

    role_id: Optional[int] = None
    role_name: Optional[str] = None
    role_key: Optional[str] = None
    #: varchar column despite the "sort" name -- keep it a string.
    role_sort: JavaString = None
    #: 数据范围（1全部数据权限 2自定数据权限 3本部门数据权限 4本部门及以下数据权限）
    data_scope: Optional[str] = None
    #: primitive boolean -> always present, defaults to false
    menu_check_strictly: bool = False
    #: primitive boolean -> always present, defaults to false
    dept_check_strictly: bool = False
    status: Optional[str] = None
    del_flag: Optional[str] = None
    #: primitive boolean initialised to false in Java
    flag: bool = False
    menu_ids: Optional[List[int]] = None
    dept_ids: Optional[List[int]] = None

    #: ``@Excel`` 注解表。``menuCheckStrictly`` / ``deptCheckStrictly`` / ``delFlag``
    #: 在 Java 里没有注解，所以只有这 6 列。
    #:
    #: ``roleSort`` 实际是 varchar（见上面的 ``JavaString``），但 ``@Excel`` 没写
    #: ``cellType``，默认 ``STRING`` —— 与类定义一致，不需要特殊处理。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("role_id", Excel(name="角色序号", cell_type=ColumnType.NUMERIC)),
        ("role_name", Excel(name="角色名称")),
        ("role_key", Excel(name="角色权限")),
        ("role_sort", Excel(name="角色排序")),
        (
            "data_scope",
            Excel(
                name="数据范围",
                read_converter_exp=(
                    "1=所有数据权限,2=自定义数据权限,3=本部门数据权限,4=本部门及以下数据权限"
                ),
            ),
        ),
        ("status", Excel(name="角色状态", read_converter_exp="0=正常,1=停用")),
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin(self) -> bool:
        """Java: ``public boolean isAdmin()`` -> ``1L == roleId``.

        与 ``SysUser.admin`` 同理：Java 在**实例方法**上没有 ``@JsonIgnore``，
        Jackson 会把它当成一个虚拟属性输出，所以每个角色 JSON 都带 ``"admin"``。
        名字从 ``is_admin`` 改成 ``admin`` 是因为 Python 里不能既定义同名的
        实例方法与静态方法（静态版见 :meth:`is_admin`）。
        """
        return self.role_id is not None and self.role_id == 1

    @staticmethod
    def is_admin(role_id: Optional[int]) -> bool:
        """Java: ``public static boolean isAdmin(Long roleId)``."""
        return role_id is not None and role_id == 1


#: Java ``SysRole`` getter 上的校验注解，**顺序与源码一致**
#: （``getRoleName`` -> ``getRoleKey`` -> ``getRoleSort``），这个顺序决定了
#: 多字段同时违规时客户端看到哪一条文案。
#:
#: 只有 ``add`` / ``edit`` 会触发（``@Validated @RequestBody``）；
#: ``dataScope`` / ``changeStatus`` 是裸 ``@RequestBody``，**不校验** ——
#: 所以只传 ``{"roleId": 2, "status": "1"}`` 改状态是合法的。
ROLE_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "角色名称不能为空") @Size(min = 0, max = 30, ...)
    NotBlank("role_name", "角色名称不能为空"),
    Size("role_name", max=30, message="角色名称长度不能超过30个字符"),
    # Java: @NotBlank(message = "权限字符不能为空") @Size(min = 0, max = 100, ...)
    NotBlank("role_key", "权限字符不能为空"),
    Size("role_key", max=100, message="权限字符长度不能超过100个字符"),
    # Java: @NotBlank(message = "显示顺序不能为空") —— 没有 @Size
    NotBlank("role_sort", "显示顺序不能为空"),
)


__all__ = ["SysRole", "ROLE_CONSTRAINTS"]
