# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/entity/SysUser.java
"""用户对象 sys_user / user account."""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, List, Optional

from pydantic import Field, computed_field, field_serializer, field_validator

from app.common.annotation.excel import ColumnType, Excel, ExcelFields, Type
from app.common.core.domain.base_entity import BaseEntity
from app.common.core.domain.entity.sys_dept import SysDept
from app.common.core.domain.entity.sys_role import SysRole
from app.common.utils.json_utils import format_iso_date_time, parse_date_time


class SysUser(BaseEntity):
    """Java: ``SysUser extends BaseEntity`` -- 40 declared fields.

    Three properties are easy to get wrong and were measured against Jackson 2.11.4:

    ``password``
        Java annotates ``getPassword()`` with ``@JsonIgnore`` **and** ``@JsonProperty``.
        That combination on a *getter* is write-only: the bcrypt hash is **never
        serialized** but is still accepted in a request body. (The same pair on a *field*
        behaves differently -- it serializes; ``SysUser`` puts it on the getter, so the
        hash stays inside the process.) Modelled with ``exclude=True``.

    ``admin``
        There is no ``admin`` field. ``public boolean isAdmin()`` makes Jackson emit a
        virtual ``"admin": true|false`` property in every payload. Reproduced with a
        computed field so response bodies stay byte-identical.

    ``loginDate``
        Unlike ``createTime``/``updateTime`` this field has **no** ``@JsonFormat``, so
        Jackson falls back to epoch milliseconds as a *number* (``1761225909123``),
        not an ISO string. See :mod:`app.common.utils.json_utils`.
    """

    user_id: Optional[int] = None
    user_no: Optional[int] = None
    dept_id: Optional[int] = None
    #: 用户账号 -- note the capital N: Java's field is ``userName``, JSON key ``userName``.
    user_name: Optional[str] = None
    #: 用户昵称
    nick_name: Optional[str] = None
    #: 用户类型（1机构用户2专家3供应商）
    user_type: Optional[str] = None
    email: Optional[str] = None
    #: Java spells it ``phonenumber`` (one word) -- the JSON key is not ``phoneNumber``.
    phonenumber: Optional[str] = None
    #: 用户性别（0男 1女 2未知）
    sex: Optional[str] = None
    avatar: Optional[str] = None

    #: Write-only: ``@JsonIgnore`` + ``@JsonProperty`` on the getter.
    password: Optional[str] = Field(default=None, exclude=True)
    #: Write-only confirmation field, used only by the profile/password endpoints.
    confirm_password: Optional[str] = None
    #: 盐加密 -- the column still exists in the schema even though bcrypt no longer uses it.
    salt: Optional[str] = None
    #: 帐号状态（0正常 1停用）
    status: Optional[str] = None
    #: 删除标志（0代表存在 2代表删除）
    del_flag: Optional[str] = None
    login_ip: Optional[str] = None
    #: No ``@JsonFormat`` in Java -> Jackson's ``StdDateFormat`` ISO text.
    login_date: Optional[datetime] = None
    #: 证书编号
    cert_id: Optional[str] = None
    #: 证书实体编号
    cert_entity_id: Optional[str] = None
    #: 业务id（userType=2 时为专家id，=3 时为供应商注册id）
    buss_id: Optional[str] = None
    buss_name: Optional[str] = None
    eps_name: Optional[str] = None
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    #: 角色编码
    role_code: Optional[str] = None

    #: 部门对象（关联查询时填充）
    dept: Optional[SysDept] = None
    #: 角色对象（关联查询时填充）
    roles: Optional[List[SysRole]] = None
    #: 角色组 -- arrives as a JSON array of ids from the user form.
    role_ids: Optional[List[int]] = None
    #: 岗位组
    post_ids: Optional[List[int]] = None
    flag: Optional[str] = None
    data_id: Optional[str] = None
    #: 部门对应的 code
    sub_code: Optional[str] = None
    #: 查询条件-用户昵称
    query_nick_name: Optional[str] = None
    #: 是否排除自己
    exclude_self: Optional[bool] = None
    #: 需要排除的数据集合
    exclude_id: Optional[int] = None
    #: 是否是总公司的人员（true 是；false/null 不是）
    head_office: Optional[bool] = None
    #: 是否是采购经理（true 是；false/null 不是）
    procurement_manager: Optional[bool] = None
    #: 部门名称（平铺字段，与 ``dept.deptName`` 并存）
    dept_name: Optional[str] = None
    #: 密码判断flag -- Java ``private int``, i.e. primitive: never null, defaults to 0.
    pj_flag: int = 0
    #: 用户签名图片文件id
    image_id: Optional[str] = None

    #: ``@Excel`` / ``@Excels`` 注解表，**顺序与 Java 字段声明顺序逐字一致**。
    #:
    #: 一共 21 个被注解的字段，其中 ``dept`` 挂的是 ``@Excels``（两个子属性），
    #: 展开后共 22 列 —— ``ExcelUtil#getFields()`` 在 Java 侧同样会把它摊平成两条，
    #: 所以两侧的列数、列序、表头文案完全一致。
    #:
    #: ``userType`` 的 ``readConverterExp`` 只有一个 ``=``（``1=机构用户2专家3供应商``），
    #: 这是 Java 源码里的原样，不是笔误 —— 后果是导出时只有 ``"1"`` 会被翻译成
    #: ``"机构用户2专家3供应商"``，其余值原样输出。见 COMPATIBILITY §37。
    EXCEL_FIELDS: ClassVar[ExcelFields] = (
        (
            "user_id",
            Excel(name="用户序号", cell_type=ColumnType.NUMERIC, prompt="用户编号"),
        ),
        (
            "user_no",
            Excel(name="用户编码", cell_type=ColumnType.NUMERIC, prompt="用户编码"),
        ),
        # 只导入不导出：导入用户时靠它定位部门
        ("dept_id", Excel(name="部门编号", type=Type.IMPORT)),
        ("user_name", Excel(name="登录名称")),
        ("nick_name", Excel(name="用户名称")),
        ("user_type", Excel(name="用户类型", read_converter_exp="1=机构用户2专家3供应商")),
        ("email", Excel(name="用户邮箱")),
        ("phonenumber", Excel(name="手机号码")),
        ("sex", Excel(name="用户性别", read_converter_exp="0=男,1=女,2=未知")),
        ("status", Excel(name="帐号状态", read_converter_exp="0=正常,1=停用")),
        ("login_ip", Excel(name="最后登录IP", type=Type.EXPORT)),
        (
            "login_date",
            Excel(
                name="最后登录时间",
                width=30,
                date_format="yyyy-MM-dd HH:mm:ss",
                type=Type.EXPORT,
            ),
        ),
        ("cert_id", Excel(name="证书Id")),
        ("cert_entity_id", Excel(name="证书实体Id")),
        ("buss_id", Excel(name="业务id")),
        ("buss_name", Excel(name="业务名称")),
        ("eps_name", Excel(name="单位名称")),
        ("tenant_id", Excel(name="租户单位id")),
        ("tenant_name", Excel(name="租户单位名称")),
        ("role_code", Excel(name="角色编码")),
        # Java: @Excels({@Excel(...), @Excel(...)}) private SysDept dept;
        ("dept", Excel(name="部门名称", target_attr="dept_name", type=Type.EXPORT)),
        ("dept", Excel(name="部门负责人", target_attr="leader", type=Type.EXPORT)),
    )

    @field_serializer("login_date")
    def _serialize_login_date(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        """No ``@JsonFormat`` in Java -> ``"2024-05-17T14:15:52.000+08:00"``."""
        return format_iso_date_time(value)

    @field_validator("login_date", mode="before")
    @classmethod
    def _parse_login_date(cls, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        return parse_date_time(value)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def admin(self) -> bool:
        """Java: ``public boolean isAdmin()`` -> ``userId != null && 1L == userId``.

        A virtual Jackson property, not a column. Emitted in every user payload.
        """
        return self.user_id is not None and self.user_id == 1

    @staticmethod
    def is_admin(user_id: Optional[int]) -> bool:
        """Java: ``public static boolean isAdmin(Long userId)``."""
        return user_id is not None and user_id == 1


__all__ = ["SysUser"]
