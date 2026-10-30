"""ID generators.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/uuid/IdUtils.java

Java's ``UUID.fastUUID()`` uses ``ThreadLocalRandom`` (a speed optimisation only). Python's
``uuid4()`` is backed by ``os.urandom`` -- also thread-safe and non-blocking after the first
call, so the fast/normal distinction disappears and both functions return the same shape.

The formats are what matter: ``randomUUID`` keeps the 8-4-4-4-12 dashes, ``simpleUUID`` removes
them. ``TokenService`` stores the dashed form inside the JWT and as part of the Redis key, so the
dashes are part of the wire contract.
"""

from __future__ import annotations

import uuid


def random_uuid() -> str:
    """Java: ``IdUtils.randomUUID()`` -> ``550e8400-e29b-41d4-a716-446655440000``."""
    return str(uuid.uuid4())


def simple_uuid() -> str:
    """Java: ``IdUtils.simpleUUID()`` -> dashes removed."""
    return str(uuid.uuid4()).replace("-", "")


def fast_uuid() -> str:
    """Java: ``IdUtils.fastUUID()`` -- same output shape as :func:`random_uuid`."""
    return str(uuid.uuid4())


def fast_simple_uuid() -> str:
    """Java: ``IdUtils.fastSimpleUUID()`` -- same output shape as :func:`simple_uuid`."""
    return str(uuid.uuid4()).replace("-", "")


__all__ = ["random_uuid", "simple_uuid", "fast_uuid", "fast_simple_uuid"]
