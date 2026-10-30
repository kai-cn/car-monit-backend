"""System module (Java: ``com.ruoyi.system``).

Contains the table-backed domain objects, their MyBatis mappers and the services that the
web layer consumes. ``ruoyi-system`` in Java is a separate Maven module; here it is a
sub-package with the same internal split:

    app/system/domain    <- com.ruoyi.system.domain
    app/system/mapper    <- com.ruoyi.system.mapper
    app/system/service   <- com.ruoyi.system.service (+ service.impl)
"""

from __future__ import annotations
