"""JSON value serializer for the Redis template.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/FastJson2JsonRedisSerializer.java

Java original
-------------
``RedisTemplate<Object, Object>`` with ``StringRedisSerializer`` keys and this serializer
for values. ``serialize`` is::

    JSON.toJSONString(t, JSONWriter.Feature.WriteClassName).getBytes(UTF-8)

``WriteClassName`` is what makes the round-trip possible: the payload carries a
``"@type"`` key naming the concrete Java class, and ``deserialize`` does
``JSON.parseObject(str, Object.class, autoTypeFilter)`` -- so the class is restored from
the payload, never from the caller. A value therefore survives a cache read by a
*different* JVM process with a different heap layout.

Python equivalent
-----------------
:meth:`FastJson2JsonRedisSerializer.serialize` emits the same shape -- camelCase property
names plus a top-level ``"@type"`` -- and :meth:`deserialize` resolves ``"@type"`` through
:data:`TYPE_REGISTRY`. Three consequences worth knowing:

1. **A Java process can read Python-written values and vice versa**, which is required
   during the cut-over (an admin who logged in against the Java build must stay logged in
   after the switch). This is why ``pickle`` was rejected in
   :mod:`app.config.redis_config`.
2. **``null`` serializes to zero bytes**, and zero bytes deserialize to ``None`` -- that
   is literally what the Java methods do, and ``RedisTemplate`` then treats the value as
   absent.
3. **The bcrypt hash IS present in the cached payload.** fastjson2 ignores Jackson's
   ``@JsonIgnore``, so ``SysUser.password`` is written to Redis even though it is excluded
   from HTTP responses. Reproduced here for byte-level interoperability; Redis is not
   reachable by clients.

Unregistered ``@type`` values are returned as plain ``dict`` rather than raising: fastjson2
with an ``autoTypeFilter`` also degrades instead of failing when the class is not on the
whitelist (``Constants.JSON_WHITELIST_STR`` = ``org.springframework``, ``com.ruoyi``).

Reading Java-written payloads -- fastjson2 is *not* strict JSON
---------------------------------------------------------------
``WriteClassName`` makes fastjson2 emit a **dialect** that ``json.loads`` rejects:

* a numeric *type suffix* on primitives -- ``"carNum":2L``, ``"createBy":1L``,
  ``"epsId":25367L`` (``L`` long, ``S`` short, ``B`` byte, ``F`` float, ``D`` double);
* a *collection wrapper* naming the concrete class -- ``"permissions":Set["*:*:*"]``,
  ``List[...]``, ``Collection[...]``.

Both appear in caches this project already ships from previous runs of the Java build
(``car_list`` is the big one), so :func:`parse_fastjson2_text` normalises the text before
``json.loads`` sees it. Python-written values are ordinary JSON, which fastjson2 parses
without complaint -- the tolerance is only needed in this direction.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, Type

from app.common.core.domain.entity.sys_user import SysUser
from app.common.core.domain.model.login_user import LoginUser
from app.common.utils.json_utils import to_jsonable
from app.manager.domain.car_info import CarInfo

logger = logging.getLogger("app.framework.config.redis_serializer")

#: Java fully-qualified class name -> Python class. Mirrors the ``com.ruoyi`` half of
#: ``Constants.JSON_WHITELIST_STR``; only classes that are genuinely cached are listed.
TYPE_REGISTRY: Dict[str, Type[Any]] = {
    "com.ruoyi.common.core.domain.model.LoginUser": LoginUser,
    "com.ruoyi.common.core.domain.entity.SysUser": SysUser,
    #: ``Constants.car_list`` —— 全量重点车辆，185 条，每条都带 ``@type``。Java 侧的类型是
    #: ``List<CarInfo>``，``carLocation`` 直接读 ``carInfo.getStatus()``；不登记就会被反序列化
    #: 成 dict，随后 ``'dict' object has no attribute 'status'``。
    "com.ruoyi.manager.domain.CarInfo": CarInfo,
}

#: Reverse lookup used by :meth:`serialize`.
_JAVA_TYPE_NAMES: Dict[Type[Any], str] = {value: key for key, value in TYPE_REGISTRY.items()}

#: Key fastjson2 uses for the class name.
TYPE_KEY = "@type"

#: Primitive *type suffixes* fastjson2 appends under ``WriteClassName``: ``2L``, ``1S``,
#: ``3B``, ``1.5F``, ``2.5D``. Lower case appears too (``1d`` from ``BigDecimal``? no --
#: from ``double`` under some writers), so both cases are stripped.
_NUMBER_SUFFIXES = frozenset("LlSsBbFfDd")

#: What may legally follow a JSON number; a suffix is only stripped before these.
_NUMBER_TERMINATORS = frozenset(",}] \t\r\n")

#: Where a *collection wrapper* may legally start: at the beginning of the document, or
#: right after a structural character. ``"a":1,"b":Set[...]`` / ``[{...},Set[...]]``.
_WRAPPER_STARTS = frozenset((",", ":", "[", "{", ""))


class SerializationError(RuntimeError):
    """Java: ``org.springframework.data.redis.serializer.SerializationException``."""


def _normalize_fastjson2_text(text: str) -> str:
    """Rewrite the ``WriteClassName`` dialect into strict JSON. See module docstring.

    A single pass, string-aware: nothing inside a ``"..."`` literal is ever touched, so a
    ``@type`` value or a remark that happens to contain ``2L`` survives verbatim.
    """
    out: list[str] = []
    index = 0
    length = len(text)
    in_string = False
    escaped = False
    #: Last significant (non-whitespace) character seen *outside* a string literal.
    previous = ""

    while index < length:
        char = text[index]

        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
                previous = '"'
            index += 1
            continue

        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue

        # ``2L`` -> ``2``. An alpha character directly behind a digit is never legal in
        # strict JSON, so the only question is whether it is the type suffix or the start
        # of a bare literal -- the terminator check settles it (``1,``/``1}`` yes,
        # ``1e5`` no, ``1true`` no).
        if char in _NUMBER_SUFFIXES and out and out[-1].isdigit():
            following = text[index + 1] if index + 1 < length else ""
            if following == "" or following in _NUMBER_TERMINATORS:
                index += 1
                continue

        # ``Set["*:*:*"]`` -> ``["*:*:*"]``; ``java.util.HashMap{...}`` -> ``{...}``.
        if (char.isalpha() or char in "._$") and previous in _WRAPPER_STARTS:
            end = index
            while end < length and (text[end].isalnum() or text[end] in "._$"):
                end += 1
            if end < length and text[end] in "[{":
                index = end
                continue

        out.append(char)
        if char not in " \t\r\n":
            previous = char
        index += 1

    return "".join(out)


def parse_fastjson2_text(text: str) -> Any:
    """Parse fastjson2 text, accepting both strict JSON and the ``WriteClassName`` dialect.

    Java: ``JSON.parseObject(str, Object.class, autoTypeFilter)``. Everything this port
    writes is ordinary JSON, so the normalising pass only runs when the plain parse fails --
    that keeps Python-written caches on the fast path and avoids any chance of rewriting a
    well-formed payload.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    return json.loads(_normalize_fastjson2_text(text))


