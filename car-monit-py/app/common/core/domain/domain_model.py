"""Base class for every Java "domain object" that crosses the HTTP boundary.

# Migrated from: com.ruoyi.common.core.domain.BaseEntity (protocol side only)

Java relies on Jackson annotations to shape JSON. The same rules are attached once,
here, so each entity only has to declare its fields:

    ============================  ===========================================
    Java annotation               Python equivalent
    ============================  ===========================================
    (implicit getter name)        ``alias_generator=to_camel`` -> ``userId``
    ``@JsonIgnore``               ``Field(exclude=True)``
    ``@JsonInclude(NON_EMPTY)``   name listed in ``_omit_when_empty``
    ``@JsonFormat``               a ``field_serializer`` on the entity
    ``@JsonProperty``             ``populate_by_name=True`` (accepts the alias)
    ============================  ===========================================

Field order
-----------
Jackson emits superclass fields first because ``AnnotatedFieldCollector`` walks the
hierarchy from the root down. Pydantic also emits parent-class fields first, so the two
agree without extra work. Measured against the running ``ruoyi-admin.jar``::

    {"createTime":"2021-05-06 00:36:41","userName":"admin","email":null,
     "loginDate":"2024-05-17T14:15:52.000+08:00"}

Unknown-property handling
-------------------------
``extra="ignore"`` mirrors Spring Boot, which disables Jackson's
``FAIL_ON_UNKNOWN_PROPERTIES``. Java would answer HTTP 200 with the *ignored* field
silently dropped, not a 400 -- so the same tolerance is required here.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, ClassVar, Dict, Optional, Tuple

from pydantic import BaseModel, BeforeValidator, ConfigDict, model_serializer
from pydantic.alias_generators import to_camel


def decimal_to_java_number(value: Decimal) -> Any:
    """``BigDecimal`` -> JSON 数字。Java: Jackson ``NumberSerializer``.

    Jackson 把 ``BigDecimal`` 写成**数字**并**保留标度**：``BigDecimal.ZERO`` 输出 ``0``、
    ``new BigDecimal("12.00")`` 输出 ``12.00``。Python 只能用内置数值近似：

    * 标度 ``>= 0``（``BigDecimal.ZERO``、整型列）-> ``int``，得到 ``0`` / ``1234``；
    * 其余 -> ``float``，``1334.23`` 原样输出。

    之所以不能一律 ``float``：``Decimal("0")`` 会变成 ``0.0``，而 Java 是 ``0`` —— 前端
    ``v-if="amount"`` 之类的判断不受影响，但逐字节比对整张列表的每个金额都会差一格。
    ``12.00`` 的尾零仍然无法保留（``float`` 没有标度概念），这一条记录在 COMPATIBILITY.md。
    """
    if value.as_tuple().exponent >= 0:
        return int(value)
    return float(value)


class DomainModel(BaseModel):
    """Java: any bean serialized by Jackson with the project's annotation set."""

    model_config = ConfigDict(
        # Java: getUserId() -> "userId". Applied to every field unless overridden.
        alias_generator=to_camel,
        # Accept both "userId" (wire) and "user_id" (Python) on input.
        populate_by_name=True,
        # Spring Boot disables FAIL_ON_UNKNOWN_PROPERTIES, so unknown keys are ignored.
        extra="ignore",
        # Do not touch the payload: Jackson does not strip whitespace either.
        str_strip_whitespace=False,
        validate_assignment=False,
        # Rows arriving from SQLAlchemy are mappings, not attributes.
        from_attributes=True,
        # Java: a ``BigDecimal`` property is written by Jackson as a JSON **number**
        # (``"chargeAmount":12.00``), never as a quoted string. pydantic's own JSON mode
        # would emit ``"12.00"`` -- a string -- which breaks every arithmetic use on the
        # frontend. 标度保留见 :func:`decimal_to_java_number`，残余差异记录在 COMPATIBILITY.md。
        json_encoders={Decimal: decimal_to_java_number},
    )

    #: Field names whose value must be dropped when empty -- Java ``@JsonInclude(NON_EMPTY)``.
    #: ``NON_EMPTY`` removes ``null``, ``""`` and empty collections/maps alike.
    _omit_when_empty: ClassVar[Tuple[str, ...]] = ()

    @model_serializer(mode="wrap")
    def _apply_non_empty_inclusion(self, handler: Any) -> Dict[str, Any]:
        """Drop ``NON_EMPTY`` fields after normal serialization.

        Implemented as a wrap-serializer (not a per-call filter) so the behaviour also
        applies to entities nested inside another one -- e.g. ``SysUser.params`` reaches
        the client through ``AjaxResult`` -> ``SysUser`` -> ``BaseEntity``.
        """
        data = handler(self)
        if not self._omit_when_empty:
            return data
        fields = type(self).model_fields
        for name in self._omit_when_empty:
            field = fields.get(name)
            if field is None:
                continue
            key = field.alias or name
            if key in data and not data[key]:
                # Java ``NON_EMPTY``: null, "", empty array, empty map are all omitted.
                del data[key]
        return data

    def to_json_dict(self) -> Dict[str, Any]:
        """Serialize with Java's property names and Java's value shapes."""
        return self.model_dump(by_alias=True, mode="json")

    def field(self, alias: str) -> Any:
        """Read a value by its **Java** property name (``"userId"`` rather than ``user_id``).

        MyBatis XML and the frontend both speak Java names; keeping this lookup in one
        place avoids scattering ``getattr(model, to_snake(alias))`` around the mappers.
        """
        for name, info in type(self).model_fields.items():
            if (info.alias or name) == alias:
                return getattr(self, name)
        raise AttributeError(f"{type(self).__name__} has no property {alias!r}")


class OptionalModel(DomainModel):
    """Marker for models whose fields are all optional (Java has no such distinction)."""

    @classmethod
    def empty(cls) -> "OptionalModel":
        return cls()


def _coerce_to_java_string(value: Any) -> Any:
    """Java ``StringDeserializer`` 的标量强制转换。

    Jackson 默认允许标量互转（``CoercionAction.TryConvert``）：给一个声明为 ``String``
    的字段传 ``1`` 或 ``true``，Java 拿到的是 ``"1"`` / ``"true"``，**不会**报错。
    pydantic v2 默认拒绝 ``int -> str``，于是前端用 ``el-input-number`` 绑定的
    ``postSort`` / ``roleSort`` / ``orderNum`` 会被当成参数校验失败（``code 500``）。

    数组/对象不在这里处理，继续交给 pydantic 报错（Java 侧同样反序列化失败）。
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return value


#: “Java 里是 ``String``、但客户端可能发数字”的字段类型（对应 Jackson 的标量强制转换）。
JavaString = Annotated[Optional[str], BeforeValidator(_coerce_to_java_string)]


__all__ = ["DomainModel", "OptionalModel", "JavaString", "to_camel", "Optional"]
