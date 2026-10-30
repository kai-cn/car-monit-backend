"""Client-IP helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/IpUtils.java

Java original
-------------
``HttpServletRequest.getHeader(name)`` is case-insensitive, and ``getRemoteAddr()`` is the TCP
peer. The header precedence below is copied verbatim -- it is the only thing that decides what
lands in ``sys_logininfor.ipaddr``, so "improving" the order would change audit data.

The Java implementation contains a **switch fall-through bug** in ``internalIp(byte[])`` that is
reproduced on purpose; see :func:`internal_ip_bytes`.
"""

from __future__ import annotations

import re
import socket
from typing import List, Optional

from app.common.utils.string_utils import is_blank, is_not_blank, split_regex, substring

_REGX_0_255 = r"(25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)"
#: 匹配 ip
REGX_IP = rf"(({_REGX_0_255}\.){{3}}{_REGX_0_255})"
#: 匹配 ip 通配符 (``*.*.*.*`` / ``1.*.*.*`` / ``1.2.*.*`` / ``1.2.3.*``)
#:
#: Composed branch-by-branch from the Java concatenation instead of copying the escaped
#: Java string literal: Java's ``"\\*"`` is the two-character regex ``\*`` (a literal ``*``),
#: which a raw Python string must spell ``\*`` -- one backslash, not two.
REGX_IP_WILDCARD = (
    "((" + r"(\*\.){3}\*" + ")|"
    + "(" + _REGX_0_255 + r"(\.\*){3})|"
    + "(" + _REGX_0_255 + r"\." + _REGX_0_255 + r")(\.\*){2}|"
    + "((" + _REGX_0_255 + r"\.){3}\*))"
)
#: 匹配网段
REGX_IP_SEG = rf"({REGX_IP}\-{REGX_IP})"

_IPV6_LOCALHOST = "0:0:0:0:0:0:0:1"
_UNKNOWN = "unknown"

_IP_PATTERN = re.compile(REGX_IP)
_IP_WILDCARD_PATTERN = re.compile(REGX_IP_WILDCARD)
_IP_SEG_PATTERN = re.compile(REGX_IP_SEG)


def get_ip_addr(request=None) -> str:
    """Java: ``IpUtils.getIpAddr([HttpServletRequest])``.

    ``request`` is a Starlette/FastAPI ``Request``. Header lookup is case-insensitive on both
    sides (Servlet API and Starlette), so the literal header names below are safe to keep.
    """
    if request is None:
        return _UNKNOWN

    ip: Optional[str] = request.headers.get("x-forwarded-for")
    if ip is None or len(ip) == 0 or _UNKNOWN.lower() == ip.lower():
        ip = request.headers.get("Proxy-Client-IP")
    if ip is None or len(ip) == 0 or _UNKNOWN.lower() == ip.lower():
        ip = request.headers.get("X-Forwarded-For")
    if ip is None or len(ip) == 0 or _UNKNOWN.lower() == ip.lower():
        ip = request.headers.get("WL-Proxy-Client-IP")
    if ip is None or len(ip) == 0 or _UNKNOWN.lower() == ip.lower():
        ip = request.headers.get("X-Real-IP")
    if ip is None or len(ip) == 0 or _UNKNOWN.lower() == ip.lower():
        client = getattr(request, "client", None)
        ip = client.host if client is not None else None

    if ip == _IPV6_LOCALHOST:
        return "127.0.0.1"
    return get_multistage_reverse_proxy_ip(ip)


def internal_ip(ip: Optional[str]) -> bool:
    """Java: ``IpUtils.internalIp(String)``."""
    if ip is None:
        # Java would NPE in textToNumericFormatV4; the public entry point is always called with
        # a value from getIpAddr, which never returns null.
        return True
    addr = text_to_numeric_format_v4(ip)
    return internal_ip_bytes(addr) or "127.0.0.1" == ip


def internal_ip_bytes(addr: Optional[List[int]]) -> bool:
    """Java: ``IpUtils.internalIp(byte[])`` -- **including its fall-through bug**.

    The Java ``switch (b0)`` has no ``break`` after ``case SECTION_2``, so a ``172.x.x.x``
    address whose second octet is *not* in ``16..31`` falls through into ``case SECTION_5`` and
    is additionally tested against ``192.168``'s second octet. Concretely ``172.168.1.1`` is
    reported as an internal address. The bug is preserved because the result feeds
    ``AddressUtils`` (and therefore ``sys_logininfor.login_location``); "fixing" it would change
    recorded login locations.
    """
    if addr is None or len(addr) < 2:
        return True
    b0 = addr[0]
    b1 = addr[1]
    # 10.x.x.x/8
    if b0 == 0x0A:
        return True
    if b0 == 0xAC:  # 172.16.x.x/12
        if 0x10 <= b1 <= 0x1F:
            return True
        # fall through (Java has no ``break`` here)
        if b1 == 0xA8:
            return True
        return False
    if b0 == 0xC0:  # 192.168.x.x/16
        return b1 == 0xA8
    return False


