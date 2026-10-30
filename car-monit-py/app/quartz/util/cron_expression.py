"""Quartz ``CronExpression`` 的逐行等价实现.

# Migrated from: org.quartz.CronExpression (quartz 2.3.2)

为什么自己写一份，而不是用 APScheduler / croniter
-------------------------------------------------
``sys_job.cron_expression`` 里存的是 **Quartz 方言**（6~7 段、``?``、``L``、``W``、``#``），
而且 ``/monitor/job`` 的校验文案、``nextValidTime`` 的取值、以及调度器的"下一次触发时刻"
都必须和线上 Java 完全一致。任何第三方库的方言/边界差异都会让同一个表达式在两端给出
不同的结果，所以这里把 Quartz 2.3.2 的 ``CronExpression`` 原样搬过来，只有这一份实现，
``is_valid`` 与 ``get_next_execution`` 共用它。

必须还原的 Java 怪癖（照抄，别"修"）
------------------------------------
1. **分词用 ``StringTokenizer``**：连续分隔符折叠、**不产生空 token**、忽略首尾分隔符。
   所以 ``"0  0 2 * * ?"``（两个空格）与 ``"0 0 2 * * ?"`` 等价，而 ``" 0 0 2 * * ? "``
   也合法 —— 与 Python 的 ``str.split()`` 恰好一致，但与 ``str.split(" ")`` **不一致**。
2. **``*/0`` 是合法表达式**（Java 实测同样是合法）。``addToSet`` 在
   ``val == ALL_SPEC_INT`` 时把 ``incr <= 0`` 改写成 ``1``，于是 ``*/0`` 退化成 ``*``。
   这一条在 ``_add_to_set`` 里用同样的分支保留：**不要**直接拒绝 ``incr == 0``。
3. **``findNextWhiteSpace`` 的判据恒为真**（``s.charAt(i) != ' ' || s.charAt(i) != '\\t'``，
   两个不等式不可能同时为假），于是 ``getNumericValue`` 总是把**剩余整串**当数字解析。
   这意味着 ``0/10abc`` 这种串会抛 ``NumberFormatException`` 而不是被截断成 ``10``。
4. **``getValue`` 的 ``pos`` 在走到串尾时返回 ``i + 1``**（越过末尾一格），
   后续 ``i >= s.length()`` 的判断依赖这个"超出一格"的行为。
5. **``Calendar.set`` 是 lenient 的**：``MINUTE=60`` 会进位到下一小时、
   ``DAY_OF_MONTH=31`` 在 2 月会溢出到 3 月。:class:`_Cal` 用"民历秒数"重算来还原这个语义
   （见该类的注释），**不能**换成 ``datetime.replace`` —— 那个是严格模式，会直接抛异常。
6. **``?`` 与 ``L``/``W`` 的互斥只在 ``buildExpression`` 里检查**，
   ``getTimeAfter`` 里遇到两者同时生效才抛 ``UnsupportedOperationException``
   （运行时才炸，解析期不报错）。

与 Java 的已知差异
------------------
* ``java.text.ParseException.getMessage()`` 的精确文案只对上面几条固定串做了逐字还原；
  少数由 ``StringIndexOutOfBoundsException`` / ``NumberFormatException`` 兜底转换的
  "``Illegal cron expression format (...)``" 文案里，括号中的异常类名是 Python 的。
  目前**没有调用方**读取该文案（``CronUtils.getInvalidMessage`` 在 RuoYi 里无人调用，
  控制器只用 :func:`is_valid`），见 ``COMPATIBILITY.md``。
* 时区：Java 用 ``TimeZone.getDefault()``（JVM 跑在 GMT+8）；本工程全程使用
  **naive 本地时间**（与 ``sys_job`` / ``sys_job_log`` 的 ``datetime`` 列一致），
  不做任何时区换算。
"""

from __future__ import annotations

import re
from bisect import bisect_left
from datetime import date, datetime
from typing import Dict, List, Optional, Sequence, Tuple

__all__ = [
    "CronParseException",
    "CronExpression",
    "SECOND",
    "MINUTE",
    "HOUR",
    "DAY_OF_MONTH",
    "MONTH",
    "DAY_OF_WEEK",
    "YEAR",
    "ALL_SPEC_INT",
    "NO_SPEC_INT",
    "MAX_YEAR",
]


class CronParseException(Exception):
    """Java: ``java.text.ParseException``.

    重命名原因：``ParseException`` 这个名字在 Python 里没有内建冲突，但同一工程里
    ``email``/``csv`` 等标准库都导出过同名类，容易误 import。保留 ``ParseException``
    别名以方便对照 Java 代码。

    ``error_offset`` 对应 ``ParseException#getErrorOffset()``：Java 的
    ``getMessage()`` **只返回消息本身**，偏移量单独存放。若照 Python 的习惯把两者都传给
    ``Exception``，``str(exc)`` 会变成 ``("msg", 0)`` 这种元组形态 —— 那是错的。
    """

    def __init__(self, message: str, error_offset: int = 0) -> None:
        super().__init__(message)
        self.message = message
        self.error_offset = error_offset

    def __str__(self) -> str:
        return self.message


#: Java: ``java.text.ParseException`` —— 便于逐行对照
ParseException = CronParseException

# Java: protected static final int SECOND = 0; ... YEAR = 6;
SECOND = 0
MINUTE = 1
HOUR = 2
DAY_OF_MONTH = 3
MONTH = 4
DAY_OF_WEEK = 5
YEAR = 6

#: Java: ``ALL_SPEC_INT = 99`` —— ``*`` 的哨兵值
ALL_SPEC_INT = 99
#: Java: ``NO_SPEC_INT = 98`` —— ``?`` 的哨兵值
NO_SPEC_INT = 98

