"""验证码文本生成器 / the arithmetic captcha text.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/KaptchaTextCreator.java

The produced string is not the visible text -- it is ``"<expression>=?@<answer>"``. For
``3*4`` it returns ``"3*4=?@12"``. ``CaptchaController`` then splits on the **last** ``@``:
everything before it is rendered into the image, everything after it is stored in Redis and is
what the client must submit.

Consequences that must not be "improved":

* The client answers with a **number**, not with the expression. The image shows
  ``3*4=?``; typing ``12`` or ``12 `` (trailing space is *not* trimmed -- see
  ``SysLoginService.validate_captcha``) is compared verbatim.
* ``randomoperands == 1`` falls back to addition when the division would not be exact,
  so ``/`` never yields a fraction. Condition: ``x != 0 && y % x == 0`` -- note the operands
  are written ``y/x`` in that branch (larger number first is not guaranteed, e.g. ``x=5,
  y=5`` gives ``5/5``).
* ``x`` and ``y`` are ``nextInt(10)``, i.e. ``0..9`` -- ``10`` can never occur, yet
  ``CNUMBERS`` has 11 entries because the original snippet was copied from a 0..10 variant.
  The extra entry is unreachable and kept only for traceability.
* Subtraction always yields a non-negative result because the operands are swapped
  (``x >= y ? x - y : y - x``).

``DefaultTextCreator``
----------------------
``com.google.code.kaptcha.text.impl.DefaultTextCreator`` is the base class, overridden here.
It is used verbatim by the ``char`` producer (``captchaProducer``), which this project only
reaches when ``ruoyi.captchaType`` is switched from ``math`` to ``char``.
"""

from __future__ import annotations

import random
from typing import Optional

#: Java: ``private static final String[] CNUMBERS = "0,1,2,3,4,5,6,7,8,9,10".split(",")``
CNUMBERS = "0,1,2,3,4,5,6,7,8,9,10".split(",")

#: kaptcha ``Constants.DEFAULT_TEXTPRODUCER_CHAR_STRING`` -- the alphabet
#: ``DefaultTextCreator`` uses when ``kaptcha.textproducer.char.string`` is not configured,
#: which is the case in ``CaptchaConfig``. Visually ambiguous glyphs (``0``/``o``/``1``/``l``)
#: were removed upstream.
DEFAULT_CHAR_STRING = "abcde2345678gfynmnpwx"


class DefaultTextCreator:
    """Java: ``com.google.code.kaptcha.text.impl.DefaultTextCreator``.

    Draws ``char_length`` characters uniformly from the configured alphabet. The alphabet and
    the length come from kaptcha's ``Config``; they are constructor arguments here.
    """

    def __init__(self, char_string: str = DEFAULT_CHAR_STRING, char_length: int = 4) -> None:
        # Java reads both from ``Config`` on every call; they are immutable here because
        # ``CaptchaConfig`` sets them once at startup.
        self._char_string = char_string
        self._char_length = char_length

    # Java: Config#getTextProducerCharString()
    @property
    def char_string(self) -> str:
        return self._char_string

    # Java: Config#getTextProducerCharLength()
    @property
    def char_length(self) -> int:
        return self._char_length

    # Java: public String getText()
    def get_text(self, rng: Optional[random.Random] = None) -> str:
        rand = rng or random.Random()
        return "".join(rand.choice(self._char_string) for _ in range(self._char_length))


class KaptchaTextCreator(DefaultTextCreator):
    """Java: ``class KaptchaTextCreator extends DefaultTextCreator``."""

    def __init__(self) -> None:
        # The parent's alphabet/length are irrelevant: ``get_text`` is fully overridden.
        # Java inherits ``Configurable`` and simply ignores the inherited config too.
        super().__init__(char_length=6)

    # Java: @Override public String getText()
    def get_text(self, rng: Optional[random.Random] = None) -> str:
        """Return ``"<expr>=?@<answer>"`` -- see the module docstring."""
        rand = rng or random.Random()
        x = rand.randrange(10)  # Java: random.nextInt(10) -> 0..9
        y = rand.randrange(10)
        operands = rand.randrange(3)

        if operands == 0:
            result = x * y
            text = f"{CNUMBERS[x]}*{CNUMBERS[y]}"
        elif operands == 1:
            # ``x != 0`` is checked **before** ``y % x``: Python would raise on ``y % 0``,
            # Java would too (ArithmeticException), so the order is load-bearing.
            if x != 0 and y % x == 0:
                result = y // x
                text = f"{CNUMBERS[y]}/{CNUMBERS[x]}"
            else:
                result = x + y
                text = f"{CNUMBERS[x]}+{CNUMBERS[y]}"
        else:
            if x >= y:
                result = x - y
                text = f"{CNUMBERS[x]}-{CNUMBERS[y]}"
            else:
                result = y - x
                text = f"{CNUMBERS[y]}-{CNUMBERS[x]}"

        # Java: suChinese.append("=?@" + result)
        return f"{text}=?@{result}"


__all__ = ["CNUMBERS", "DEFAULT_CHAR_STRING", "DefaultTextCreator", "KaptchaTextCreator"]
