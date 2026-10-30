"""验证码操作处理.

# Migrated from: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/CaptchaController.java

``GET /captchaImage`` -- ``permitAll`` in ``SecurityConfig``, so it works before login.

Response shape (``AjaxResult.success()`` plus two keys)::

    {"msg": "操作成功", "img": "/9j/4AAQSkZJRg...", "code": 200, "uuid": "8f3c..."}

**键序是 HashMap 桶序，不是 put 序**：``AjaxResult extends HashMap``，三个键的桶号是
``msg``=0 / ``img``=2 / ``code``=3 / ``uuid``=13，所以真实响应里 ``img`` 夹在 ``msg``
和 ``code`` 中间。写成 ``ajax["uuid"] = ...`` 会按插入序排到末尾，所以必须走
``put_chain``（见 :mod:`app.common.core.domain.java_hash_map`）。

There is **no** ``captchaEnabled`` flag -- unlike stock RuoYi 3.8.x, this controller never puts
one, so the client cannot learn from here whether the captcha is enforced. It *is* enforced,
purely because ``SysLoginService`` looks at whether the request carries a ``code``.

The two-way split on ``@``
--------------------------
``KaptchaTextCreator`` returns ``"3*4=?@12"``. The controller keeps the text left of the
**last** ``@`` for the image and stores everything right of it in Redis as the expected
answer. ``lastIndexOf`` (not ``indexOf``) matters: a future expression containing ``@``
would still split correctly, and ``substring`` on the answer side is
``lastIndexOf("@") + 1`` -- with no ``@`` the Java code throws
``StringIndexOutOfBoundsException`` (index ``0``), i.e. a real 500. Not reachable with
:class:`KaptchaTextCreator`, which always appends ``@``.

``char`` branch
---------------
``captchaProducer.createText()`` gives 4 characters and the whole string *is* the answer.
``ruoyi.captchaType`` is ``math`` in ``application.yml``, so this branch only runs if the
configuration is switched.

Image encoding
--------------
Java writes JPEG into memory via ``ImageIO`` and Base64-encodes the bytes. The failure branch
(``catch (IOException) -> AjaxResult.error(e.getMessage())``) is kept, although Pillow raises
different exception types; a failed encode answers ``{"code":500,...}`` with HTTP 200, exactly
like Java.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter

from app.common.constant.constants import CAPTCHA_CODE_KEY, CAPTCHA_EXPIRATION
from app.common.core.domain.ajax_result import AjaxResult
from app.common.core.redis.redis_cache import RedisCache, get_redis_cache
from app.common.utils import base64_utils
from app.common.utils.time_unit import TimeUnit
from app.common.utils.uuid_utils import simple_uuid
from app.framework.config.captcha_config import (
    DefaultKaptcha,
    encode_jpeg,
    get_captcha_producer,
    get_captcha_producer_math,
)
from app.settings import get_settings

logger = logging.getLogger("app.api.common.captcha")

router = APIRouter(tags=["common-captcha"])

#: Java: ``@Value("${ruoyi.captchaType}")`` -- ``"math"`` or ``"char"``.
_MATH = "math"
_CHAR = "char"

_PRODUCER: Optional[DefaultKaptcha] = None
_PRODUCER_MATH: Optional[DefaultKaptcha] = None
_REDIS_CACHE: Optional[RedisCache] = None


# Java: @Resource(name = "captchaProducerMath") private Producer captchaProducerMath
def _captcha_producer_math() -> DefaultKaptcha:
    global _PRODUCER_MATH
    if _PRODUCER_MATH is None:
        _PRODUCER_MATH = get_captcha_producer_math()
    return _PRODUCER_MATH


# Java: @Resource(name = "captchaProducer") private Producer captchaProducer
def _captcha_producer() -> DefaultKaptcha:
    global _PRODUCER
    if _PRODUCER is None:
        _PRODUCER = get_captcha_producer()
    return _PRODUCER


# Java: @Autowired private RedisCache redisCache
def _redis_cache() -> RedisCache:
    global _REDIS_CACHE
    if _REDIS_CACHE is None:
        _REDIS_CACHE = get_redis_cache()
    return _REDIS_CACHE


def reset_captcha_controller() -> None:
    """Test helper: drop the cached collaborators so fakes can be injected."""
    global _PRODUCER, _PRODUCER_MATH, _REDIS_CACHE
    _PRODUCER = None
    _PRODUCER_MATH = None
    _REDIS_CACHE = None


def get_code() -> AjaxResult:
    """Java: ``@GetMapping("/captchaImage") public AjaxResult getCode(HttpServletResponse)``.

    Split out from the route so tests can call it without HTTP. The Java parameter
    ``HttpServletResponse`` only exists for cookie/header tricks the method never performs.
    """
    # 保存验证码信息
    uuid = simple_uuid()
    verify_key = CAPTCHA_CODE_KEY + uuid

    cap_str: Optional[str] = None
    code: Optional[str] = None
    image = None

    captcha_type = get_settings().ruoyi.captcha_type
    # 生成验证码
    if captcha_type == _MATH:
        cap_text = _captcha_producer_math().create_text()
        # Java: capStr = capText.substring(0, capText.lastIndexOf("@"));
        #       code   = capText.substring(capText.lastIndexOf("@") + 1);
        split_at = cap_text.rfind("@")
        if split_at < 0:
            # Java would throw StringIndexOutOfBoundsException here -> a real 500.
            raise IndexError("String index out of range: -1")
        cap_str = cap_text[:split_at]
        code = cap_text[split_at + 1:]
        image = _captcha_producer_math().create_image(cap_str)
    elif captcha_type == _CHAR:
        cap_str = code = _captcha_producer().create_text()
        image = _captcha_producer().create_image(cap_str)

    # Note: when neither branch matches, ``code`` stays ``None`` and is *still* written to
    # Redis -- Java does the same, so a misconfigured ``captchaType`` stores a null answer and
    # every login with a code fails as ``验证码错误``. Preserved deliberately.
    _redis_cache().set_cache_object_with_timeout(
        verify_key, code, CAPTCHA_EXPIRATION, TimeUnit.MINUTES
    )

    # 转换流信息写出
    try:
        payload = encode_jpeg(image)
    except OSError as ex:  # Java: catch (IOException e) -> AjaxResult.error(e.getMessage())
        return AjaxResult.error_message(str(ex))

    ajax = AjaxResult.success()
    # Java: ajax.put("uuid", uuid); ajax.put("img", base64) —— HashMap 桶序，不是追加
    ajax.put_chain("uuid", uuid)
    ajax.put_chain("img", base64_utils.encode(payload))
    return ajax


# ``response_model=None`` -- ``AjaxResult`` subclasses ``dict``, so FastAPI cannot derive a
# Pydantic response model from the annotation and would fail at import time. Java's
# ``AjaxResult extends HashMap`` is serialized verbatim by Jackson; disabling the response
# model is the exact analogue.
@router.get("/captchaImage", response_model=None)
def captcha_image() -> AjaxResult:
    """Java: ``@GetMapping("/captchaImage")``.

    A plain (non-async) ``def`` so Pillow rendering runs on the worker thread pool, like a
    Tomcat request thread.
    """
    return get_code()


__all__ = ["router", "get_code", "reset_captcha_controller"]