#: Java: ``MAX_YEAR = Calendar.getInstance().get(Calendar.YEAR) + 100``
#: —— **静态**初始化，进程启动时算一次，不随年份变化。
MAX_YEAR = datetime.now().year + 100

_MONTH_MAP: Dict[str, int] = {
    "JAN": 0,
    "FEB": 1,
    "MAR": 2,
    "APR": 3,
    "MAY": 4,
    "JUN": 5,
    "JUL": 6,
    "AUG": 7,
    "SEP": 8,
    "OCT": 9,
    "NOV": 10,
    "DEC": 11,
}

_DAY_MAP: Dict[str, int] = {
    "SUN": 1,
    "MON": 2,
    "TUE": 3,
    "WED": 4,
    "THU": 5,
    "FRI": 6,
    "SAT": 7,
}

#: Java: ``s.matches("^L-[0-9]*[W]?")`` —— ``matches`` 是**整串匹配**。
_L_MINUS_REGEX = re.compile(r"^L-[0-9]*W?$")


# --------------------------------------------------------------------------- 字符串工具
#
# 下面几个函数是 ``java.lang.String`` 的等价物。``slice`` 在越界时不抛异常（Python 语义），
# 而 Java 会抛 ``StringIndexOutOfBoundsException`` 并被 ``buildExpression`` 的
# ``catch (Exception e)`` 转成 ``ParseException``。为了保留"越界即解析失败"的行为，
# 这里统一用 :func:`_char_at` 显式检查。


def _char_at(s: str, index: int) -> str:
    """Java: ``s.charAt(index)`` —— 越界抛 ``IndexError``（外层转 ParseException）。"""
    if index < 0 or index >= len(s):
        raise IndexError("String index out of range: %d" % index)
    return s[index]


def _substring(s: str, begin: int, end: Optional[int] = None) -> str:
    """Java: ``s.substring(begin[, end])`` —— 越界抛 ``IndexError``。"""
    if end is None:
        end = len(s)
    if begin < 0 or end > len(s) or begin > end:
        raise IndexError("begin %d, end %d, length %d" % (begin, end, len(s)))
    return s[begin:end]


def _java_trim(s: str) -> str:
    """Java: ``String.trim()`` —— 去掉两端 ``<= ' '``（0x20）的字符，**不只**空白。"""
    start = 0
    end = len(s)
    while start < end and s[start] <= " ":
        start += 1
    while end > start and s[end - 1] <= " ":
        end -= 1
    return s[start:end]


def _tokenize(s: str, delimiters: str) -> List[str]:
    """Java: ``new StringTokenizer(s, delimiters, false)``.

    ``false`` 表示**不返回分隔符**：连续分隔符折叠成一个、首尾分隔符被丢掉、
    **不会产生空 token**。这与 ``str.split(delimiters)`` 完全等价（后者同样保留
    "相邻分隔符之间"的空串吗？—— 不，Python 的 ``str.split(sep)`` **会**保留空串，
    所以这里必须自己实现，不能用 ``str.split``）。
    """
    tokens: List[str] = []
    current: List[str] = []
    for ch in s:
        if ch in delimiters:
            if current:
                tokens.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        tokens.append("".join(current))
    return tokens


# --------------------------------------------------------------------------- 民历换算
#
# Java ``Calendar`` 的 ``set`` 是 lenient 的：字段越界不会抛异常，而是在下一次
# ``getTime()`` 时向上进位（``MINUTE=60`` -> 下一小时第 0 分；``DAY_OF_MONTH=31`` 在
# 2 月 -> 3 月 3 日；``MONTH=12``（0-based 的 13 月）-> 下一年 1 月）。
# 实现方式：把日历状态压成一个"民历秒数"整数（自公元 1 年 1 月 1 日 00:00:00 起的秒数），
# 每次 ``set`` 都把越界部分重算一遍。这样"月初日 + 天数偏移"的溢出自然进位，
# 与 ``java.util.GregorianCalendar`` 的归一化结果完全一致，且不受时区/夏令时干扰。


def _month_start_ordinal(year: int, month: int) -> int:
    """(year, month) 那个月 1 号的 ``date.toordinal()``；month 允许越界。"""
    total = year * 12 + (month - 1)
    real_year, real_month = divmod(total, 12)
    return date(real_year, real_month + 1, 1).toordinal()


def _parts_to_seconds(
    year: int, month: int, day: int, hour: int, minute: int, second: int
) -> int:
    """把（可能越界的）字段组合成民历秒数 —— 等价于 ``Calendar.computeTime()``."""
    ordinal = _month_start_ordinal(year, month) + (day - 1)
    return ordinal * 86400 + hour * 3600 + minute * 60 + second


def _seconds_to_parts(total: int) -> Tuple[int, int, int, int, int, int]:
    """民历秒数 -> ``(year, month, day, hour, minute, second)``（1-based 月/日）。"""
    days, remainder = divmod(total, 86400)
    day = date.fromordinal(days)
    return (
        day.year,
        day.month,
        day.day,
        remainder // 3600,
        (remainder % 3600) // 60,
        remainder % 60,
    )


