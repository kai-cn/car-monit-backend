# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysDept.java
"""部门对象 sys_dept / department (tree node).

``DEPT_CONSTRAINTS``
--------------------
Java 把 ``@NotBlank`` / ``@Size`` / ``@Email`` 挂在 **getter** 上，由
``SysDeptController`` 的 ``@Validated @RequestBody`` 触发。Python 侧把同一组约束放在
实体旁边（同位置、同顺序），由端点显式调用
:func:`app.common.utils.bean_validation.validate`。

**四项约束，不是五个字段都有约束**：``leader`` / ``bankName`` / ``account`` /
``socialCode`` / ``postalCode`` / ``address`` 在 Java 上**没有任何注解**，所以它们可以
随便空着 —— 不要看到 ``@Size`` 就“补全”到所有字符串字段。
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import Field

from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.domain_model import JavaString
from app.common.utils.bean_validation import Constraint, Email, NotBlank, Size


class SysDept(BaseEntity):
    """Java: ``SysDept extends BaseEntity`` (40 column-mapped fields included).

    Two things differ from the upstream RuoYi 3.8.7 class and must not be "tidied up":
      * ``orderNum`` is a **String**, not an Integer -- the table column is ``varchar``.
      * ``treeLeavel`` keeps Java's spelling (``Leavel``, not ``Level``); it is a column
        name and a JSON key the frontend reads.
    """

    dept_id: Optional[int] = None
    parent_id: Optional[int] = None
    #: 祖级列表, e.g. ``"0,100,101"``
    ancestors: Optional[str] = None
    dept_name: Optional[str] = None
    #: varchar 列。客户端可能传数字（``el-input-number``），按 Jackson 的标量强制转换收下。
    order_num: JavaString = None
    leader_id: Optional[int] = None
    leader: Optional[str] = None
    fgld_id: Optional[int] = None
    fgld_name: Optional[str] = None
    bank_name: Optional[str] = None
    account: Optional[str] = None
    social_code: Optional[str] = None
    postal_code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    #: 部门状态:0正常,1停用
    status: Optional[str] = None
    #: 是否有招标资格(0否1是)
    is_zbzg: Optional[str] = None
    #: 是否是单位(0否1是)
    is_uint: Optional[str] = None
    #: 树级别 -- Java spells it "Leavel"; the column and JSON key keep that spelling.
    tree_leavel: Optional[int] = None
    sub_code: Optional[str] = None
    dept_jc: Optional[str] = None
    del_flag: Optional[str] = None
    parent_name: Optional[str] = None
    #: Java initialises this to ``new ArrayList<>()``, so a fresh node serializes as ``[]``
    #: rather than ``null`` -- and ``@JsonInclude`` is NOT applied, so ``[]`` is emitted.
    children: List["SysDept"] = Field(default_factory=list)
    tenant_id: Optional[int] = None
    flag: Optional[str] = None
    data_id: Optional[str] = None
    #: 查询下面子节点包括自己
    dept_sub_code: Optional[str] = None


SysDept.model_rebuild()

#: Java ``SysDept`` getter 上的校验注解，**顺序与源码一致**
#: （``getDeptName`` -> ``getOrderNum`` -> ``getPhone`` -> ``getEmail``）。
#: 这个顺序决定了多字段同时违规时 ``getFieldError()`` 落在哪一条。
DEPT_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "部门名称不能为空") @Size(min = 0, max = 30, ...)
    NotBlank("dept_name", "部门名称不能为空"),
    Size("dept_name", max=30, message="部门名称长度不能超过30个字符"),
    # Java: @NotBlank(message = "显示顺序不能为空") —— 没有 @Size
    NotBlank("order_num", "显示顺序不能为空"),
    # Java: @Size(min = 0, max = 11, message = "联系电话长度不能超过11个字符")
    Size("phone", max=11, message="联系电话长度不能超过11个字符"),
    # Java: @Email(message = "邮箱格式不正确") @Size(min = 0, max = 50, ...)
    Email("email", "邮箱格式不正确"),
    Size("email", max=50, message="邮箱长度不能超过50个字符"),
)


__all__ = ["SysDept", "DEPT_CONSTRAINTS"]
