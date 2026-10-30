"""获取地址类 / IP-to-location lookup.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/AddressUtils.java

Mirrored behaviours
-------------------
* **Internal IPs never leave the process.** ``IpUtils.internalIp(ip)`` short-circuits to
  ``"内网IP"``. This project inherits the ``internalIp`` switch fall-through bug that
  treats ``172.168.*.*`` as internal (see :mod:`app.common.utils.ip_utils`), so a few
  public addresses are also reported as 内网IP -- identical to Java.
* **``addressEnabled: false`` in ``application.yml``**, so :func:`get_real_address_by_ip`
  returns ``"XX XX"`` for every non-internal address without doing any I/O. That is the
  default and therefore the behaviour in production today; the lookup branch exists for
  completeness and is only exercised when the flag is switched on.
* The remote service is ``http://whois.pconline.com.cn/ipJson.jsp`` read as **GBK**, and
  its ``pro`` / ``city`` fields are joined with a single space.
"""

from __future__ import annotations

import json
import logging

from app.common.constant.constants import GBK
from app.common.utils.http_utils import send_get
from app.common.utils.ip_utils import internal_ip
from app.settings import get_settings

logger = logging.getLogger("app.common.utils.address")

#: IP 地址查询
IP_URL = "http://whois.pconline.com.cn/ipJson.jsp"
#: 未知地址
UNKNOWN = "XX XX"


def get_real_address_by_ip(ip: str) -> str:
    """Java: ``AddressUtils.getRealAddressByIP(String)``."""
    # 内网不查询
    if internal_ip(ip):
        return "内网IP"
    if get_settings().ruoyi.address_enabled:
        try:
            rsp_str = send_get(IP_URL, f"ip={ip}&json=true", GBK)
            if not rsp_str:
                logger.error("获取地理位置异常 %s", ip)
                return UNKNOWN
            # fastjson2's ``getString`` returns null for a missing key; ``.get`` matches.
            obj = json.loads(rsp_str)
            region = obj.get("pro")
            city = obj.get("city")
            # Java: String.format("%s %s", region, city) -- null renders as "null".
            return f"{_java_string(region)} {_java_string(city)}"
        except Exception:  # noqa: BLE001 - Java logs and falls through to UNKNOWN
            logger.exception("获取地理位置异常 %s", ip)
    return UNKNOWN


def _java_string(value: object) -> str:
    """Java: ``String.format`` renders a null argument as the literal ``null``."""
    return "null" if value is None else str(value)


__all__ = ["get_real_address_by_ip", "IP_URL", "UNKNOWN"]
