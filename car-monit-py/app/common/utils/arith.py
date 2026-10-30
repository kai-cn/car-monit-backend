"""精确的浮点数运算 / exact decimal arithmetic.

# Migrated from: ruoyi-common/src/main/java/com/ruoyi/common/utils/Arith.java

Java 用 ``BigDecimal`` + ``RoundingMode.HALF_UP`` 做"精确"浮点运算，并统一以
``new BigDecimal(Double.toString(v))`` 构造 —— 注意是 **``Double.toString``**，不是
``new BigDecimal(double)``。前者取的是该 double 的**最短可回读十进制串**（
``0.1`` → ``"0.1"``），后者取的是二进制真值（``0.1`` → ``0.1000000000000000055511…``）。
两者结果差别很大，所以这里统一走 ``Decimal(str(v))``，与 Java 一致。

``round`` 改名为 ``round_half_up``
---------------------------------
Java 的方法名叫 ``round``。Python 有内建 ``round``，同名的模块级函数虽然合法，
但 ``from app.common.utils.arith import round`` 会静默覆盖内建函数 —— 本项目此前
已因同类问题改过 ``AjaxResult.put`` -> ``put_chain``（见 ``COMPATIBILITY.md`` §5），
这里沿用同一套命名约定。

四舍五入 vs Python 内建 ``round``
--------------------------------
Python 的 ``round()`` 是 **银行家舍入**（round-half-even）：``round(2.675, 2)``
得到 ``2.67``，Java 的 ``HALF_UP`` 得到 ``2.68``。`Server` 的百分比、`Mem` 的
GB 换算都直接展示给前端，用错会有肉眼可见的偏差，因此**不要**把这里的调用换成
内建 ``round``。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

#: Java: ``Arith.DEF_DIV_SCALE``
DEF_DIV_SCALE: int = 10


def _decimal(value: float) -> Decimal:
    """Java: ``new BigDecimal(Double.toString(v))``."""
    return Decimal(str(value))


def _to_float(value: Decimal) -> float:
    return float(value)


def add(value1: float, value2: float) -> float:
    """Java: ``Arith.add(double, double)`` —— 精确加法。"""
    return _to_float(_decimal(value1) + _decimal(value2))


def sub(value1: float, value2: float) -> float:
    """Java: ``Arith.sub(double, double)`` —— 精确减法。"""
    return _to_float(_decimal(value1) - _decimal(value2))


def mul(value1: float, value2: float) -> float:
    """Java: ``Arith.mul(double, double)`` —— 精确乘法。"""
    return _to_float(_decimal(value1) * _decimal(value2))


def div(value1: float, value2: float, scale: int = DEF_DIV_SCALE) -> float:
    """Java: ``Arith.div(double, double[, int scale])`` —— 精确除法，``HALF_UP``。

    ``scale < 0`` 时抛 ``ValueError``（Java 抛 ``IllegalArgumentException``）。

    被除数为 **0** 时直接返回 ``0.0``，**不做**除法 —— 这一行是为了避开
    ``BigDecimal.divide`` 在除数为 0 时的 ``ArithmeticException``，照抄。
    因此 ``div(0, 0, 4)`` 返回 ``0.0`` 而不是报错。
    """
    if scale < 0:
        raise ValueError("The scale must be a positive integer or zero")
    dividend = _decimal(value1)
    divisor = _decimal(value2)
    if dividend == 0:
        return 0.0
    # Java: b1.divide(b2, scale, RoundingMode.HALF_UP)
    # Decimal 的 ``/`` 默认保留 28 位有效数字，必须显式 quantize 到 ``scale`` 才是
    # BigDecimal 的语义。除数为 0 时 Decimal 抛 DivisionByZero（ArithmeticError 子类），
    # 与 BigDecimal 的 ArithmeticException 同族。
    quantum = Decimal(1).scaleb(-scale)
    return _to_float((dividend / divisor).quantize(quantum, rounding=ROUND_HALF_UP))


def round_half_up(value: float, scale: int) -> float:
    """Java: ``Arith.round(double, int)`` —— ``HALF_UP`` 保留 ``scale`` 位小数。"""
    if scale < 0:
        raise ValueError("The scale must be a positive integer or zero")
    try:
        quantum = Decimal(1).scaleb(-scale)
        return _to_float(_decimal(value).quantize(quantum, rounding=ROUND_HALF_UP))
    except InvalidOperation:  # pragma: no cover - NaN / Infinity
        # Java: BigDecimal 对 NaN 直接抛 NumberFormatException
        raise ValueError(f"Cannot round {value!r}") from None


__all__ = ["DEF_DIV_SCALE", "add", "sub", "mul", "div", "round_half_up"]