class _Cal:
    """``java.util.GregorianCalendar`` 的最小可变替身（只保留本算法用到的字段）.

    Java 的 ``Calendar.set(field, value)`` 只记录字段、``get(field)`` 时才归一化。
    本实现把"归一化"提前到 ``set`` 结束处，结果等价（本算法里从不在同一次
    ``set``/``get`` 之间窥探原始值），但代码短得多。
    """

    __slots__ = ("_seconds",)

    def __init__(self, moment: datetime) -> None:
        self._seconds = moment.toordinal() * 86400 + moment.hour * 3600 + moment.minute * 60 + moment.second

    # ---- Java: Calendar#get(int) ---------------------------------------
    def get(self, field: int) -> int:
        year, month, day, hour, minute, second = _seconds_to_parts(self._seconds)
        if field == YEAR:
            return year
        if field == MONTH:  # Java 的 MONTH 是 0-based
            return month - 1
        if field == DAY_OF_MONTH:
            return day
        if field == HOUR:
            return hour
        if field == MINUTE:
            return minute
        if field == SECOND:
            return second
        raise ValueError("unexpected calendar field: %r" % (field,))

    # ---- Java: Calendar#set(int, int) ----------------------------------
    def set(self, field: int, value: int) -> None:
        year, month, day, hour, minute, second = _seconds_to_parts(self._seconds)
        if field == YEAR:
            year = value
        elif field == MONTH:
            month = value + 1
        elif field == DAY_OF_MONTH:
            day = value
        elif field == HOUR:
            hour = value
        elif field == MINUTE:
            minute = value
        elif field == SECOND:
            second = value
        else:
            raise ValueError("unexpected calendar field: %r" % (field,))
        self._seconds = _parts_to_seconds(year, month, day, hour, minute, second)

    # ---- Java: Calendar#add(Calendar.YEAR, n) --------------------------
    def add_year(self, amount: int) -> None:
        year, month, day, hour, minute, second = _seconds_to_parts(self._seconds)
        self._seconds = _parts_to_seconds(year + amount, month, day, hour, minute, second)

    # ---- Java: Calendar#getTime() -------------------------------------
    def get_time(self) -> datetime:
        year, month, day, hour, minute, second = _seconds_to_parts(self._seconds)
        return datetime(year, month, day, hour, minute, second)


def _moment(year: int, month: int, day: int, hour: int, minute: int, second: int) -> datetime:
    """``new GregorianCalendar(...)`` + 一串 ``set`` 之后 ``getTime()`` 的结果."""
    return datetime(
        *_seconds_to_parts(_parts_to_seconds(year, month, day, hour, minute, second))
    )


def _java_day_of_week(year: int, month: int, day: int) -> int:
    """``Calendar.DAY_OF_WEEK``：周日 = 1 … 周六 = 7。"""
    # Python: 周一 = 0 … 周日 = 6
    return (date(year, month, day).weekday() + 1) % 7 + 1


def _tail(sequence: Sequence[int], value: int) -> Sequence[int]:
    """Java: ``SortedSet#tailSet(value)`` —— 大于等于 ``value`` 的那一段。"""
    index = bisect_left(sequence, value)
    return sequence[index:] if index < len(sequence) else ()


# --------------------------------------------------------------------------- 主体


