"""验证码配置 / the two kaptcha producers.

# Migrated from: ruoyi-framework/src/main/java/com/ruoyi/framework/config/CaptchaConfig.java

Java wires two ``DefaultKaptcha`` beans, and ``CaptchaController`` picks one by
``ruoyi.captchaType``:

===============  ==========================================  ==========================
bean              text source                                 used when
===============  ==========================================  ==========================
captchaProducer   kaptcha ``DefaultTextCreator`` (4 chars)    ``captchaType == "char"``
captchaProducerMath  :class:`KaptchaTextCreator` (``a+b=?@c``)  ``captchaType == "math"``
===============  ==========================================  ==========================

``ruoyi.captchaType`` is ``math`` in ``application.yml``, so only the second bean is reachable
in production. The first is kept because the branch exists in the controller.

Pixel parity: **not achievable, and not attempted**
---------------------------------------------------
kaptcha renders with ``java.awt`` (``Graphics2D``, ``GradientPaint``, ``ShadowGimpy``). Pillow
uses a different rasteriser, different hinting and a different notion of "Arial". Two
renderings of the same string will never be byte-identical, and no client can depend on
captcha pixels -- the contract is "a human can read the expression", not "these exact bytes".

What *is* preserved:

* geometry -- 160x60 for both producers, 1px border, text colour, font size 38/35;
* the arithmetic ``a+b=?`` and its answer, i.e. the only part that is machine-consumed;
* JPEG output (``ImageIO.write(image, "jpg", ...)``) at Pillow's default quality 75, which is
  also the JDK's default JPEG quality.

What is approximated: ``ShadowGimpy`` becomes "draw a translucent offset copy, then the real
text"; ``DefaultNoise`` becomes random single-pixel dots. The visual effect is equivalent;
the pixels are not. Recorded in ``COMPATIBILITY.md``.

Two small divergences worth knowing:

* ``ImageIO.write`` on kaptcha's ``TYPE_INT_ARGB`` image silently flattens alpha against
  black-then-white; drawing on an opaque gradient is what the output actually looks like.
* kaptcha picks a **random font per character** from ``kaptcha.textproducer.font.names``
  (``Arial,Courier``). Reproduced, because mixing fonts is visible.
"""

from __future__ import annotations

import io
import random
from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.framework.config.kaptcha_text_creator import (
    DEFAULT_CHAR_STRING,
    DefaultTextCreator,
    KaptchaTextCreator,
)

#: ``java.awt.Color`` constants used by ``CaptchaConfig`` / kaptcha defaults.
WHITE: Tuple[int, int, int] = (255, 255, 255)
LIGHT_GRAY: Tuple[int, int, int] = (192, 192, 192)
BLACK: Tuple[int, int, int] = (0, 0, 0)
BLUE: Tuple[int, int, int] = (0, 0, 255)

#: kaptcha ``Config`` default: ``KAPTCHA_BORDER_THICKNESS = 1``.
DEFAULT_BORDER_THICKNESS = 1

#: kaptcha ``Config`` default: ``KAPTCHA_TEXTPRODUCER_CHAR_SPACE = 2``.
DEFAULT_CHAR_SPACE = 2

#: Font files tried in order. ``Arial``/``Courier New`` exist on Windows; DejaVu is the
#: usual fallback on Linux containers. ``ImageFont.load_default`` is the last resort so the
#: endpoint never fails just because a font is missing.
_FONT_CANDIDATES = {
    "Arial": ("arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"),
    "Courier": ("cour.ttf", "Courier New.ttf", "DejaVuSansMono.ttf", "LiberationMono-Regular.ttf"),
}


@dataclass
class KaptchaConfig:
    """Java: kaptcha ``com.google.code.kaptcha.util.Config`` (only the keys RuoYi sets)."""

    image_width: int = 200
    image_height: int = 50
    border: bool = True
    border_color: Tuple[int, int, int] = BLACK
    border_thickness: int = DEFAULT_BORDER_THICKNESS
    text_font_size: int = 40
    text_font_color: Tuple[int, int, int] = BLACK
    text_font_names: Sequence[str] = field(default_factory=lambda: ("Arial", "Courier"))
    text_char_space: int = DEFAULT_CHAR_SPACE
    noise_color: Tuple[int, int, int] = BLACK
    #: ``KAPTCHA_NOISE_IMPL = NoNoise`` -> ``False``. ``DefaultNoise`` -> ``True``.
    noise_enabled: bool = True
    #: ``KAPTCHA_TEXTPRODUCER_CHAR_STRING``; empty means kaptcha's built-in alphabet.
    char_string: str = DEFAULT_CHAR_STRING


