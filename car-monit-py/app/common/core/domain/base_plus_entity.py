"""MyBatis-Plus 实体基类（``base`` / ``manager`` / ``flow`` 三个包在用）。

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BasePlusEntity.java

与另外两个实体基类的区别
------------------------
::

    ==============  ====================  ====================  ======================
    字段             BaseEntity            BaseUuidEntity         BasePlusEntity
    ==============  ====================  ====================  ======================
    主键            （无）                ``id``: String         ``id``: String（UUID）
    ``createBy``    String                Long                  Long
    ``createTime``  Date                  Timestamp             Timestamp
    额外字段        ``remark`` /          ``remart`` 等 +        ``epsId`` / ``delFlag`` /
                    ``params``            ``deptSubCode``       ``sort`` / ``tenantId``
    ``params``      有 ``@JsonInclude``   **没有**              **根本没有这个字段**
    ==============  ====================  ====================  ======================

三点必须照抄的地方：

1. ``delFlag`` 只有 ``@TableField(select = false)`` —— 那是"查不回来"，**不是**
   ``@JsonIgnore``。Jackson 照样会输出 ``"delFlag": null``，前端能看到这个键。
2. 没有 ``params`` / ``remark`` / ``searchValue`` —— 所以这一族实体的列表接口
   **收不到** ``params[beginTime]`` 这类区间条件，查询条件只能是实体自有的列。
3. ``createTime`` / ``updateTime`` 是 ``java.sql.Timestamp`` 且带
   ``@JsonFormat("yyyy-MM-dd HH:mm:ss")`` -> 序列化成字符串，不是 epoch 毫秒。

``@Accessors(chain = true)``（setter 返回 ``this``）与 ``implements CustomClass``
（空标记接口）在 Python 无对应物，不迁移。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Optional

from pydantic import field_serializer, field_validator

from app.common.core.domain.domain_model import DomainModel
from app.common.utils.json_utils import format_date_time, parse_date_time


class BasePlusEntity(DomainModel):
    """Entity 基类 / MyBatis-Plus base entity."""

    #: ``@TableId(value = "id", type = ...)`` —— 供 ``PlusMapper`` 生成主键用。
    #: 默认 ``ASSIGN_UUID``；兄弟基类按 Java 原文各自覆盖（见文件尾部）。
    id_type: ClassVar[str] = "ASSIGN_UUID"

    #: 主键. Java: ``@TableId(value = "id", type = IdType.ASSIGN_UUID)``
    #: —— 32 位无连字符 hex，由 ``insert`` 时生成（见 ``app.base.mapper.plus_mapper``）。
    id: Optional[str] = None

    #: 创建人所在单位或科室. Java: ``@TableField(value = "eps_id", fill = INSERT)``
    eps_id: Optional[int] = None

    #: 删除标志（0 存在 1 删除）. Java: ``@TableLogic(value = "0", delval = "1")`` +
    #: ``@TableField(value = "del_flag", select = false)``
    del_flag: Optional[str] = None

    #: 创建人（``Long`` 用户id，不是用户名）
    create_by: Optional[int] = None

    #: 创建时间. Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    create_time: Optional[datetime] = None

    #: 更新人（``Long``）
    update_by: Optional[int] = None

    #: 更新时间. Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    update_time: Optional[datetime] = None

    #: 排序
    sort: Optional[int] = None

    #: 租户
    tenant_id: Optional[int] = None

    @field_serializer("create_time", "update_time")
    def _serialize_date_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        """Java: ``@JsonFormat`` —— 默认 Jackson 会输出 epoch 毫秒，前端渲染不了。"""
        return format_date_time(value)

    @field_validator("create_time", "update_time", mode="before")
    @classmethod
    def _parse_date_time(cls, value: Any) -> Optional[datetime]:
        """接受 ``@JsonFormat`` 字符串、ISO-8601、日期对象或 epoch 毫秒。"""
        if value is None or value == "":
            return None
        return parse_date_time(value)


class BasePlusEntityNew(BasePlusEntity):
    """Java: ``com.ruoyi.common.core.domain.BasePlusEntityNew``.

    字段与 :class:`BasePlusEntity` **逐字相同**（连 ``ASSIGN_UUID`` 都一样），
    Java 侧只是复制了一份类。为了 ``instanceof`` 与注释可读性保留同名子类，
    行为零差异 —— 不要在这里加字段。
    """

    id_type: ClassVar[str] = "ASSIGN_UUID"


class BasePlusEntityInput(BasePlusEntity):
    """Java: ``BasePlusEntityInput`` —— ``@TableId(type = IdType.INPUT)``.

    主键由调用方给，``insert`` **不**生成 UUID；没给主键就写 ``null``
    （与 MP 一致，不是报错）。
    """

    id_type: ClassVar[str] = "INPUT"


class BasePlusEntityInputNew(BasePlusEntity):
    """Java: ``BasePlusEntityInputNew`` —— 与 :class:`BasePlusEntityInput` 同字段同主键策略."""

    id_type: ClassVar[str] = "INPUT"


class BasePlusEntityLong(BasePlusEntity):
    """Java: ``BasePlusEntityLong`` —— ``@TableId(type = IdType.ASSIGN_ID)``（19 位雪花号）."""

    id_type: ClassVar[str] = "ASSIGN_ID"


__all__ = [
    "BasePlusEntity",
    "BasePlusEntityInput",
    "BasePlusEntityInputNew",
    "BasePlusEntityLong",
    "BasePlusEntityNew",
]
