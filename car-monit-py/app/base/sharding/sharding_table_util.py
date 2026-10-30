"""通用分表工具类.

# Migrated from: ruoyi-system/src/main/java/com/ruoyi/base/sharding/ShardingTableUtil.java

全部为静态方法，Python 侧收在 :class:`ShardingTableUtil` 的 ``@staticmethod`` 上，
调用点可以逐行照着 Java 写（``ShardingTableUtil.get_table_names_by_date_range(a, b)``）。

三处必须照抄的 Java 语义
------------------------
1. **默认前缀与策略是硬编码的**：``DEFAULT_TABLE_PREFIX = "ods_rt_szdn_snapshot_flow"``、
   ``DEFAULT_STRATEGY = MONTHLY``。Java 从不读 ``ShardingConfig``，这里也不读。
2. **``Calendar.add(MONTH, 1)`` 会夹紧日期且会漂移**：``2025-01-31`` 加一个月是
   ``2025-02-28``，再加一个月是 ``2025-03-28``（不是 ``03-31``）。因此
   :meth:`get_table_names_by_date_range` 里"逐月推进"的写法必须保留，
   不能改成"算出月份差再枚举"。
3. **``parseDate`` 的三种长度**：>=19 按 ``yyyy-MM-dd HH:mm:ss``（Java 的
   ``SimpleDateFormat.parse`` 只解析**前缀**，多余字符被忽略 —— 这里先截到 19 位）；
   ==10 按 ``yyyy-MM-dd``；==8 按 ``yyyyMMdd``；其余 -> ``None``。

已知差异（见 ``COMPATIBILITY.md``）
-----------------------------------
Java 的 ``SimpleDateFormat`` 默认 ``lenient = true``，会把 ``2025-13-45`` 规范化成
合法日期；Python 的 ``strptime`` 是严格的，这类非法日期在这里返回 ``None``
（Java 则返回一个被顺延的日期）。正常 UI 输入不受影响。
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import List, Optional

from app.base.sharding.sharding_config import ShardingStrategy


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _add_months(value: datetime, months: int) -> datetime:
    """等价于 ``Calendar.add(Calendar.MONTH, months)``：日期按目标月**夹紧**。"""
    total = (value.year * 12 + (value.month - 1)) + months
    year, month_index = divmod(total, 12)
    month = month_index + 1
    day = min(value.day, _days_in_month(year, month))
    return value.replace(year=year, month=month, day=day)


def _add_years(value: datetime, years: int) -> datetime:
    """等价于 ``Calendar.add(Calendar.YEAR, years)``：``02-29`` 夹紧到 ``02-28``。"""
    year = value.year + years
    day = min(value.day, _days_in_month(year, value.month))
    return value.replace(year=year, day=day)


class ShardingTableUtil:
    """Java: ``public class ShardingTableUtil``（纯静态工具类）."""

    #: Java: ``public static final String DEFAULT_TABLE_PREFIX``
    DEFAULT_TABLE_PREFIX: str = "ods_rt_szdn_snapshot_flow"

    #: Java: ``private static final ShardingStrategy DEFAULT_STRATEGY = MONTHLY``
    DEFAULT_STRATEGY: ShardingStrategy = ShardingStrategy.MONTHLY

    # ------------------------------------------------------------------ 表名

    # Java: public static String getTableNamePrefix()
    @staticmethod
    def get_table_name_prefix() -> str:
        return ShardingTableUtil.DEFAULT_TABLE_PREFIX

    # Java: public static String getTableNameByDate(Date date)
    @staticmethod
    def get_table_name_by_date(
        date: datetime,
        table_prefix: Optional[str] = None,
        strategy: Optional[ShardingStrategy] = None,
    ) -> str:
        """Java 有两个重载：``(Date)`` 与 ``(String, Date, ShardingStrategy)``。

        Python 用一个方法 + 可选参数表达（默认值与 Java 的 1 参重载一致）。
        """
        prefix = ShardingTableUtil.DEFAULT_TABLE_PREFIX if table_prefix is None else table_prefix
        effective = ShardingTableUtil.DEFAULT_STRATEGY if strategy is None else strategy
        return prefix + "_" + ShardingTableUtil.get_table_suffix(date, effective)

    # Java: public static String getTableNameByDateStr(String, String, ShardingStrategy)
    @staticmethod
    def get_table_name_by_date_str(
        table_prefix: str, date_str: Optional[str], strategy: ShardingStrategy
    ) -> Optional[str]:
        date = ShardingTableUtil.parse_date(date_str)
        if date is None:
            return None
        return ShardingTableUtil.get_table_name_by_date(date, table_prefix, strategy)

    # Java: public static List<String> getTableNamesByDateRange(String, String)
    @staticmethod
    def get_table_names_by_date_range(
        start_date_str: Optional[str],
        end_date_str: Optional[str],
        table_prefix: Optional[str] = None,
        strategy: Optional[ShardingStrategy] = None,
    ) -> List[str]:
        """Java 的两个重载合成一个；前缀 / 策略为空时用 Java 的默认值。

        任一日期解析失败 -> 返回**空列表**（Java 同样是 ``return tableNames;``）。
        """
        prefix = ShardingTableUtil.DEFAULT_TABLE_PREFIX if table_prefix is None else table_prefix
        effective = ShardingTableUtil.DEFAULT_STRATEGY if strategy is None else strategy

        table_names: List[str] = []
        start_date = ShardingTableUtil.parse_date(start_date_str)
        end_date = ShardingTableUtil.parse_date(end_date_str)
        if start_date is None or end_date is None:
            return table_names

        cursor = start_date
        while cursor <= end_date:  # Java: while (!startCal.after(endCal))
            table_name = ShardingTableUtil.get_table_name_by_date(cursor, prefix, effective)
            if table_name not in table_names:
                table_names.append(table_name)
            cursor = ShardingTableUtil.advance_calendar(cursor, effective)
        return table_names

    # Java: public static List<String> getFutureTableNames(String, int, ShardingStrategy)
    @staticmethod
    def get_future_table_names(
        periods: int,
        table_prefix: Optional[str] = None,
        strategy: Optional[ShardingStrategy] = None,
    ) -> List[str]:
        prefix = ShardingTableUtil.DEFAULT_TABLE_PREFIX if table_prefix is None else table_prefix
        effective = ShardingTableUtil.DEFAULT_STRATEGY if strategy is None else strategy

        table_names: List[str] = []
        cursor = datetime.now()
        for _ in range(periods):
            table_name = ShardingTableUtil.get_table_name_by_date(cursor, prefix, effective)
            if table_name not in table_names:
                table_names.append(table_name)
            cursor = ShardingTableUtil.advance_calendar(cursor, effective)
        return table_names

    # Java: public static boolean isOverMonths(String, String, int)
    @staticmethod
    def is_over_months(start_date_str: Optional[str], end_date_str: Optional[str], months: int) -> bool:
        start_date = ShardingTableUtil.parse_date(start_date_str)
        end_date = ShardingTableUtil.parse_date(end_date_str)
        if start_date is None or end_date is None:
            return False
        # Java: endCal.add(Calendar.MONTH, -months); return startCal.before(endCal);
        return start_date < _add_months(end_date, -months)

    # ------------------------------------------------------------------ 周期

    # Java: public static String getCurrentPeriodTable(String, ShardingStrategy)
    @staticmethod
    def get_current_period_table(table_prefix: str, strategy: ShardingStrategy) -> str:
        return ShardingTableUtil.get_table_name_by_date(datetime.now(), table_prefix, strategy)

    # Java: public static Date getPeriodStart(Date, ShardingStrategy)
    @staticmethod
    def get_period_start(date: datetime, strategy: ShardingStrategy) -> datetime:
        if strategy == ShardingStrategy.DAILY:
            return date.replace(hour=0, minute=0, second=0, microsecond=0)
        if strategy == ShardingStrategy.MONTHLY:
            return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if strategy == ShardingStrategy.QUARTERLY:
            # Java: int month = cal.get(Calendar.MONTH);  // 0-based
            month_index = date.month - 1
            quarter_start_month = (month_index // 3) * 3  # 0-based
            return date.replace(
                month=quarter_start_month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        if strategy == ShardingStrategy.YEARLY:
            return date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return date

    # Java: public static Date getPeriodEnd(Date, ShardingStrategy)
    @staticmethod
    def get_period_end(date: datetime, strategy: ShardingStrategy) -> datetime:
        start = ShardingTableUtil.get_period_start(date, strategy)
        if strategy == ShardingStrategy.DAILY:
            start = start + timedelta(days=1)
        elif strategy == ShardingStrategy.MONTHLY:
            start = _add_months(start, 1)
        elif strategy == ShardingStrategy.QUARTERLY:
            start = _add_months(start, 3)
        elif strategy == ShardingStrategy.YEARLY:
            start = _add_years(start, 1)
        # Java: cal.add(Calendar.MILLISECOND, -1);
        return start - timedelta(milliseconds=1)

    # ------------------------------------------------------------------ 格式化

    # Java: public static String formatDate(Date date)
    @staticmethod
    def format_date(date: datetime) -> str:
        return date.strftime("%Y-%m-%d %H:%M:%S")

    # Java: public static String formatDateOnly(Date date)
    @staticmethod
    def format_date_only(date: datetime) -> str:
        return date.strftime("%Y-%m-%d")

    # ------------------------------------------------------------------ 内部

    # Java: private static String getTableSuffix(Date, ShardingStrategy)
    @staticmethod
    def get_table_suffix(date: datetime, strategy: ShardingStrategy) -> str:
        year = date.year
        month = date.month
        day = date.day
        quarter = (month - 1) // 3 + 1

        if strategy == ShardingStrategy.DAILY:
            return f"{year:04d}{month:02d}{day:02d}"
        if strategy == ShardingStrategy.MONTHLY:
            return f"{year:04d}{month:02d}"
        if strategy == ShardingStrategy.QUARTERLY:
            return f"{year:04d}Q{quarter}"
        if strategy == ShardingStrategy.YEARLY:
            return f"{year:04d}"
        # Java: else -> 默认按月分表
        return f"{year:04d}{month:02d}"

    # Java: private static void advanceCalendar(Calendar, ShardingStrategy)
    @staticmethod
    def advance_calendar(cursor: datetime, strategy: ShardingStrategy) -> datetime:
        if strategy == ShardingStrategy.DAILY:
            return cursor + timedelta(days=1)
        if strategy == ShardingStrategy.MONTHLY:
            return _add_months(cursor, 1)
        if strategy == ShardingStrategy.QUARTERLY:
            return _add_months(cursor, 3)
        if strategy == ShardingStrategy.YEARLY:
            return _add_years(cursor, 1)
        return cursor

    # Java: private static Date parseDate(String)
    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """``null`` / 空串 / 长度不在 {8, 10, >=19} -> ``None``；解析失败 -> ``None``."""
        if date_str is None or date_str.strip() == "":
            return None

        trimmed = date_str.strip()
        if len(trimmed) >= 19:
            # Java: SimpleDateFormat("yyyy-MM-dd HH:mm:ss").parse(...) 只消费前 19 个字符
            candidate = trimmed[:19]
            pattern = "%Y-%m-%d %H:%M:%S"
        elif len(trimmed) == 10:
            candidate = trimmed
            pattern = "%Y-%m-%d"
        elif len(trimmed) == 8:
            candidate = trimmed
            pattern = "%Y%m%d"
        else:
            return None

        try:
            return datetime.strptime(candidate, pattern)
        except ValueError:
            # Java: catch (ParseException e) { log.warn(...); return null; }
            return None


__all__ = ["ShardingTableUtil"]
