"""文件管理对象 sys_file.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/system/domain/SysFile.java

**不继承 ``BaseEntity``**
------------------------
Java 的 ``SysFile`` 是一个裸 POJO（只有 ``serialVersionUID``），没有 ``extends BaseEntity``，
所以：

* **没有** ``searchValue`` / ``remark`` / ``params`` 三件套 —— 请求体里带 ``params[beginTime]``
  也不会被绑定（前端这张表没有时间范围筛选）；
* 审计列的类型与 ``BaseEntity`` **相反**：``createUser`` / ``updateUser`` 是 ``String``，
  而 ``BaseEntity.updateBy`` 是 ``Long``。service 里写的是
  ``sysFile.setCreateUser(userId.toString())``，转换发生在**赋值那一刻**；
* 时间字段自带 ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``，与 ``BaseEntity`` 相同，
  但这里要自己声明（没有基类可继承）。

``id`` 序列化成**字符串**
-------------------------
::

    @JsonSerialize(using = ToStringSerializer.class)
    private Long id;

Snowflake id 有 19 位十进制数字，超过 JavaScript ``Number.MAX_SAFE_INTEGER``（16 位），
直接发数字前端会丢精度，所以 Jackson 把它写成字符串。**这是线上契约**：响应里
``"id": "1234567890123456789"``。Python 侧内部仍是 ``int``（要参与 SQL 的 id 比较），
只在序列化时转 ``str``。

``files`` / ``createUserName`` 是"临时字段"
-------------------------------------------
* ``files`` —— 前端把 base64 图片串放在这里（``uploadFileId`` 读它），**不落库**：
  XML 的 14 个插入列里没有它；
* ``createUserName`` —— 只由 ``selectSysFileByIds`` 的 ``left join sys_user`` 填，
  所以列表 / 按 id 查都拿不到这个值（是 ``null``）。

两个字段都带 ``@Excel``（``files`` 的注解名还写成了 ``"文件s"``），是 Excel 导出的列名。
``ExcelUtil`` 尚未迁移，见 ``COMPATIBILITY.md`` 的缺口表。
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Optional

from pydantic import BeforeValidator, field_serializer, field_validator

from app.common.core.domain.domain_model import DomainModel
from app.common.utils.json_utils import format_date_time, parse_date_time


def _empty_string_as_none(value: Any) -> Any:
    """Jackson 对包装类型收到空串时给的是 ``null``（``CoercionAction.AsNull``）。

    ``Long id`` / ``Long fileSize`` / ``Long tenantId`` 三个数值字段都要这一条：前端清空
    数字输入框时发的是 ``""``，Java 得到 ``null``，pydantic 默认会直接报错。
    """
    return None if value == "" else value


#: "Java 里是 ``Long``、但客户端可能发空串"的字段类型
JavaLong = Annotated[Optional[int], BeforeValidator(_empty_string_as_none)]


class SysFile(DomainModel):
    """文件管理对象 sys_file."""

    #: 编号 —— ``@JsonSerialize(using = ToStringSerializer.class)``
    id: JavaLong = None

    #: 文件名称（OSS 上的 key，UUID + 后缀）
    file_name: Optional[str] = None
    #: 上传包名
    bucket_name: Optional[str] = None
    #: 上传文件名称（用户设备的原始文件名，可能是中文）
    original: Optional[str] = None
    #: 文件类型（小写后缀）
    type: Optional[str] = None
    #: 文件大小（字节）
    file_size: JavaLong = None
    #: 业务类型
    buss_type: Optional[str] = None
    #: 业务名称（供应商代理证有效期等）
    buss_name: Optional[str] = None

    #: 创建时间 —— ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    create_time: Optional[datetime] = None
    #: 创建人 —— **String**（不是 ``BaseEntity`` 的 ``Long createBy``）
    create_user: Optional[str] = None

    #: 更新时间 —— ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    update_time: Optional[datetime] = None
    #: 更新人 —— **String**
    update_user: Optional[str] = None

    #: 删除标志（0 存在 1 删除）
    del_flag: Optional[str] = None
    #: 所属租户
    tenant_id: JavaLong = None

    #: 文件名称（前端上传 base64 用；**不落库**）
    files: Optional[str] = None
    #: 创建人姓名（只有 ``selectSysFileByIds`` 的 join 会填）
    create_user_name: Optional[str] = None

    # Java: getCreateTime()/getUpdateTime() 上的 @JsonFormat
    @field_serializer("create_time", "update_time")
    def _serialize_date_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        return format_date_time(value)

    @field_validator("create_time", "update_time", mode="before")
    @classmethod
    def _parse_date_time(cls, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        return parse_date_time(value)

    # Java: @JsonSerialize(using = ToStringSerializer.class) on ``id``
    @field_serializer("id")
    def _serialize_id(self, value: Optional[int], _info: Any) -> Optional[str]:
        return None if value is None else str(value)


__all__ = ["SysFile"]
