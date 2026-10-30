package com.ruoyi.base.sharding;

import com.ruoyi.base.sharding.ShardingConfig.ShardingStrategy;
import lombok.extern.slf4j.Slf4j;

import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.List;

/**
 * 通用分表工具类
 * <p>
 * 支持多种分表策略：按月、按日、按季度、按年
 * 提供分表名生成、时间范围计算等通用方法
 * </p>
 */
@Slf4j
public class ShardingTableUtil {

    /**
     * 默认表名前缀
     */
    public static final String DEFAULT_TABLE_PREFIX = "ods_rt_szdn_snapshot_flow";

    /**
     * 默认分表策略
     */
    private static final ShardingStrategy DEFAULT_STRATEGY = ShardingStrategy.MONTHLY;

    /**
     * 获取表名前缀（兼容旧代码）
     */
    public static String getTableNamePrefix() {
        return DEFAULT_TABLE_PREFIX;
    }

    /**
     * 根据日期获取分表名（使用默认配置）
     *
     * @param date 日期
     * @return 分表名
     */
    public static String getTableNameByDate(Date date) {
        return getTableNameByDate(DEFAULT_TABLE_PREFIX, date, DEFAULT_STRATEGY);
    }

    /**
     * 根据日期获取分表名
     *
     * @param tablePrefix 表名前缀
     * @param date        日期
     * @param strategy    分表策略
     * @return 分表名
     */
    public static String getTableNameByDate(String tablePrefix, Date date, ShardingStrategy strategy) {
        String suffix = getTableSuffix(date, strategy);
        return tablePrefix + "_" + suffix;
    }

    /**
     * 根据日期字符串获取分表名
     *
     * @param tablePrefix 表名前缀
     * @param dateStr     日期字符串（yyyy-MM-dd HH:mm:ss 或 yyyy-MM-dd）
     * @param strategy    分表策略
     * @return 分表名
     */
    public static String getTableNameByDateStr(String tablePrefix, String dateStr, ShardingStrategy strategy) {
        Date date = parseDate(dateStr);
        return date != null ? getTableNameByDate(tablePrefix, date, strategy) : null;
    }

    /**
     * 根据时间范围获取所有涉及的分表名列表
     *
     * @param startDateStr 开始日期字符串
     * @param endDateStr   结束日期字符串
     * @return 分表名列表
     */
    public static List<String> getTableNamesByDateRange(String startDateStr, String endDateStr) {
        return getTableNamesByDateRange(DEFAULT_TABLE_PREFIX, startDateStr, endDateStr, DEFAULT_STRATEGY);
    }

