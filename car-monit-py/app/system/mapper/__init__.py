"""MyBatis mappers (Java: ``com.ruoyi.system.mapper``).

One class per Java mapper **interface**; the SQL that used to live in
``resources/mapper/**/*Mapper.xml`` sits next to the method that executes it, because
Python has no XML mapper binding. Every statement keeps the original ``<if>`` logic as an
explicit Python condition, and every docstring names the XML file it came from.
"""

from __future__ import annotations
