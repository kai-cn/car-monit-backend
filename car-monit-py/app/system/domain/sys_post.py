"""岗位表 sys_post.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysPost.java

``SysPost`` 在 Java 里 ``extends BaseEntity``，所以 JSON 里同样携带
``createBy`` / ``createTime`` / ``updateBy`` / ``updateTime`` / ``remark``，以及
``@JsonInclude(NON_EMPTY)`` 的 ``params``（为空时不输出）。

``flag``
--------
``private boolean flag = false;`` 是**基本类型**，配合 ``isFlag()`` 让 Jackson 输出
``"flag": false``。它不落库，只表示"当前用户是否拥有该岗位"，由前端下拉框使用。
与 :class:`app.common.core.domain.entity.SysRole` 的同名字段一样，声明成
``bool = False`` 而不是 ``Optional[bool]``。

``POST_CONSTRAINTS``
--------------------
Java 把 ``@NotBlank`` / ``@Size`` 挂在 **getter** 上，由 ``SysPostController`` 的
``@Validated @RequestBody`` 触发。Python 侧把同一组约束放在实体旁边（同位置、同顺序），
由端点显式调用 :func:`app.common.utils.bean_validation.validate`。
注意 ``SysPost`` 的校验是**生效的**，而 :class:`SysUser` 的 ``@NotBlank`` / ``@Size``
在 Java 源码里被整段注释掉了 —— 两者不一样，不要"统一"掉。
"""

from __future__ import annotations

from typing import ClassVar, Optional, Tuple

from app.common.annotation.excel import ColumnType, Excel, ExcelFields
from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.domain_model import JavaString
from app.common.utils.bean_validation import Constraint, NotBlank, Size


class SysPost(BaseEntity):
    """岗位对象 sys_post / post."""

    #: 岗位序号
    post_id: Optional[int] = None
    #: 岗位编码
    post_code: Optional[str] = None
    #: 岗位名称
    post_name: Optional[str] = None
    #: 岗位排序 -- varchar 列，保持字符串（与 SysRole.roleSort / SysDept.orderNum 同理）
    post_sort: JavaString = None
    #: 状态（0正常 1停用）
    status: Optional[str] = None
    #: 用户是否存在此岗位标识，默认不存在（primitive boolean -> 恒定输出）
    flag: bool = False

    #: ``@Excel`` 注解表。``flag`` 不落库、不导出，所以只有这 5 列。
    #: 注意表头是 ``"状态"`` 而不是 ``"岗位状态"`` —— 与 Java 逐字一致。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        ("post_id", Excel(name="岗位序号", cell_type=ColumnType.NUMERIC)),
        ("post_code", Excel(name="岗位编码")),
        ("post_name", Excel(name="岗位名称")),
        ("post_sort", Excel(name="岗位排序")),
        ("status", Excel(name="状态", read_converter_exp="0=正常,1=停用")),
    )


#: Java ``SysPost`` getter 上的校验注解，**顺序与源码一致**
#: （``getPostCode`` -> ``getPostName`` -> ``getPostSort``），
#: 这个顺序决定了多字段同时违规时 ``getFieldError()`` 落在哪一条。
POST_CONSTRAINTS: Tuple[Constraint, ...] = (
    # Java: @NotBlank(message = "岗位编码不能为空") @Size(min = 0, max = 64, ...)
    NotBlank("post_code", "岗位编码不能为空"),
    Size("post_code", max=64, message="岗位编码长度不能超过64个字符"),
    # Java: @NotBlank(message = "岗位名称不能为空") @Size(min = 0, max = 50, ...)
    NotBlank("post_name", "岗位名称不能为空"),
    Size("post_name", max=50, message="岗位名称长度不能超过50个字符"),
    # Java: @NotBlank(message = "显示顺序不能为空") —— 没有 @Size
    NotBlank("post_sort", "显示顺序不能为空"),
)


__all__ = ["SysPost", "POST_CONSTRAINTS"]
