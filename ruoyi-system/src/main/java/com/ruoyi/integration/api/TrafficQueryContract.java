package com.ruoyi.integration.api;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.temporal.ChronoUnit;
import java.util.Map;

/**
 * 查询契约校验（设计文档 §4.3「强制约束」）。
 *
 * <ul>
 *   <li>时间范围必填；缺省默认最近 7 天；最大 365 天；</li>
 *   <li>模糊查询至少 2 个字符（车牌 1 字符拒绝）；</li>
 *   <li>列表 pageSize ≤ 100，from+size ≤ 10000，深页要求 search_after。</li>
 * </ul>
 *
 * @author car-monit-backend-java-v3
 */
public final class TrafficQueryContract
{
    public static final int DEFAULT_RANGE_DAYS = 7;

    public static final int MAX_RANGE_DAYS = 365;

    public static final int MAX_PAGE_SIZE = 100;

    public static final int MAX_FROM_SIZE = 10000;

    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private static final DateTimeFormatter DATETIME = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    private TrafficQueryContract()
    {
    }

    /**
     * 标准化时间范围，返回 {start, end}（yyyy-MM-dd HH:mm:ss）。
     */
    public static String[] normalizeDateTimeRange(String start, String end)
    {
        LocalDateTime endTime = parseDateTime(end, LocalDateTime.now(), true);
        LocalDateTime startTime = parseDateTime(start, endTime.minusDays(DEFAULT_RANGE_DAYS), false);
        validateRange(startTime, endTime);
        return new String[] { DATETIME.format(startTime), DATETIME.format(endTime) };
    }

    /**
     * 标准化日期范围，返回 {start, end}（yyyy-MM-dd），用于预聚合按天统计。
     */
    public static String[] normalizeDateRange(String start, String end)
    {
        LocalDateTime endTime = parseDateTime(end, LocalDateTime.now(), true);
        LocalDateTime startTime = parseDateTime(start, endTime.minusDays(DEFAULT_RANGE_DAYS), false);
        validateRange(startTime, endTime);
        return new String[] { DATE.format(startTime.toLocalDate()), DATE.format(endTime.toLocalDate()) };
    }

    /**
     * 只校验、不重写（用于 legacy SQL 兜底路径，保持原有日期字符串语义）。
     */
    public static void validateDateTimeRange(String start, String end)
    {
        normalizeDateTimeRange(start, end);
    }

    public static void validatePaging(int pageNum, int pageSize)
    {
        if (pageNum < 1 || pageSize < 1)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "分页参数非法: pageNum=" + pageNum + ", pageSize=" + pageSize);
        }
        if (pageSize > MAX_PAGE_SIZE)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "pageSize 不能超过 " + MAX_PAGE_SIZE + ": " + pageSize);
        }
        if ((long) pageNum * pageSize > MAX_FROM_SIZE)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "深页超出 from+size 上限 " + MAX_FROM_SIZE + "，请使用 search_after");
        }
    }

    public static void validateFuzzy(String field, String value)
    {
        if (value == null || value.trim().isEmpty())
        {
            return;
        }
        if (value.trim().length() < 2)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "模糊查询字段 " + field + " 至少需要 2 个字符");
        }
    }

    public static void validateFuzzyMap(Map<String, String> fuzzyFields)
    {
        if (fuzzyFields == null)
        {
            return;
        }
        for (Map.Entry<String, String> entry : fuzzyFields.entrySet())
        {
            validateFuzzy(entry.getKey(), entry.getValue());
        }
    }

    public static String today()
    {
        return DATE.format(LocalDate.now());
    }

    public static String defaultStartDate()
    {
        return DATE.format(LocalDate.now().minusDays(DEFAULT_RANGE_DAYS));
    }

    private static void validateRange(LocalDateTime start, LocalDateTime end)
    {
        if (start.isAfter(end))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "开始时间不能晚于结束时间");
        }
        if (ChronoUnit.DAYS.between(start, end) > MAX_RANGE_DAYS)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "时间范围不能超过 " + MAX_RANGE_DAYS + " 天");
        }
    }

    private static LocalDateTime parseDateTime(String value, LocalDateTime defaultValue, boolean endOfDay)
    {
        if (value == null || value.trim().isEmpty())
        {
            return defaultValue;
        }
        String trimmed = value.trim();
        try
        {
            if (trimmed.length() == 10)
            {
                LocalDate date = LocalDate.parse(trimmed, DATE);
                return endOfDay ? date.atTime(23, 59, 59) : date.atStartOfDay();
            }
            return LocalDateTime.parse(trimmed, DATETIME);
        }
        catch (DateTimeParseException e)
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "contract",
                    "时间格式非法: " + trimmed + "，支持 yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss");
        }
    }
}
