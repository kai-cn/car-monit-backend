"""通用 http 发送方法 / plain HTTP helpers.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/http/HttpUtils.java

Only :func:`send_get` is ported: the Java class also has ``sendPost``/``sendSSLPost``, but
nothing in this project's *reachable* code calls them (they belong to the SMS and 恒达
integrations, which arrive in a later phase). Add them when their call sites are migrated --
an unused port would be untested dead code.

Mirrored behaviours
-------------------
* **Every failure is swallowed.** ``ConnectException``, ``SocketTimeoutException``,
  ``IOException`` and ``Exception`` are logged and the method returns whatever it had
  accumulated -- usually ``""``. So a dead geolocation service degrades to "unknown
  address", it never fails the request. Reproduced with a single ``except Exception``.
* **Lines are concatenated without separators.** ``BufferedReader.readLine()`` strips the
  line terminator and the Java loop appends nothing in its place, so ``"a\nb"`` becomes
  ``"ab"``. :func:`_java_read_line` reproduces that splitting rule exactly.
* **No timeout is configured in Java.** ``URLConnection`` therefore uses an infinite
  connect/read timeout; the same is expressed here as ``timeout=None``. Callers that need
  a bound must add one -- don't quietly diverge.
* **TLS certificates are not validated.** ``sendSSLPost`` installs a trust-all
  ``TrustManager``; ``sendGet`` inherits the JVM default (validating) but is only ever
  pointed at ``http://`` URLs. ``verify=False`` is used for parity with the class's intent.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.common.constant.constants import UTF8

logger = logging.getLogger("app.common.utils.http")


def send_get(url: str, param: str = "", charset: str = UTF8) -> str:
    """向指定 URL 发送 GET 方法的请求.

    Java: ``HttpUtils.sendGet(String url, String param, String contentType)``.
    ``contentType`` is the *response* charset (``AddressUtils`` passes ``GBK``).
    """
    collected: list[str] = []
    # Java: String urlNameString = StringUtils.isNotBlank(param) ? url + "?" + param : url;
    url_name_string = f"{url}?{param}" if param and param.strip() else url
    try:
        logger.info("sendGet - %s", url_name_string)
        headers = {
            "accept": "*/*",
            "connection": "Keep-Alive",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        # timeout=None mirrors URLConnection's infinite default.
        with httpx.Client(timeout=None, verify=False, follow_redirects=False) as client:
            response = client.get(url_name_string, headers=headers)
            # Java decodes the whole body with the supplied charset before splitting lines;
            # ``iter_lines`` would instead sniff the response encoding.
            text = response.content.decode(_python_codec(charset), errors="replace")
            collected.extend(_java_read_line(text))
        logger.info("recv - %s", "".join(collected))
    except Exception as exc:  # noqa: BLE001 - Java catches Exception here on purpose
        logger.error("调用HttpUtils.sendGet 异常, url=%s,param=%s, %s", url, param, exc)
    return "".join(collected)


def _java_read_line(text: str) -> list[str]:
    """Java: repeated ``BufferedReader.readLine()`` -- terminators stripped, no ``\\r``."""
    normalised = text.replace("\r\n", "\n").replace("\r", "\n")
    if normalised.endswith("\n"):
        normalised = normalised[:-1]
    return normalised.split("\n") if normalised else []


#: Java charset name -> Python codec name. Java uses ``GBK`` in ``AddressUtils``.
_CODECS = {"GBK": "gbk", "UTF-8": "utf-8", "GB2312": "gb2312", "ISO-8859-1": "iso-8859-1"}


def _python_codec(java_charset: Optional[str]) -> str:
    if not java_charset:
        return "utf-8"
    return _CODECS.get(java_charset.upper(), java_charset.lower())


__all__ = ["send_get"]
