"""i18n message lookup.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/MessageUtils.java

Java original
-------------
``MessageUtils.message(code, args)`` resolves through Spring's ``MessageSource``
configured with ``spring.messages.basename = i18n/messages``. Resource bundles live in
``ruoyi-admin/src/main/resources/i18n/messages.properties``.

Python equivalent
-----------------
A plain ``dict`` bundle loaded from ``config/i18n/messages*.properties`` with
``Accept-Language`` resolution delegated to the caller. Missing keys return ``None``
(matching Spring's ``NoSuchMessageException`` -> ``null`` fallback in ``BaseException``).
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from typing import Any, Dict, Optional

from app.settings import PROJECT_ROOT

_BUNDLE_DIR = PROJECT_ROOT / "config" / "i18n"

_PLACEHOLDER = re.compile(r"\{(\d+)\}")


@functools.lru_cache(maxsize=8)
def _load_bundle(locale: str) -> Dict[str, str]:
    """Load a ``messages_<locale>.properties`` file; ``messages`` for the default locale."""
    suffix = "" if locale in ("", "zh_CN", "zh") else f"_{locale}"
    path = _BUNDLE_DIR / f"messages{suffix}.properties"
    if not path.is_file():
        return {}
    entries: Dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            entries[key.strip()] = value.strip()
    return entries


def message(code: Optional[str], args: Any = None, locale: str = "zh_CN") -> Optional[str]:
    """Java: ``MessageUtils.message(String code, Object[] args)``.

    Returns ``None`` when the code is unknown, so callers can fall back to a default.
    """
    if code is None:
        return None
    template = _load_bundle(locale).get(code)
    if template is None and locale != "zh_CN":
        template = _load_bundle("zh_CN").get(code)
    if template is None:
        return None
    if args is None:
        return template
    argv = args if isinstance(args, (list, tuple)) else [args]
    return _PLACEHOLDER.sub(lambda m: str(argv[int(m.group(1))]) if int(m.group(1)) < len(argv) else m.group(0), template)


def reset_bundle_cache() -> None:
    """Test helper."""
    _load_bundle.cache_clear()


__all__ = ["message", "reset_bundle_cache", "Path"]
