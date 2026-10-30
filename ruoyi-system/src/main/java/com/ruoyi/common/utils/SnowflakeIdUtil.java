package com.ruoyi.common.utils;

import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 雪花算法工具类（ID中嵌入时间戳）
 * <p>
 * 【设计思路】
 * 雪花算法生成的ID结构：[1bit符号位][41bit时间戳][10bit机器ID][12bit序列号]
 * 通过解析ID中的时间戳部分，可以确定数据所属的分区，从而避免全表扫描
 * </p>
 * 
 * <p>【单条记录查询优化原理】</p>
 * <pre>
 * 1. 从雪花ID中提取41位时间戳
 * 2. 根据时间戳计算出月份
 * 3. 根据月份确定分区名（如 p202508）
 * 4. 使用分区提示直接查询目标分区，避免扫描所有分区
 * </pre>
 * 
 * @author ruoyi
 */
public class SnowflakeIdUtil {

    /**
     * 时间戳偏移量（2021-01-01 00:00:00）
     * 用于缩小时间戳范围，增加可用年限
     */
    private static final long TIMESTAMP_OFFSET = 1609459200000L;

    /**
     * 时间戳占用位数（41位）
     */
    private static final long TIMESTAMP_BITS = 41L;

    /**
     * 最大时间戳值
     */
    private static final long MAX_TIMESTAMP = (1L << 41) - 1;

    /**
     * 机器ID占用位数（10位）
     */
    private static final long WORKER_ID_BITS = 10L;

    /**
     * 序列号占用位数（12位）
     */
    private static final long SEQUENCE_BITS = 12L;

    /**
     * 机器ID左移位数
     */
    private static final long WORKER_ID_SHIFT = SEQUENCE_BITS;

    /**
     * 时间戳左移位数
     */
    private static final long TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS;

    /**
     * 日期格式化器（线程安全）
     */
    private static final ThreadLocal<SimpleDateFormat> MONTH_FORMATTER = 
            ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyyMM"));

    /**
     * 从雪花ID解析时间戳
     * 
     * <p>【算法原理】</p>
     * 将ID右移22位（12位序列号+10位机器ID），得到时间戳部分，
     * 然后加上偏移量得到实际时间戳（毫秒）
     * 
     * @param id 雪花ID（字符串形式，需可解析为long）
     * @return 对应的Date对象，如果解析失败返回null
     */
    public static Date parseDateFromId(String id) {
        try {
            long longId = Long.parseLong(id);
            return parseDateFromId(longId);
        } catch (NumberFormatException e) {
            // ID格式不正确，返回null
            return null;
        }
    }

    /**
     * 从雪花ID解析时间戳（long类型）
     * 
     * @param id 雪花ID
     * @return 对应的Date对象
     */
    public static Date parseDateFromId(long id) {
        // 右移22位获取时间戳部分，然后加上偏移量
        long timestamp = (id >> TIMESTAMP_SHIFT) + TIMESTAMP_OFFSET;
        
        // 校验时间戳有效性
        if (timestamp < TIMESTAMP_OFFSET || timestamp > System.currentTimeMillis() + MAX_TIMESTAMP) {
            return null;
        }
        
        return new Date(timestamp);
    }

    /**
     * 从雪花ID解析月份（用于分区定位）
     * 
     * <p>【使用场景】</p>
     * 单条记录查询时，通过ID解析出月份，确定目标分区，
     * 使用分区提示直接查询，避免全表扫描
     * 
     * @param id 雪花ID
     * @return 月份字符串（格式：yyyyMM），如 202508
     */
    public static String parseMonthFromId(String id) {
        Date date = parseDateFromId(id);
        if (date == null) {
            return null;
        }
        return MONTH_FORMATTER.get().format(date);
    }

    /**
     * 从雪花ID解析分区名
     * 
     * <p>【返回格式】</p>
     * p + yyyyMM，如 p202508
     * 
     * @param id 雪花ID
     * @return 分区名，如果解析失败返回null
     */
    public static String parsePartitionFromId(String id) {
        String month = parseMonthFromId(id);
        if (month == null) {
            return null;
        }
        return "p" + month;
    }

    /**
     * 估算ID对应的时间范围（前后各1天）
     * 
     * <p>【使用场景】</p>
     * 当无法精确解析分区时，使用时间范围查询缩小扫描范围
     * 
     * @param id 雪花ID
     * @return 时间范围数组，[0]为开始时间，[1]为结束时间
     */
    public static Date[] estimateTimeRange(String id) {
        Date estimatedDate = parseDateFromId(id);
        if (estimatedDate == null) {
            return null;
        }

        java.util.Calendar cal = java.util.Calendar.getInstance();
        cal.setTime(estimatedDate);
        
        // 开始时间：前1天
        cal.add(java.util.Calendar.DAY_OF_MONTH, -1);
        Date start = cal.getTime();
        
        // 结束时间：后1天
        cal.add(java.util.Calendar.DAY_OF_MONTH, 2);
        Date end = cal.getTime();
        
        return new Date[]{start, end};
    }

    /**
     * 验证ID是否为有效的雪花ID
     * 
     * @param id 待验证的ID
     * @return true=有效，false=无效
     */
    public static boolean isValidSnowflakeId(String id) {
        if (id == null || id.isEmpty()) {
            return false;
        }
        
        try {
            long longId = Long.parseLong(id);
            Date date = parseDateFromId(longId);
            return date != null;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}
