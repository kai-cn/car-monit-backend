"""Base entity shared by every RuoYi table-backed domain object.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/core/domain/BaseEntity.java

Field-by-field mapping (JSON names are Java's, and are what the frontend sees):

    Java field      JSON key       Python attribute   Notes
    --------------  -------------  -----------------  -----------------------------------
    searchValue     (absent)       search_value       @JsonIgnore -> never (de)serialized
    createBy        createBy       create_by
    createTime      createTime     create_time        @JsonFormat "yyyy-MM-dd HH:mm:ss"
    updateBy        updateBy       update_by
    updateTime      updateTime     update_time        @JsonFormat "yyyy-MM-dd HH:mm:ss"
    remark          remark         remark
    params          params         params             @JsonInclude(NON_EMPTY) -> omitted when {}

``searchValue`` deserves a warning: it is ``@JsonIgnore``d, so a client **cannot** set it
through the request body. The value is only ever set by server-side code (it drives the
``${params.dataScope}`` substitution in the MyBatis XML). Keep it excluded on input too --
letting a request populate it would be a privilege-escalation vector.

``params`` is how the Java frontend passes date ranges: Spring's ``WebDataBinder`` turns
``?params[beginTime]=2025-01-01`` into ``params.put("beginTime", ...)``. FastAPI has no
such binding, so the query-string adapter in the controller layer has to rebuild the map.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar, Dict, Optional, Tuple

from pydantic import Field, field_serializer, field_validator

from app.common.core.domain.domain_model import DomainModel
from app.common.utils.json_utils import format_date_time, parse_date_time


class BaseEntity(DomainModel):
    """Entity基类 / base entity."""

    #: Java: ``@JsonIgnore private String searchValue`` -- excluded in **both** directions.
    search_value: Optional[str] = Field(default=None, exclude=True)

    create_by: Optional[str] = None

    #: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    create_time: Optional[datetime] = None

    update_by: Optional[str] = None

    #: Java: ``@JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")``
    update_time: Optional[datetime] = None

    remark: Optional[str] = None

    #: Java: ``@JsonInclude(JsonInclude.Include.NON_EMPTY)`` -- see ``_omit_when_empty``.
    params: Dict[str, Any] = Field(default_factory=dict)

    _omit_when_empty: ClassVar[Tuple[str, ...]] = ("params",)

    # Java: getCreateTime()/getUpdateTime() carry @JsonFormat; the default Jackson
    # serialization would emit epoch millis, which the frontend cannot render.
    @field_serializer("create_time", "update_time")
    def _serialize_date_time(self, value: Optional[datetime], _info: Any) -> Optional[str]:
        return format_date_time(value)

    @field_validator("search_value", mode="before")
    @classmethod
    def _ignore_search_value_from_input(cls, value: Any) -> None:
        """Java: ``@JsonIgnore`` blocks deserialization too, not just serialization.

        ``Field(exclude=True)`` alone is only half of that: it drops the field from the
        output but would still let a request body populate it. ``searchValue`` feeds the
        ``${params.dataScope}`` splice in the MyBatis XML, so accepting it from a client
        would let a caller inject its own data-scope predicate. Input is discarded; only
        server-side code may set the attribute.
        """
        return None

    @field_validator("create_time", "update_time", mode="before")
    @classmethod
    def _parse_date_time(cls, value: Any) -> Optional[datetime]:
        """Accept the ``@JsonFormat`` string, ISO-8601, a date, or epoch millis."""
        if value is None or value == "":
            return None
        return parse_date_time(value)


__all__ = ["BaseEntity"]