class FastJson2JsonRedisSerializer:
    """Java: ``FastJson2JsonRedisSerializer<T>`` with ``T = Object``."""

    def __init__(self) -> None:
        # Java stores ``clazz``; with ``Object.class`` it is only used as the fallback
        # type when no "@type" marker is present.
        self.clazz = object

    # Java: public byte[] serialize(T t)
    def serialize(self, value: Any) -> str:
        """Serialize to JSON text (the client decodes bytes to ``str`` for us)."""
        if value is None:
            # Java: return new byte[0];
            return ""
        try:
            payload = self._with_type(value)
            return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise SerializationError(f"Cannot serialize {type(value).__name__}: {exc}") from exc

    # Java: public T deserialize(byte[] bytes)
    def deserialize(self, text: Optional[str]) -> Any:
        if text is None or text == "":
            # Java: if (bytes == null || bytes.length <= 0) { return null; }
            return None
        try:
            # ``parse_fastjson2_text`` -- not ``json.loads`` -- because a cache written by
            # the Java build carries ``2L`` suffixes and ``Set[...]`` wrappers.
            payload = parse_fastjson2_text(text)
        except json.JSONDecodeError as exc:
            raise SerializationError(f"Cannot deserialize {text!r}: {exc}") from exc
        return self._from_payload(payload)

    # -- internals --------------------------------------------------------

    def _with_type(self, value: Any) -> Any:
        """``to_jsonable`` plus the ``"@type"`` marker fastjson2 writes."""
        if isinstance(value, list):
            return [self._with_type(item) for item in value]
        if isinstance(value, dict):
            return {key: self._with_type(item) for key, item in value.items()}

        java_name = _JAVA_TYPE_NAMES.get(type(value))
        if java_name is None:
            return to_jsonable(value)

        # ``model_dump`` then re-attach "@type" first so the payload reads like fastjson2's.
        dumped = value.to_json_dict()  # type: ignore[attr-defined]
        payload: Dict[str, Any] = {TYPE_KEY: java_name}
        payload.update(dumped)
        # Jackson's @JsonIgnore / pydantic's exclude drop ``password``; fastjson2 does not.
        # Re-attached for the top-level bean and for the ``SysUser`` nested in a LoginUser.
        if isinstance(value, SysUser):
            payload["password"] = value.password
        elif isinstance(value, LoginUser) and isinstance(payload.get("user"), dict):
            payload["user"]["password"] = value.user.password if value.user else None
        return payload

    def _from_payload(self, payload: Any) -> Any:
        if isinstance(payload, list):
            return [self._from_payload(item) for item in payload]
        if not isinstance(payload, dict):
            return payload

        data = {key: item for key, item in payload.items() if key != TYPE_KEY}
        java_name = payload.get(TYPE_KEY)
        target = TYPE_REGISTRY.get(java_name) if isinstance(java_name, str) else None
        if target is None:
            if java_name is not None:
                logger.debug("Redis payload carries unregistered @type=%s; returning dict", java_name)
            return {key: self._from_payload(item) for key, item in data.items()}

        # Nested objects (``user``) are declared with a concrete type in Java, so they
        # carry no "@type"; pydantic validates them from the plain dict.
        return target.model_validate(data)


__all__ = [
    "FastJson2JsonRedisSerializer",
    "SerializationError",
    "TYPE_REGISTRY",
    "TYPE_KEY",
    "parse_fastjson2_text",
]