class CronExpression:
    """Java: ``public final class CronExpression implements Serializable, Cloneable``."""

    def __init__(self, cron_expression: Optional[str]) -> None:
        if cron_expression is None:
            # Java: throw new IllegalArgumentException("cronExpression cannot be null");
            # 注意它**不是** ParseException，所以 isValidExpression 不会吞掉它 ——
            # 线上 POST /monitor/job 缺 cronExpression 时回的就是这条文案。
            raise ValueError("cronExpression cannot be null")

        # Java: this.cronExpression = cronExpression.toUpperCase(Locale.US);
        self.cron_expression: str = cron_expression.upper()

        self.seconds: List[int] = []
        self.minutes: List[int] = []
        self.hours: List[int] = []
        self.days_of_month: List[int] = []
        self.months: List[int] = []
        self.days_of_week: List[int] = []
        self.years: List[int] = []

        self.lastday_of_week: bool = False
        self.nthday_of_week: int = 0
        self.lastday_of_month: bool = False
        self.nearest_weekday: bool = False
        self.lastday_offset: int = 0
        self.expression_parsed: bool = False

        self.build_expression(self.cron_expression)

    # ----------------------------------------------------------------- 解析

    # Java: protected void buildExpression(String expression) throws ParseException
    def build_expression(self, expression: str) -> None:
        self.expression_parsed = True
        self.seconds = []
        self.minutes = []
        self.hours = []
        self.days_of_month = []
        self.months = []
        self.days_of_week = []
        self.years = []

        try:
            expr_on = SECOND
            for token in _tokenize(expression, " \t"):
                if expr_on > YEAR:
                    break
                expr = _java_trim(token)

                # throw an exception if L is used with other days of the month
                if (
                    expr_on == DAY_OF_MONTH
                    and "L" in expr
                    and len(expr) > 1
                    and "," in expr
                ):
                    raise CronParseException(
                        "Support for specifying 'L' and 'LW' with other days of the month is not implemented",
                        -1,
                    )
                # throw an exception if L is used with other days of the week
                if (
                    expr_on == DAY_OF_WEEK
                    and "L" in expr
                    and len(expr) > 1
                    and "," in expr
                ):
                    raise CronParseException(
                        "Support for specifying 'L' with other days of the week is not implemented",
                        -1,
                    )
                # throw an exception if '#' is used more than once in day-of-week
                if expr_on == DAY_OF_WEEK:
                    first_hash = expr.find("#")
                    if first_hash != -1 and expr.find("#", first_hash + 1) != -1:
                        raise CronParseException(
                            'Support for specifying multiple "nth" days is not implemented.', -1
                        )

                for value in _tokenize(expr, ","):
                    self.store_expression_vals(0, value, expr_on)

                expr_on += 1

            if expr_on <= DAY_OF_WEEK:
                raise CronParseException("Unexpected end of expression.", len(expression))

            if expr_on <= YEAR:
                self.store_expression_vals(0, "*", YEAR)

            dow = self.get_set(DAY_OF_WEEK)
            dom = self.get_set(DAY_OF_MONTH)

            # Copying the logic from the UnsupportedOperationException below
            day_of_m_spec = NO_SPEC_INT not in dom
            day_of_w_spec = NO_SPEC_INT not in dow

            if (not day_of_m_spec) or day_of_w_spec:
                if (not day_of_w_spec) or day_of_m_spec:
                    raise CronParseException(
                        "Support for specifying both a day-of-week AND a day-of-month parameter is not implemented.",
                        0,
                    )
        except CronParseException:
            raise
        except Exception as exc:  # noqa: BLE001 —— Java: catch (Exception e)
            raise CronParseException(
                "Illegal cron expression format (%s: %s)" % (type(exc).__name__, exc), 0
            ) from None

        # Java 的 TreeSet 天然有序；这里在解析结束后统一排序一次。
        self.seconds = sorted(set(self.seconds))
        self.minutes = sorted(set(self.minutes))
        self.hours = sorted(set(self.hours))
        self.days_of_month = sorted(set(self.days_of_month))
        self.months = sorted(set(self.months))
        self.days_of_week = sorted(set(self.days_of_week))
        self.years = sorted(set(self.years))

    # Java: protected int storeExpressionVals(int pos, String s, int type)
    def store_expression_vals(self, pos: int, s: str, type_: int) -> int:  # noqa: A002
        incr = 0
        i = self._skip_white_space(pos, s)
        if i >= len(s):
            return i
        c = s[i]
        if (
            "A" <= c <= "Z"
            and s != "L"
            and s != "LW"
            and not _L_MINUS_REGEX.fullmatch(s)
        ):
            sub = _substring(s, i, i + 3)
            sval = -1
            eval_ = -1
            if type_ == MONTH:
                sval = self._get_month_number(sub) + 1
                if sval <= 0:
                    raise CronParseException("Invalid Month value: '%s'" % sub, i)
                if len(s) > i + 3:
                    c = s[i + 3]
                    if c == "-":
                        i += 4
                        sub = _substring(s, i, i + 3)
                        eval_ = self._get_month_number(sub) + 1
                        if eval_ <= 0:
                            raise CronParseException("Invalid Month value: '%s'" % sub, i)
            elif type_ == DAY_OF_WEEK:
                sval = self._get_day_of_week_number(sub)
                if sval < 0:
                    raise CronParseException("Invalid Day-of-Week value: '%s'" % sub, i)
                if len(s) > i + 3:
                    c = s[i + 3]
                    if c == "-":
                        i += 4
                        sub = _substring(s, i, i + 3)
                        eval_ = self._get_day_of_week_number(sub)
                        if eval_ < 0:
                            raise CronParseException("Invalid Day-of-Week value: '%s'" % sub, i)
                    elif c == "#":
                        try:
                            i += 4
                            self.nthday_of_week = int(_substring(s, i))
                            if self.nthday_of_week < 1 or self.nthday_of_week > 5:
                                raise ValueError("out of range")
                        except Exception:  # noqa: BLE001 —— Java: catch (Exception e)
                            raise CronParseException(
                                "A numeric value between 1 and 5 must follow the '#' option", i
                            ) from None
                    elif c == "L":
                        self.lastday_of_week = True
                        i += 1
            else:
                raise CronParseException("Illegal characters for this position: '%s'" % sub, i)

            if eval_ != -1:
                incr = 1
            self._add_to_set(sval, eval_, incr, type_)
            return i + 3

        if c == "?":
            i += 1
            if (i + 1) < len(s) and (s[i] != " " and s[i + 1] != "\t"):
                raise CronParseException("Illegal character after '?': %s" % s[i], i)
            if type_ != DAY_OF_WEEK and type_ != DAY_OF_MONTH:
                raise CronParseException(
                    "'?' can only be specified for Day-of-Month or Day-of-Week.", i
                )
            if type_ == DAY_OF_WEEK and not self.lastday_of_month:
                val = self.days_of_month[-1]
                if val == NO_SPEC_INT:
                    raise CronParseException(
                        "'?' can only be specified for Day-of-Month -OR- Day-of-Week.", i
                    )

            self._add_to_set(NO_SPEC_INT, -1, 0, type_)
            return i

        if c == "*" or c == "/":
            if c == "*" and (i + 1) >= len(s):
                self._add_to_set(ALL_SPEC_INT, -1, incr, type_)
                return i + 1
            elif c == "/" and (
                (i + 1) >= len(s) or s[i + 1] == " " or s[i + 1] == "\t"
            ):
                raise CronParseException("'/' must be followed by an integer.", i)
            elif c == "*":
                i += 1
            c = _char_at(s, i)
            if c == "/":  # is an increment specified?
                i += 1
                if i >= len(s):
                    raise CronParseException("Unexpected end of string.", i)

                incr = self._get_numeric_value(s, i)

                i += 1
                if incr > 10:
                    i += 1
                self._check_increment_range(incr, type_, i)
            else:
                incr = 1

            self._add_to_set(ALL_SPEC_INT, -1, incr, type_)
            return i
        elif c == "L":
            i += 1
            if type_ == DAY_OF_MONTH:
                self.lastday_of_month = True
            if type_ == DAY_OF_WEEK:
                self._add_to_set(7, 7, 0, type_)
            if type_ == DAY_OF_MONTH and len(s) > i:
                c = s[i]
                if c == "-":
                    value, i = self._get_value(0, s, i + 1)
                    self.lastday_offset = value
                    if self.lastday_offset > 30:
                        raise CronParseException("Offset from last day must be <= 30", i + 1)
                if len(s) > i:
                    c = s[i]
                    if c == "W":
                        self.nearest_weekday = True
                        i += 1
            return i
        elif "0" <= c <= "9":
            val = int(c)
            i += 1
            if i >= len(s):
                self._add_to_set(val, -1, -1, type_)
            else:
                c = s[i]
                if "0" <= c <= "9":
                    val, i = self._get_value(val, s, i)
                i = self.check_next(i, s, val, type_)
                return i
        else:
            raise CronParseException("Unexpected character: %s" % c, i)

        return i

    # Java: private void checkIncrementRange(int incr, int type, int idxPos)
    def _check_increment_range(self, incr: int, type_: int, idx_pos: int) -> None:
        if incr > 59 and (type_ == SECOND or type_ == MINUTE):
            raise CronParseException("Increment > 60 : %d" % incr, idx_pos)
        elif incr > 23 and type_ == HOUR:
            raise CronParseException("Increment > 24 : %d" % incr, idx_pos)
        elif incr > 31 and type_ == DAY_OF_MONTH:
            raise CronParseException("Increment > 31 : %d" % incr, idx_pos)
        elif incr > 7 and type_ == DAY_OF_WEEK:
            raise CronParseException("Increment > 7 : %d" % incr, idx_pos)
        elif incr > 12 and type_ == MONTH:
            raise CronParseException("Increment > 12 : %d" % incr, idx_pos)

    # Java: protected int checkNext(int pos, String s, int val, int type)
    def check_next(self, pos: int, s: str, val: int, type_: int) -> int:  # noqa: A002
        end = -1
        i = pos

        if i >= len(s):
            self._add_to_set(val, end, -1, type_)
            return i

        c = s[pos]

        if c == "L":
            if type_ == DAY_OF_WEEK:
                if val < 1 or val > 7:
                    raise CronParseException("Day-of-Week values must be between 1 and 7", -1)
                self.lastday_of_week = True
            else:
                raise CronParseException("'L' option is not valid here. (pos=%d)" % i, i)
            self.get_set(type_).append(val)
            i += 1
            return i

        if c == "W":
            if type_ == DAY_OF_MONTH:
                self.nearest_weekday = True
            else:
                raise CronParseException("'W' option is not valid here. (pos=%d)" % i, i)
            if val > 31:
                raise CronParseException(
                    "The 'W' option does not make sense with values larger than 31 (max number of days in a month)",
                    i,
                )
            self.get_set(type_).append(val)
            i += 1
            return i

        if c == "#":
            if type_ != DAY_OF_WEEK:
                raise CronParseException("'#' option is not valid here. (pos=%d)" % i, i)
            i += 1
            try:
                self.nthday_of_week = int(_substring(s, i))
                if self.nthday_of_week < 1 or self.nthday_of_week > 5:
                    raise ValueError("out of range")
            except Exception:  # noqa: BLE001 —— Java: catch (Exception e)
                raise CronParseException(
                    "A numeric value between 1 and 5 must follow the '#' option", i
                ) from None

            self.get_set(type_).append(val)
            i += 1
            return i

        if c == "-":
            i += 1
            c = _char_at(s, i)
            v = int(c)
            end = v
            i += 1
            if i >= len(s):
                self._add_to_set(val, end, 1, type_)
                return i
            c = s[i]
            if "0" <= c <= "9":
                end, i = self._get_value(v, s, i)
            if i < len(s) and s[i] == "/":
                i += 1
                c = _char_at(s, i)
                v2 = int(c)
                i += 1
                if i >= len(s):
                    self._add_to_set(val, end, v2, type_)
                    return i
                c = s[i]
                if "0" <= c <= "9":
                    v3, i = self._get_value(v2, s, i)
                    self._add_to_set(val, end, v3, type_)
                    return i
                else:
                    self._add_to_set(val, end, v2, type_)
                    return i
            else:
                self._add_to_set(val, end, 1, type_)
                return i

        if c == "/":
            if (i + 1) >= len(s) or s[i + 1] == " " or s[i + 1] == "\t":
                raise CronParseException("'/' must be followed by an integer.", i)

            i += 1
            c = _char_at(s, i)
            v2 = int(c)
            i += 1
            if i >= len(s):
                self._check_increment_range(v2, type_, i)
                self._add_to_set(val, end, v2, type_)
                return i
            c = s[i]
            if "0" <= c <= "9":
                v3, i = self._get_value(v2, s, i)
                self._check_increment_range(v3, type_, i)
                self._add_to_set(val, end, v3, type_)
                return i
            else:
                raise CronParseException("Unexpected character '%s' after '/'" % c, i)

        self._add_to_set(val, end, 0, type_)
        i += 1
        return i

    # Java: protected int skipWhiteSpace(int i, String s)
    def _skip_white_space(self, i: int, s: str) -> int:
        while i < len(s) and (s[i] == " " or s[i] == "\t"):
            i += 1
        return i

    # Java: protected int findNextWhiteSpace(int i, String s)
    def _find_next_white_space(self, i: int, s: str) -> int:
        """判据恒为真（``!= ' ' || != '\\t'``），所以总是走到串尾 —— 照抄 Java 的 bug。"""
        while i < len(s) and (s[i] != " " or s[i] != "\t"):
            i += 1
        return i

    # Java: protected void addToSet(int val, int end, int incr, int type)
    def _add_to_set(self, val: int, end: int, incr: int, type_: int) -> None:
        target = self.get_set(type_)

        if type_ == SECOND or type_ == MINUTE:
            if (val < 0 or val > 59 or end > 59) and val != ALL_SPEC_INT:
                raise CronParseException("Minute and Second values must be between 0 and 59", -1)
        elif type_ == HOUR:
            if (val < 0 or val > 23 or end > 23) and val != ALL_SPEC_INT:
                raise CronParseException("Hour values must be between 0 and 23", -1)
        elif type_ == DAY_OF_MONTH:
            if (
                (val < 1 or val > 31 or end > 31)
                and val != ALL_SPEC_INT
                and val != NO_SPEC_INT
            ):
                raise CronParseException("Day of month values must be between 1 and 31", -1)
        elif type_ == MONTH:
            if (val < 1 or val > 12 or end > 12) and val != ALL_SPEC_INT:
                raise CronParseException("Month values must be between 1 and 12", -1)
        elif type_ == DAY_OF_WEEK:
            if (
                (val == 0 or val > 7 or end > 7)
                and val != ALL_SPEC_INT
                and val != NO_SPEC_INT
            ):
                raise CronParseException("Day-of-Week values must be between 1 and 7", -1)

        if (incr == 0 or incr == -1) and val != ALL_SPEC_INT:
            target.append(val if val != -1 else NO_SPEC_INT)
            return

        start_at = val
        stop_at = end

        if val == ALL_SPEC_INT and incr <= 0:
            incr = 1
            target.append(ALL_SPEC_INT)  # put in a marker, but also fill values

        if type_ == SECOND or type_ == MINUTE:
            if stop_at == -1:
                stop_at = 59
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 0
        elif type_ == HOUR:
            if stop_at == -1:
                stop_at = 23
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 0
        elif type_ == DAY_OF_MONTH:
            if stop_at == -1:
                stop_at = 31
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 1
        elif type_ == MONTH:
            if stop_at == -1:
                stop_at = 12
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 1
        elif type_ == DAY_OF_WEEK:
            if stop_at == -1:
                stop_at = 7
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 1
        elif type_ == YEAR:
            if stop_at == -1:
                stop_at = MAX_YEAR
            if start_at == -1 or start_at == ALL_SPEC_INT:
                start_at = 1970

        # if the end of the range is before the start, then we need to overflow into
        # the next day, month etc.
        maximum = -1
        if stop_at < start_at:
            if type_ == SECOND or type_ == MINUTE:
                maximum = 60
            elif type_ == HOUR:
                maximum = 24
            elif type_ == MONTH:
                maximum = 12
            elif type_ == DAY_OF_WEEK:
                maximum = 7
            elif type_ == DAY_OF_MONTH:
                maximum = 31
            elif type_ == YEAR:
                raise ValueError("Start year must be less than stop year")
            else:
                raise ValueError("Unexpected type encountered")
            stop_at += maximum

        for value in range(start_at, stop_at + 1, incr):
            if maximum == -1:
                target.append(value)
            else:
                reduced = value % maximum
                # 1-indexed ranges should not include 0, and should include their max
                if reduced == 0 and type_ in (MONTH, DAY_OF_WEEK, DAY_OF_MONTH):
                    reduced = maximum
                target.append(reduced)

    # Java: TreeSet<Integer> getSet(int type)
    def get_set(self, type_: int) -> List[int]:  # noqa: A002
        if type_ == SECOND:
            return self.seconds
        if type_ == MINUTE:
            return self.minutes
        if type_ == HOUR:
            return self.hours
        if type_ == DAY_OF_MONTH:
            return self.days_of_month
        if type_ == MONTH:
            return self.months
        if type_ == DAY_OF_WEEK:
            return self.days_of_week
        if type_ == YEAR:
            return self.years
        raise ValueError("unexpected set type: %r" % (type_,))

    # Java: protected ValueSet getValue(int v, String s, int i)
    def _get_value(self, v: int, s: str, i: int) -> Tuple[int, int]:
        c = _char_at(s, i)
        buf = [str(v)]
        while "0" <= c <= "9":
            buf.append(c)
            i += 1
            if i >= len(s):
                break
            c = s[i]
        pos = i if i < len(s) else i + 1
        return int("".join(buf)), pos

    # Java: protected int getNumericValue(String s, int i)
    def _get_numeric_value(self, s: str, i: int) -> int:
        end_of_val = self._find_next_white_space(i, s)
        return int(_substring(s, i, end_of_val))

    # Java: protected int getMonthNumber(String s)
    def _get_month_number(self, s: str) -> int:
        return _MONTH_MAP.get(s, -1)

    # Java: protected int getDayOfWeekNumber(String s)
    def _get_day_of_week_number(self, s: str) -> int:
        return _DAY_MAP.get(s, -1)

    # ----------------------------------------------------------------- 计算

    # Java: public boolean isSatisfiedBy(Date date)
    def is_satisfied_by(self, moment: datetime) -> bool:
        cal = _Cal(moment)
        cal.set(SECOND, cal.get(SECOND))  # 归一化到整秒（Java: set(MILLISECOND, 0)）
        original = cal.get_time()
        cal.set(SECOND, cal.get(SECOND) - 1)
        time_after = self.get_time_after(cal.get_time())
        return time_after is not None and time_after == original

    # Java: public Date getNextValidTimeAfter(Date date)
    def get_next_valid_time_after(self, moment: datetime) -> Optional[datetime]:
        return self.get_time_after(moment)

    # Java: public Date getTimeAfter(Date afterTime)
    def get_time_after(self, after_time: datetime) -> Optional[datetime]:  # noqa: C901
        cl = _Cal(after_time)
        # move ahead one second, since we're computing the time *after* the given time
        cl.set(SECOND, cl.get(SECOND) + 1)

        after_time = cl.get_time()
        got_one = False

        seconds = self.seconds
        minutes = self.minutes
        hours = self.hours
        days_of_month = self.days_of_month
        days_of_week = self.days_of_week
        months = self.months
        years = self.years

        while not got_one:
            if cl.get(YEAR) > 2999:  # prevent endless loop...
                return None

            sec = cl.get(SECOND)
            min_ = cl.get(MINUTE)

            # get second.................................................
            st = _tail(seconds, sec)
            if st:
                sec = st[0]
            else:
                sec = seconds[0]
                min_ += 1
                cl.set(MINUTE, min_)
            cl.set(SECOND, sec)

            min_ = cl.get(MINUTE)
            hr = cl.get(HOUR)
            t = -1

            # get minute.................................................
            st = _tail(minutes, min_)
            if st:
                t = min_
                min_ = st[0]
            else:
                min_ = minutes[0]
                hr += 1
            if min_ != t:
                cl.set(SECOND, 0)
                cl.set(MINUTE, min_)
                self._set_calendar_hour(cl, hr)
                continue
            cl.set(MINUTE, min_)

            hr = cl.get(HOUR)
            day = cl.get(DAY_OF_MONTH)
            t = -1

            # get hour...................................................
            st = _tail(hours, hr)
            if st:
                t = hr
                hr = st[0]
            else:
                hr = hours[0]
                day += 1
            if hr != t:
                cl.set(SECOND, 0)
                cl.set(MINUTE, 0)
                cl.set(DAY_OF_MONTH, day)
                self._set_calendar_hour(cl, hr)
                continue
            cl.set(HOUR, hr)

            day = cl.get(DAY_OF_MONTH)
            mon = cl.get(MONTH) + 1  # 1-based
            t = -1
            tmon = mon

            # get day...................................................
            day_of_m_spec = NO_SPEC_INT not in days_of_month
            day_of_w_spec = NO_SPEC_INT not in days_of_week
            if day_of_m_spec and not day_of_w_spec:  # get day by day of month rule
                st = _tail(days_of_month, day)
                if self.lastday_of_month:
                    if not self.nearest_weekday:
                        t = day
                        day = self.get_last_day_of_month(mon, cl.get(YEAR))
                        day -= self.lastday_offset
                        if t > day:
                            mon += 1
                            if mon > 12:
                                mon = 1
                                tmon = 3333  # ensure test of mon != tmon fails
                                cl.add_year(1)
                            day = 1
                    else:
                        t = day
                        day = self.get_last_day_of_month(mon, cl.get(YEAR))
                        day -= self.lastday_offset

                        ldom = self.get_last_day_of_month(mon, cl.get(YEAR))
                        dow = _java_day_of_week(cl.get(YEAR), mon, day)

                        if dow == 7 and day == 1:  # Calendar.SATURDAY
                            day += 2
                        elif dow == 7:
                            day -= 1
                        elif dow == 1 and day == ldom:  # Calendar.SUNDAY
                            day -= 2
                        elif dow == 1:
                            day += 1

                        n_time = _moment(cl.get(YEAR), mon, day, hr, min_, sec)
                        if n_time < after_time:
                            day = 1
                            mon += 1
                elif self.nearest_weekday:
                    t = day
                    day = days_of_month[0]

                    ldom = self.get_last_day_of_month(mon, cl.get(YEAR))
                    dow = _java_day_of_week(cl.get(YEAR), mon, day)

                    if dow == 7 and day == 1:
                        day += 2
                    elif dow == 7:
                        day -= 1
                    elif dow == 1 and day == ldom:
                        day -= 2
                    elif dow == 1:
                        day += 1

                    n_time = _moment(cl.get(YEAR), mon, day, hr, min_, sec)
                    if n_time < after_time:
                        day = days_of_month[0]
                        mon += 1
                elif st:
                    t = day
                    day = st[0]
                    # make sure we don't over-run a short month, such as february
                    last_day = self.get_last_day_of_month(mon, cl.get(YEAR))
                    if day > last_day:
                        day = days_of_month[0]
                        mon += 1
                else:
                    day = days_of_month[0]
                    mon += 1

                if day != t or mon != tmon:
                    cl.set(SECOND, 0)
                    cl.set(MINUTE, 0)
                    cl.set(HOUR, 0)
                    cl.set(DAY_OF_MONTH, day)
                    cl.set(MONTH, mon - 1)
                    continue
            elif day_of_w_spec and not day_of_m_spec:  # get day by day of week rule
                if self.lastday_of_week:
                    dow = days_of_week[0]  # desired d-o-w
                    c_dow = _java_day_of_week(*_ymd(cl))
                    days_to_add = 0
                    if c_dow < dow:
                        days_to_add = dow - c_dow
                    if c_dow > dow:
                        days_to_add = dow + (7 - c_dow)

                    l_day = self.get_last_day_of_month(mon, cl.get(YEAR))

                    if day + days_to_add > l_day:  # did we already miss the last one?
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, 1)
                        cl.set(MONTH, mon)  # no '- 1' here: promoting the month
                        continue

                    # find date of last occurrence of this day in this month...
                    while (day + days_to_add + 7) <= l_day:
                        days_to_add += 7

                    day += days_to_add

                    if days_to_add > 0:
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, day)
                        cl.set(MONTH, mon - 1)
                        continue
                elif self.nthday_of_week != 0:
                    dow = days_of_week[0]  # desired d-o-w
                    c_dow = _java_day_of_week(*_ymd(cl))
                    days_to_add = 0
                    if c_dow < dow:
                        days_to_add = dow - c_dow
                    elif c_dow > dow:
                        days_to_add = dow + (7 - c_dow)

                    day_shifted = days_to_add > 0

                    day += days_to_add
                    week_of_month = day // 7
                    if day % 7 > 0:
                        week_of_month += 1

                    days_to_add = (self.nthday_of_week - week_of_month) * 7
                    day += days_to_add
                    if days_to_add < 0 or day > self.get_last_day_of_month(mon, cl.get(YEAR)):
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, 1)
                        cl.set(MONTH, mon)  # no '- 1' here: promoting the month
                        continue
                    elif days_to_add > 0 or day_shifted:
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, day)
                        cl.set(MONTH, mon - 1)
                        continue
                else:
                    c_dow = _java_day_of_week(*_ymd(cl))
                    dow = days_of_week[0]  # desired d-o-w
                    st = _tail(days_of_week, c_dow)
                    if st:
                        dow = st[0]

                    days_to_add = 0
                    if c_dow < dow:
                        days_to_add = dow - c_dow
                    if c_dow > dow:
                        days_to_add = dow + (7 - c_dow)

                    l_day = self.get_last_day_of_month(mon, cl.get(YEAR))

                    if day + days_to_add > l_day:  # will we pass the end of the month?
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, 1)
                        cl.set(MONTH, mon)  # no '- 1' here: promoting the month
                        continue
                    elif days_to_add > 0:  # are we switching days?
                        cl.set(SECOND, 0)
                        cl.set(MINUTE, 0)
                        cl.set(HOUR, 0)
                        cl.set(DAY_OF_MONTH, day + days_to_add)
                        cl.set(MONTH, mon - 1)
                        continue
            else:
                raise NotImplementedError(
                    "Support for specifying both a day-of-week AND a day-of-month parameter is not implemented."
                )
            cl.set(DAY_OF_MONTH, day)

            mon = cl.get(MONTH) + 1  # 1-based
            year = cl.get(YEAR)
            t = -1

            # test for expressions that never generate a valid fire date, but keep looping...
            if year > MAX_YEAR:
                return None

            # get month...................................................
            st = _tail(months, mon)
            if st:
                t = mon
                mon = st[0]
            else:
                mon = months[0]
                year += 1
            if mon != t:
                cl.set(SECOND, 0)
                cl.set(MINUTE, 0)
                cl.set(HOUR, 0)
                cl.set(DAY_OF_MONTH, 1)
                cl.set(MONTH, mon - 1)
                cl.set(YEAR, year)
                continue
            cl.set(MONTH, mon - 1)

            year = cl.get(YEAR)
            t = -1

            # get year...................................................
            st = _tail(years, year)
            if st:
                t = year
                year = st[0]
            else:
                return None  # ran out of years...

            if year != t:
                cl.set(SECOND, 0)
                cl.set(MINUTE, 0)
                cl.set(HOUR, 0)
                cl.set(DAY_OF_MONTH, 1)
                cl.set(MONTH, 0)
                cl.set(YEAR, year)
                continue
            cl.set(YEAR, year)

            got_one = True

        return cl.get_time()

    # Java: protected void setCalendarHour(Calendar cal, int hour)
    def _set_calendar_hour(self, cal: _Cal, hour: int) -> None:
        cal.set(HOUR, hour)
        if cal.get(HOUR) != hour and hour != 24:
            cal.set(HOUR, hour + 1)

    # Java: public Date getTimeBefore(Date endTime) —— NOT YET IMPLEMENTED
    def get_time_before(self, end_time: datetime) -> Optional[datetime]:
        return None

    # Java: public Date getFinalFireTime() —— NOT YET IMPLEMENTED
    def get_final_fire_time(self) -> Optional[datetime]:
        return None

    # Java: protected boolean isLeapYear(int year)
    def is_leap_year(self, year: int) -> bool:
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    # Java: protected int getLastDayOfMonth(int monthNum, int year)
    def get_last_day_of_month(self, month_num: int, year: int) -> int:
        if month_num == 1:
            return 31
        if month_num == 2:
            return 29 if self.is_leap_year(year) else 28
        if month_num == 3:
            return 31
        if month_num == 4:
            return 30
        if month_num == 5:
            return 31
        if month_num == 6:
            return 30
        if month_num == 7:
            return 31
        if month_num == 8:
            return 31
        if month_num == 9:
            return 30
        if month_num == 10:
            return 31
        if month_num == 11:
            return 30
        if month_num == 12:
            return 31
        raise ValueError("Illegal month number: %d" % month_num)

    # Java: public String getCronExpression() / toString()
    def get_cron_expression(self) -> str:
        return self.cron_expression

    def __str__(self) -> str:  # Java: toString()
        return self.cron_expression

    def __repr__(self) -> str:
        return "CronExpression(%r)" % self.cron_expression

    # ----------------------------------------------------------------- 静态工厂

    # Java: public static boolean isValidExpression(String cronExpression)
    @staticmethod
    def is_valid_expression(cron_expression: Optional[str]) -> bool:
        try:
            CronExpression(cron_expression)
        except CronParseException:
            return False
        return True

    # Java: public static void validateExpression(String cronExpression)
    @staticmethod
    def validate_expression(cron_expression: Optional[str]) -> None:
        CronExpression(cron_expression)


def _ymd(cal: _Cal) -> Tuple[int, int, int]:
    """``(year, month, day)`` —— 用于算 ``DAY_OF_WEEK``（Java 的 ``Calendar.get`` 里没有这一格）。"""
    return cal.get(YEAR), cal.get(MONTH) + 1, cal.get(DAY_OF_MONTH)
