"""User-Agent parsing.

# Migrated from: eu.bitwalker:useragentutils (third-party library, no RuoYi file)
# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/ip/AddressUtils.java (call sites)

Why this module exists
----------------------
Two RuoYi classes call ``UserAgent.parseUserAgentString(...)``:

* ``TokenService.setUserAgent``     -> ``LoginUser.browser`` / ``LoginUser.os``
* ``AsyncFactory.recordLogininfor`` -> ``sys_logininfor.browser`` / ``.os``

Both must produce the same strings for the same request, so the mapping lives here once
instead of being duplicated. ``eu.bitwalker:useragentutils`` has no Python counterpart; the
``user-agents`` package is used and the differences are pinned in the docstrings below.

Field semantics copied from useragentutils
------------------------------------------
* ``Browser.getName()``     -> bare family name, never a version.
* ``OperatingSystem.getName()`` -> bare family name, **except Windows**, whose enum
  constants embed the release (``"Windows 10"``, ``"Windows 7"``, ``"Windows 8.1"``).
* No match -> ``Browser.UNKNOWN`` / ``OperatingSystem.UNKNOWN``, whose name is ``"Unknown"``.
"""

from __future__ import annotations

from typing import Optional

import user_agents

#: Java: ``Browser.UNKNOWN.getName()`` and ``OperatingSystem.UNKNOWN.getName()``.
UNKNOWN_AGENT = "Unknown"


def browser_name(user_agent_string: Optional[str]) -> str:
    """Java: ``UserAgent.parseUserAgentString(s).getBrowser().getName()``.

    For every browser that can actually submit the login form the two libraries agree:
    ``"Chrome"``, ``"Firefox"``, ``"Edge"``, ``"Safari"``, ``"Chrome Mobile"``,
    ``"Mobile Safari"``, ``"IE"``.

    **Known divergence** (see ``COMPATIBILITY.md``): non-browser agents. ``user-agents``
    reports ``"curl"``, ``"Wget"``, ``"Python Requests"``, ``"okhttp"`` and
    ``"Go-http-client"``, whereas useragentutils only carries browser patterns and returns
    ``"Unknown"``. The library value is kept instead of being guessed into a denylist: these
    fields are display-only (``sys_user_online.browser``) and no business rule reads them.

    A missing header behaves like Java's null argument: ``"Unknown"``. (useragentutils'
    ``getBrowser(null)`` returns ``Browser.UNKNOWN`` rather than throwing.)
    """
    if not user_agent_string:
        return UNKNOWN_AGENT
    family = user_agents.parse(user_agent_string).browser.family
    return UNKNOWN_AGENT if family == "Other" else family


def operating_system_name(user_agent_string: Optional[str]) -> str:
    """Java: ``UserAgent.parseUserAgentString(s).getOperatingSystem().getName()``.

    ``user-agents`` splits family and version; useragentutils embeds the version in the
    Windows family names only, so the release is re-joined for Windows and dropped
    everywhere else (``"Mac OS X"``, not ``"Mac OS X 10.15.7"``).
    """
    if not user_agent_string:
        return UNKNOWN_AGENT
    information = user_agents.parse(user_agent_string)
    family = information.os.family
    if family == "Other":
        return UNKNOWN_AGENT
    if family == "Windows":
        # ``version_string`` is "10" / "8.1" / "7" for the UA strings Windows actually sends.
        version = information.os.version_string
        return f"Windows {version}" if version else family
    return family


__all__ = ["UNKNOWN_AGENT", "browser_name", "operating_system_name"]