def text_to_numeric_format_v4(text: Optional[str]) -> Optional[List[int]]:
    """Java: ``IpUtils.textToNumericFormatV4(String)``.

    Returns four unsigned octet values (Java returns ``byte[]``, whose values are signed; the
    only consumer -- :func:`internal_ip_bytes` -- compares them against signed constants, so
    unsigned ints with unsigned constants are equivalent and far easier to read).
    """
    if text is None or len(text) == 0:
        return None

    elements = split_regex(text, r"\.", limit=-1)
    if elements is None:
        return None
    try:
        if len(elements) == 1:
            value = int(elements[0])
            if value < 0 or value > 4294967295:
                return None
            return [
                (value >> 24) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF,
            ]
        if len(elements) == 2:
            first = int(elements[0])
            if first < 0 or first > 255:
                return None
            second = int(elements[1])
            if second < 0 or second > 16777215:
                return None
            return [first & 0xFF, (second >> 16) & 0xFF, (second >> 8) & 0xFF, second & 0xFF]
        if len(elements) == 3:
            octets: List[int] = []
            for index in range(2):
                value = int(elements[index])
                if value < 0 or value > 255:
                    return None
                octets.append(value & 0xFF)
            third = int(elements[2])
            if third < 0 or third > 65535:
                return None
            octets.append((third >> 8) & 0xFF)
            octets.append(third & 0xFF)
            return octets
        if len(elements) == 4:
            octets = []
            for element in elements:
                value = int(element)
                if value < 0 or value > 255:
                    return None
                octets.append(value & 0xFF)
            return octets
        return None
    except ValueError:
        # Java catches NumberFormatException and returns null.
        return None


def get_host_ip() -> str:
    """Java: ``IpUtils.getHostIp()``."""
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def get_host_name() -> str:
    """Java: ``IpUtils.getHostName()``."""
    try:
        return socket.gethostname()
    except OSError:
        return "未知"


def get_multistage_reverse_proxy_ip(ip: Optional[str]) -> str:
    """Java: ``IpUtils.getMultistageReverseProxyIp(String)``.

    For ``"a, b"`` the first non-unknown entry wins (Java trims the whole header first, not the
    individual entries -- so ``"a, b"`` yields ``"b"`` with a leading space).
    """
    if ip is not None and ip.find(",") > 0:
        for sub_ip in split_regex(ip.strip(), ",") or []:
            if not is_unknown(sub_ip):
                ip = sub_ip
                break
    return substring(ip, 0, 255)


def is_unknown(check_string: Optional[str]) -> bool:
    """Java: ``IpUtils.isUnknown(String)``."""
    return is_blank(check_string) or _UNKNOWN.lower() == (check_string or "").lower()


def is_ip(ip: Optional[str]) -> bool:
    """Java: ``IpUtils.isIP(String)``."""
    return is_not_blank(ip) and _IP_PATTERN.fullmatch(ip or "") is not None


def is_ip_wild_card(ip: Optional[str]) -> bool:
    """Java: ``IpUtils.isIpWildCard(String)``."""
    return is_not_blank(ip) and _IP_WILDCARD_PATTERN.fullmatch(ip or "") is not None


def ip_is_in_wild_card_no_check(ip_wild_card: str, ip: str) -> bool:
    """Java: ``IpUtils.ipIsInWildCardNoCheck(String, String)`` -- prefix compare, stops at ``*``."""
    segment_wild = split_regex(ip_wild_card, r"\.") or []
    segment_ip = split_regex(ip, r"\.") or []
    matched = True
    index = 0
    while index < len(segment_wild) and segment_wild[index] != "*":
        if segment_wild[index] != segment_ip[index]:
            matched = False
            break
        index += 1
    return matched


def is_ip_segment(ip_seg: Optional[str]) -> bool:
    """Java: ``IpUtils.isIPSegment(String)`` -- ``10.10.10.1-10.10.10.99``."""
    return is_not_blank(ip_seg) and _IP_SEG_PATTERN.fullmatch(ip_seg or "") is not None


def ip_is_in_net_no_check(ip_area: str, ip: str) -> bool:
    """Java: ``IpUtils.ipIsInNetNoCheck(String, String)`` -- numeric range compare."""
    idx = ip_area.find("-")
    start_octets = split_regex(ip_area[:idx], r"\.") or []
    end_octets = split_regex(ip_area[idx + 1:], r"\.") or []
    target_octets = split_regex(ip, r"\.") or []
    ip_start = 0
    ip_end = 0
    ip_target = 0
    for index in range(4):
        ip_start = (ip_start << 8) | int(start_octets[index])
        ip_end = (ip_end << 8) | int(end_octets[index])
        ip_target = (ip_target << 8) | int(target_octets[index])
    if ip_start > ip_end:
        ip_start, ip_end = ip_end, ip_start
    return ip_start <= ip_target <= ip_end


def is_matched_ip(ip_filter: Optional[str], ip: Optional[str]) -> bool:
    """Java: ``IpUtils.isMatchedIp(String filter, String ip)``.

    ``filter`` supports ``;``-separated entries, ``*`` suffix wildcards and ``a-b`` ranges.
    """
    if is_blank(ip_filter) or is_blank(ip):
        return False
    assert ip_filter is not None and ip is not None
    for item in split_regex(ip_filter, ";"):
        if is_ip(item) and item == ip:
            return True
        if is_ip_wild_card(item) and ip_is_in_wild_card_no_check(item, ip):
            return True
        if is_ip_segment(item) and ip_is_in_net_no_check(item, ip):
            return True
    return False


__all__ = [
    "REGX_IP",
    "REGX_IP_WILDCARD",
    "REGX_IP_SEG",
    "get_ip_addr",
    "internal_ip",
    "internal_ip_bytes",
    "text_to_numeric_format_v4",
    "get_host_ip",
    "get_host_name",
    "get_multistage_reverse_proxy_ip",
    "is_unknown",
    "is_ip",
    "is_ip_wild_card",
    "ip_is_in_wild_card_no_check",
    "is_ip_segment",
    "ip_is_in_net_no_check",
    "is_matched_ip",
]
