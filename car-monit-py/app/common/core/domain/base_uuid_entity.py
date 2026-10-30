"""UUID-keyed base entity (``sys_index_menu`` / flow / base tables).

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseUuidEntity.java

与 :class:`~app.common.core.domain.base_entity.BaseEntity` 的区别
-----------------------------------------------------------------
这是本工程里**第二条**实体基类。两者字段名高度重合，但类型和空值语义不同，不能互相替代：

    ==============  ====================  ==========================
    字段             BaseEntity            BaseUuidEntity
    ==============  ====================  ==========================
    主键            （无，各自声明 Long）  ``id``：**String**
    ``createBy``    ``String``            ``Long``
    ``updateBy``    ``String``            ``Long``
    ``createTime``  ``Date``              ``java.sql.Timestamp``
    额外字段        —                     ``epsId`` / ``delFlag`` /
                                          ``deptSubCode`` / ``tenantId`` /
                                          ``sort`` / ``remark``
    ``params``      有 ``@JsonInclude``    **没有** 注解
    ==============  ====================  ==========================

``BaseUuidEntity`` 服务于早期（非 RuoYi 原生）的业务表：主键是 UUID 字符串，审计人
是 ``Long``。照抄，不要"顺手"统一成 ``String``。

``params`` 在这里会输出 ``null``
--------------------------------
Java 只给 ``BaseEntity.params`` 挂了 ``@JsonInclude(NON_EMPTY)``；
``BaseUuidEntity.params`` 没有注解，因此序列化成 ``"params": null``。
所以本类**不**设置 ``_omit_when_empty``，与 :mod:`base_entity` 相反。

``searchValue`` 仍是 ``@JsonIgnore``
-----------------------------------
与 ``BaseEntity`` 同理（输入输出双向排除），复用同一套 ``before`` validator。

Java 里 ``BaseUuidEntity implements Serializable, CustomClass``。``CustomClass`` 是一个
空标记接口（无方法），Python 无对应物，不迁移。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import field_serializer, field_validator

from app.common.core.domain.domain_model import DomainModel
from app.common.utils.json_utils import format_date_time, parse_date_time


class BaseUuidEntity(DomainModel):
    """Entity 基类 / UUID-keyed base entity."""

    #: 主键（UUID 字符串）
    id: Optional[str] = None

    #: 创建人所在单位或科室
    eps_id: Optional[int] = None

    #: 删除标志（0 存在 1 删除）
    del_flag: Optional[str] = None

    #: 创建人（Java 是 ``Long``，不是用户名）
    create_by: Optional[int] = None

    #: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    create_time: Optional[datetime] = None

    #: 更新人（Java 是 ``Long``）
    update_by: Optional[int] = None

    #: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    update_time: Optional[datetime] = None

    #: 排序
    sort: Optional[int] = None

    #: 备注
    remark: Optional[str] = None

    #: 租户
    tenant_id: Optional[int] = None

    #: 部门编码
    dept_sub_code: Optional[str] = None

    #: 标志
    flag: Optional[str] = None

    #: 搜索值。**没有** ``@JsonIgnore`` —— 与 :class:`~app.common.core.domain.base_entity.BaseEntity`
    #: 不同，``BaseUuidEntity.searchValue`` 会作为 ``"searchValue": null`` 出现在响应里，
    #: 也接受请求体写入。（``BaseEntity`` 那份才带 ``@JsonIgnore``。）
    search_value: Optional[str] = None

    #: 请求参数。**没有** ``@JsonInclude(NON_EMPTY)`` —— 为 ``None`` 时会输出 ``"params": null``
    #: （与 :class:`~app.common.core.domain.base_entity.BaseEntity` 相反，那边为空时整个键消失）。
    params: Optional[Dict[str, Any]] = None

    # Java: getCreateTime()/getUpdateTime() carry @JsonFormat; the default Jackson
    # serialization would emit epoch millis, which the frontend cannot render.
    @field_serializer("create_time", "update_time")
    def _serialize_date_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        return format_date_time(value)

    @field_validator("create_time", "update_time", mode="before")
    @classmethod
    def _parse_date_time(cls, value: Any) -> Optional[datetime]:
        """Accept the ``@JsonFormat`` string, ISO-8601, a date, or epoch millis."""
        if value is None or value == "":
            return None
        return parse_date_time(value)

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: Any) -> Optional[str]:
        """Java 侧 ``id`` 是 ``String``，MyBatis 会把 ``bigint`` 主键自动转成字符串
        （``sys_index_menu.id`` 就是 bigint -> ``89`` 输出成 ``"89"``）。"""
        if value is None or isinstance(value, str):
            return value
        return str(value)


__all__ = ["BaseUuidEntity"]