class DefaultKaptcha:
    """Java: ``com.google.code.kaptcha.impl.DefaultKaptcha``.

    ``createText``/``createImage`` are split exactly as in Java so the controller's two-way
    split on ``@`` can be migrated line by line.
    """

    def __init__(self, config: KaptchaConfig, text_producer: object) -> None:
        self._config = config
        self._text_producer = text_producer

    @property
    def config(self) -> KaptchaConfig:
        return self._config

    # Java: public String createText()
    def create_text(self) -> str:
        return self._text_producer.get_text()

    # Java: public BufferedImage createImage(String text)
    def create_image(self, text: str) -> Image.Image:
        """Render ``text`` onto a fresh RGB image."""
        config = self._config
        image = Image.new("RGB", (config.image_width, config.image_height), WHITE)
        self._draw_background(image)
        if config.noise_enabled:
            self._draw_noise(image)
        text_layer = self._render_text_layer(text)
        # Java: ``ShadowGimpy`` -- a blurred, offset copy underneath the crisp text.
        shadow = _tint_alpha(
            text_layer.filter(ImageFilter.GaussianBlur(radius=1)), (90, 60, 60), 150
        )
        image.paste(shadow, (2, 3), shadow)
        image.paste(text_layer, (0, 0), text_layer)
        if config.border:
            self._draw_border(image)
        return image

    # Java: DefaultBackground.addBackground(Graphics2D, width, height, Config)
    def _draw_background(self, image: Image.Image) -> None:
        """``GradientPaint`` from ``Color.WHITE`` (top) to ``Color.LIGHT_GRAY`` (bottom)."""
        draw = ImageDraw.Draw(image)
        height = self._config.image_height
        for y in range(height):
            ratio = y / max(1, height - 1)
            color = tuple(
                round(WHITE[i] + (LIGHT_GRAY[i] - WHITE[i]) * ratio) for i in range(3)
            )
            draw.line([(0, y), (self._config.image_width, y)], fill=color)

    # Java: DefaultNoise.addNoise(Graphics2D, BufferedImage, Config)
    def _draw_noise(self, image: Image.Image) -> None:
        """Approximation: scattered single-pixel dots in ``kaptcha.noise.color``."""
        draw = ImageDraw.Draw(image)
        config = self._config
        rand = random.Random()
        # kaptcha draws roughly half a dot per pixel-column; ~4 per mille is visually close
        # without obscuring a 6-character expression.
        count = (config.image_width * config.image_height) // 250
        for _ in range(count):
            x = rand.randrange(config.image_width)
            y = rand.randrange(config.image_height)
            draw.point((x, y), fill=config.noise_color)

    # Java: DefaultBorder.addBorder(Graphics2D, width, height, Config)
    def _draw_border(self, image: Image.Image) -> None:
        draw = ImageDraw.Draw(image)
        config = self._config
        for offset in range(config.border_thickness):
            draw.rectangle(
                [
                    offset,
                    offset,
                    config.image_width - offset - 1,
                    config.image_height - offset - 1,
                ],
                outline=config.border_color,
            )

    # Java: DefaultWordRenderer.renderWord(Graphics2D, word, width, height, Config)
    def _render_text_layer(self, text: str) -> Image.Image:
        """Transparent layer holding the text, ready to be composited.

        Returns RGBA so the shadow copy can be offset without repainting the background.
        """
        config = self._config
        layer = Image.new("RGBA", (config.image_width, config.image_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        rand = random.Random()

        fonts = [_load_font(name, config.text_font_size) for name in config.text_font_names]
        if not fonts:  # pragma: no cover - placeholder guard
            fonts = [ImageFont.load_default(size=config.text_font_size)]

        # Measure with the first font to centre the whole word, then draw each glyph with a
        # randomly chosen font -- that is what makes kaptcha's output look uneven.
        widths = [draw.textbbox((0, 0), ch, font=fonts[0])[2] for ch in text]
        total = sum(widths) + config.text_char_space * max(0, len(text) - 1)
        x = max(0, (config.image_width - total) // 2)
        # Baseline: centre vertically. Java uses FontMetrics ascent/descent; Pillow's anchors
        # make ``lm`` (left-middle) the equivalent, so no manual offset is needed.
        baseline_shift = rand.randint(-2, 2)

        for index, char in enumerate(text):
            font = fonts[rand.randrange(len(fonts))]
            y = config.image_height // 2 + baseline_shift + rand.randint(-3, 3)
            draw.text((x, y), char, font=font, fill=config.text_font_color, anchor="lm")
            x += widths[index] + config.text_char_space
        return layer


def _load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    """Resolve a Java font name (``Arial``/``Courier``) to a Pillow font object."""
    for candidate in _FONT_CANDIDATES.get(name, (f"{name}.ttf",)):
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    # ``load_default(size=...)`` needs Pillow >= 10.1; requirements.txt pins 11.1.0.
    return ImageFont.load_default(size=size)


def _tint_alpha(layer: Image.Image, color: Tuple[int, int, int], alpha: int) -> Image.Image:
    """Recolour a text layer to ``color`` at ``alpha`` -- the shadow of ``ShadowGimpy``."""
    tinted = Image.new("RGBA", layer.size, color + (0,))
    tinted.putalpha(layer.getchannel("A").point(lambda value: value * alpha // 255))
    return tinted


# --------------------------------------------------------------------------- beans
#: Java: ``@Bean(name = "captchaProducer")`` -- the ``char`` producer.
CHAR_PRODUCER_CONFIG = KaptchaConfig(
    image_width=160,
    image_height=60,
    border=True,
    border_color=BLACK,  # default; CaptchaConfig does not override it for this bean
    text_font_color=BLACK,
    text_font_size=38,
    text_font_names=("Arial", "Courier"),
    text_char_space=DEFAULT_CHAR_SPACE,
    noise_color=BLACK,
    noise_enabled=True,  # default NoiseProducer = DefaultNoise
    char_string=DEFAULT_CHAR_STRING,
)

#: Java: ``@Bean(name = "captchaProducerMath")`` -- the ``math`` producer.
MATH_PRODUCER_CONFIG = KaptchaConfig(
    image_width=160,
    image_height=60,
    border=True,
    border_color=(105, 179, 90),  # KAPTCHA_BORDER_COLOR = "105,179,90"
    text_font_color=BLUE,
    text_font_size=35,
    text_font_names=("Arial", "Courier"),
    text_char_space=3,
    noise_color=WHITE,
    noise_enabled=False,  # KAPTCHA_NOISE_IMPL = NoNoise
    char_string=DEFAULT_CHAR_STRING,
)

_CAPTCHA_PRODUCER: Optional[DefaultKaptcha] = None
_CAPTCHA_PRODUCER_MATH: Optional[DefaultKaptcha] = None


def get_captcha_producer() -> DefaultKaptcha:
    """Java: ``@Resource(name = "captchaProducer")``."""
    global _CAPTCHA_PRODUCER
    if _CAPTCHA_PRODUCER is None:
        # kaptcha instantiates the text producer reflectively from
        # ``kaptcha.textproducer.impl``; here it is passed explicitly. ``char.length`` is 4.
        _CAPTCHA_PRODUCER = DefaultKaptcha(
            CHAR_PRODUCER_CONFIG, DefaultTextCreator(char_length=4)
        )
    return _CAPTCHA_PRODUCER


def get_captcha_producer_math() -> DefaultKaptcha:
    """Java: ``@Resource(name = "captchaProducerMath")``."""
    global _CAPTCHA_PRODUCER_MATH
    if _CAPTCHA_PRODUCER_MATH is None:
        _CAPTCHA_PRODUCER_MATH = DefaultKaptcha(MATH_PRODUCER_CONFIG, KaptchaTextCreator())
    return _CAPTCHA_PRODUCER_MATH


def reset_captcha_producers() -> None:
    """Test helper: drop both beans."""
    global _CAPTCHA_PRODUCER, _CAPTCHA_PRODUCER_MATH
    _CAPTCHA_PRODUCER = None
    _CAPTCHA_PRODUCER_MATH = None


def encode_jpeg(image: Image.Image) -> bytes:
    """Java: ``ImageIO.write(image, "jpg", os)`` + ``os.toByteArray()``.

    The JDK's default JPEG quality is 0.75 and Pillow's default ``quality`` is 75, so passing
    no argument keeps the two encoders' *intent* identical even though the DCT output differs.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


__all__ = [
    "WHITE",
    "LIGHT_GRAY",
    "BLACK",
    "BLUE",
    "KaptchaConfig",
    "DefaultKaptcha",
    "CHAR_PRODUCER_CONFIG",
    "MATH_PRODUCER_CONFIG",
    "get_captcha_producer",
    "get_captcha_producer_math",
    "reset_captcha_producers",
    "encode_jpeg",
]