    /**
     * 根据时间范围获取所有涉及的分表名列表
     *
     * @param tablePrefix 表名前缀
     * @param startDateStr 开始日期字符串
     * @param endDateStr   结束日期字符串
     * @param strategy    分表策略
     * @return 分表名列表
     */
    public static List<String> getTableNamesByDateRange(String tablePrefix, String startDateStr,
                                                        String endDateStr, ShardingStrategy strategy) {
        List<String> tableNames = new ArrayList<>();

        Date startDate = parseDate(startDateStr);
        Date endDate = parseDate(endDateStr);

        if (startDate == null || endDate == null) {
            return tableNames;
        }

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);

        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);

        // 根据策略设置日历字段
        while (!startCal.after(endCal)) {
            String tableName = getTableNameByDate(tablePrefix, startCal.getTime(), strategy);
            if (!tableNames.contains(tableName)) {
                tableNames.add(tableName);
            }
            advanceCalendar(startCal, strategy);
        }

        return tableNames;
    }

    /**
     * 获取未来N个周期的分表名
     *
     * @param months 未来月份数
     * @return 分表名列表
     */
    public static List<String> getFutureTableNames(int months) {
        return getFutureTableNames(DEFAULT_TABLE_PREFIX, months, DEFAULT_STRATEGY);
    }

    /**
     * 获取未来N个周期的分表名
     *
     * @param tablePrefix 表名前缀
     * @param periods     未来周期数
     * @param strategy    分表策略
     * @return 分表名列表
     */
    public static List<String> getFutureTableNames(String tablePrefix, int periods, ShardingStrategy strategy) {
        List<String> tableNames = new ArrayList<>();
        Calendar calendar = Calendar.getInstance();

        for (int i = 0; i < periods; i++) {
            String tableName = getTableNameByDate(tablePrefix, calendar.getTime(), strategy);
            if (!tableNames.contains(tableName)) {
                tableNames.add(tableName);
            }
            advanceCalendar(calendar, strategy);
        }

        return tableNames;
    }

    /**
     * 判断时间范围是否超过指定月份数
     *
     * @param startDateStr 开始日期
     * @param endDateStr   结束日期
     * @param months       月份数
     * @return 是否超过
     */
    public static boolean isOverMonths(String startDateStr, String endDateStr, int months) {
        Date startDate = parseDate(startDateStr);
        Date endDate = parseDate(endDateStr);

        if (startDate == null || endDate == null) {
            return false;
        }

        Calendar startCal = Calendar.getInstance();
        startCal.setTime(startDate);
        Calendar endCal = Calendar.getInstance();
        endCal.setTime(endDate);
        endCal.add(Calendar.MONTH, -months);

        return startCal.before(endCal);
    }

    /**
     * 获取分表后缀
     *
     * @param date     日期
     * @param strategy 分表策略
     * @return 分表后缀（如 202508, 20250801, 2025Q3, 2025）
     */
    private static String getTableSuffix(Date date, ShardingStrategy strategy) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(date);
        int year = cal.get(Calendar.YEAR);
        int month = cal.get(Calendar.MONTH) + 1;
        int day = cal.get(Calendar.DAY_OF_MONTH);
        int quarter = (month - 1) / 3 + 1;

        if (strategy == ShardingStrategy.DAILY) {
            return String.format("%04d%02d%02d", year, month, day);
        } else if (strategy == ShardingStrategy.MONTHLY) {
            return String.format("%04d%02d", year, month);
        } else if (strategy == ShardingStrategy.QUARTERLY) {
            return String.format("%04dQ%d", year, quarter);
        } else if (strategy == ShardingStrategy.YEARLY) {
            return String.format("%04d", year);
        } else {
            return String.format("%04d%02d", year, month); // 默认按月分表
        }
    }

    /**
     * 推进日历到下一个周期
     *
     * @param calendar  日历
     * @param strategy 分表策略
     */
    private static void advanceCalendar(Calendar calendar, ShardingStrategy strategy) {
        if (strategy == ShardingStrategy.DAILY) {
            calendar.add(Calendar.DAY_OF_MONTH, 1);
        } else if (strategy == ShardingStrategy.MONTHLY) {
            calendar.add(Calendar.MONTH, 1);
        } else if (strategy == ShardingStrategy.QUARTERLY) {
            calendar.add(Calendar.MONTH, 3);
        } else if (strategy == ShardingStrategy.YEARLY) {
            calendar.add(Calendar.YEAR, 1);
        }
    }

    /**
     * 解析日期字符串
     *
     * @param dateStr 日期字符串
     * @return 日期对象
     */
    private static Date parseDate(String dateStr) {
        if (dateStr == null || dateStr.trim().isEmpty()) {
            return null;
        }

        String trimmedDate = dateStr.trim();
        SimpleDateFormat sdf;

        if (trimmedDate.length() >= 19) {
            sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        } else if (trimmedDate.length() == 10) {
            sdf = new SimpleDateFormat("yyyy-MM-dd");
        } else if (trimmedDate.length() == 8) {
            sdf = new SimpleDateFormat("yyyyMMdd");
        } else {
            return null;
        }

        try {
            return sdf.parse(trimmedDate);
        } catch (ParseException e) {
            log.warn("【分表工具】日期解析失败: {}", dateStr);
            return null;
        }
    }

    /**
     * 获取当前周期的分表名
     *
     * @param tablePrefix 表名前缀
     * @param strategy    分表策略
     * @return 当前周期的分表名
     */
    public static String getCurrentPeriodTable(String tablePrefix, ShardingStrategy strategy) {
        return getTableNameByDate(tablePrefix, new Date(), strategy);
    }

    /**
     * 获取指定周期的起始日期
     *
     * @param date     日期
     * @param strategy 分表策略
     * @return 周期起始日期
     */
    public static Date getPeriodStart(Date date, ShardingStrategy strategy) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(date);

        switch (strategy) {
            case DAILY:
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                cal.set(Calendar.MILLISECOND, 0);
                break;
            case MONTHLY:
                cal.set(Calendar.DAY_OF_MONTH, 1);
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                cal.set(Calendar.MILLISECOND, 0);
                break;
            case QUARTERLY:
                int month = cal.get(Calendar.MONTH);
                int quarterStartMonth = (month / 3) * 3;
                cal.set(Calendar.MONTH, quarterStartMonth);
                cal.set(Calendar.DAY_OF_MONTH, 1);
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                cal.set(Calendar.MILLISECOND, 0);
                break;
            case YEARLY:
                cal.set(Calendar.MONTH, 0);
                cal.set(Calendar.DAY_OF_MONTH, 1);
                cal.set(Calendar.HOUR_OF_DAY, 0);
                cal.set(Calendar.MINUTE, 0);
                cal.set(Calendar.SECOND, 0);
                cal.set(Calendar.MILLISECOND, 0);
                break;
        }

        return cal.getTime();
    }

    /**
     * 获取指定周期的结束日期
     *
     * @param date     日期
     * @param strategy 分表策略
     * @return 周期结束日期
     */
    public static Date getPeriodEnd(Date date, ShardingStrategy strategy) {
        Calendar cal = Calendar.getInstance();
        cal.setTime(getPeriodStart(date, strategy));

        switch (strategy) {
            case DAILY:
                cal.add(Calendar.DAY_OF_MONTH, 1);
                break;
            case MONTHLY:
                cal.add(Calendar.MONTH, 1);
                break;
            case QUARTERLY:
                cal.add(Calendar.MONTH, 3);
                break;
            case YEARLY:
                cal.add(Calendar.YEAR, 1);
                break;
        }

        cal.add(Calendar.MILLISECOND, -1);
        return cal.getTime();
    }

    /**
     * 格式化日期为字符串
     */
    public static String formatDate(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(date);
    }

    /**
     * 格式化日期为字符串（仅日期部分）
     */
    public static String formatDateOnly(Date date) {
        return new SimpleDateFormat("yyyy-MM-dd").format(date);
    }
}
