"""``Arith`` —— ``BigDecimal`` 四则运算的 Python 等价物.

# Migrated from: (no Java test) -- behaviour copied from
#   ruoyi-common/src/main/java/com/ruoyi/common/utils/Arith.java

为什么需要专门测这个文件
------------------------
``Server`` / ``Cpu`` / ``Mem`` / ``Jvm`` 的**每一个**数字都经过这里，而 Java 与
Python 有四处默认行为不同：

1. ``new BigDecimal(double)`` 会带二进制误差（``0.1`` -> ``0.1000000000000000055511…``），
   Java 用的是 ``new BigDecimal(Double.toString(v))`` —— 先转成**十进制字面量**
   再构造。对应 Python 的 ``Decimal(str(v))``。用 ``Decimal(v)`` 就会差出末位。
2. Java ``BigDecimal.divide`` **必须**给 ``scale``，否则除不尽抛
   ``ArithmeticException``；``Arith`` 固定给 10 位并 ``HALF_UP``。
3. Java 的 ``String.format("%.2f")`` 与 ``DecimalFormat`` 都是 **HALF_UP**，
   而 Python 内置 ``round()`` 是**银行家舍入**（``round(2.5) == 2``）。
   所以本模块把 Java 的 ``round`` 改名成 ``round_half_up`` —— 名字本身就是提醒。
4. ``scale < 0`` 在 Java 抛 ``IllegalArgumentException("The scale must be a
   positive integer or zero")``，这里逐字保留。

``Arith.round`` 为什么改名
--------------------------
Python 里已经有 ``round`` 内置函数，同名导出会让调用方误用银行家舍入。改名是
**唯一**的 API 差异，记录在 ``COMPATIBILITY.md`` §39.6。
"""

from __future__ import annotations

import pytest

from app.common.utils.arith import DEF_DIV_SCALE, add, div, mul, round_half_up, sub


class TestBasicArithmetic:
    """``add`` / ``sub`` / ``mul`` —— Java 直接用 ``BigDecimal.xxx``，无 scale。"""

    def test_add(self) -> None:
        # 0.1 + 0.2 在 double 里是 0.30000000000000004；Decimal(str(...)) 给出 0.3
        assert add(0.1, 0.2) == 0.3

    def test_sub(self) -> None:
        assert sub(0.3, 0.1) == 0.2

    def test_mul(self) -> None:
        assert mul(2.5, 4) == 10.0

    def test_mul_keeps_the_decimal_literal_semantics(self) -> None:
        """§39.6：``Double.toString`` 往返是**十进制**，不是二进制真值。"""
        # 0.1 * 3 = 0.30000000000000004（double），但 BigDecimal("0.1") * 3 = 0.3
        assert mul(0.1, 3) == 0.3

    def test_negative_operands(self) -> None:
        assert add(-1.5, 1.5) == 0.0
        assert mul(-2, 3) == -6.0


class TestDiv:
    """``div`` —— 固定 10 位 + ``HALF_UP``，除数为 0 抛 ``ZeroDivisionError``。"""

    def test_default_scale_is_ten(self) -> None:
        assert DEF_DIV_SCALE == 10

    def test_ten_digits_by_default(self) -> None:
        # 1/3 在 Java 里是 0.3333333333（10 位，HALF_UP）
        assert div(1, 3) == 0.3333333333

    def test_half_up_at_the_last_digit(self) -> None:
        """第 11 位是 5 时**进位**（Python 的 ``round`` 会舍去）。"""
        # 2/3 = 0.6666666666666... -> 10 位 HALF_UP = 0.6666666667
        assert div(2, 3) == 0.6666666667

    def test_explicit_scale(self) -> None:
        assert div(1024 * 1024 * 1024, 1024 * 1024 * 1024, 2) == 1.0
        assert div(1, 3, 2) == 0.33
        assert div(2, 3, 2) == 0.67

    def test_dividend_zero_returns_zero(self) -> None:
        """Java 里 ``0 / x`` 走同一分支；显式短路避免 ``0.0000000000`` 的多余刻度。"""
        assert div(0, 5, 2) == 0.0

    def test_divisor_zero_raises(self) -> None:
        """Java: ``BigDecimal.divide`` -> ``ArithmeticException("/ by zero")``."""
        with pytest.raises(ZeroDivisionError):
            div(1, 0, 2)

    def test_negative_scale_raises_with_the_java_message(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            div(1, 2, -1)
        assert str(excinfo.value) == "The scale must be a positive integer or zero"


class TestRoundHalfUp:
    """``round_half_up`` —— 取代 Java 的 ``Arith.round``."""

    @pytest.mark.parametrize(
        ("value", "scale", "expected"),
        [
            (2.5, 0, 3.0),  # Python 的 round(2.5) 是 2
            (3.5, 0, 4.0),  # Python 的 round(3.5) 是 4（巧合）
            (1.005, 2, 1.01),  # double 里 1.005 实际是 1.00499999…，但 str() 给 "1.005"
            (-2.5, 0, -3.0),  # HALF_UP 是"远离零"，不是"向下"
            (0.0, 2, 0.0),
        ],
    )
    def test_half_up(self, value: float, scale: int, expected: float) -> None:
        assert round_half_up(value, scale) == expected

    def test_keeps_the_requested_scale(self) -> None:
        """返回值是 ``float``，所以刻度信息丢失 —— 与 Java 返回 ``double`` 一致。"""
        assert isinstance(round_half_up(1.0, 2), float)

    def test_negative_scale_raises(self) -> None:
        with pytest.raises(ValueError) as excinfo:
            round_half_up(1.5, -1)
        assert str(excinfo.value) == "The scale must be a positive integer or zero"


class TestUsedByServerPanel:
    """``Server`` / ``Cpu`` / ``Mem`` / ``Jvm`` 真正用到的那几个算式。"""

    def test_mem_usage_formula(self) -> None:
        """Java: ``Arith.mul(Arith.div(used, total, 4), 100)`` —— 先 4 位再乘 100。"""
        total = 33550336000
        used = 13420134400
        assert mul(div(used, total, 4), 100) == 40.0

    def test_mem_gb_conversion(self) -> None:
        """Java: ``Arith.div(bytes, 1024 * 1024 * 1024, 2)``."""
        assert div(33550336000, 1024 * 1024 * 1024, 2) == 31.25

    def test_jvm_mb_conversion(self) -> None:
        """Java: ``Jvm`` 用 ``1024 * 1024``，比 ``Mem`` 的 GB 多两位量级。"""
        assert div(1024 * 1024, 1024 * 1024, 2) == 1.0

    def test_cpu_total_quirk_multiplies_without_dividing(self) -> None:
        """§39.2：``Cpu.getTotal()`` 是 ``mul(total, 100)``，**没有** ``/ total``。"""
        assert round_half_up(mul(1234.5, 100), 2) == 123450.0
