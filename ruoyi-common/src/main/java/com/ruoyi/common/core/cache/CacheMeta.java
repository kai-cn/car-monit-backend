package com.ruoyi.common.core.cache;

import java.util.Date;

/**
 * 请求级缓存元数据，供大屏响应头输出（X-Cache / X-Data-Age / X-Degrade / X-Data-As-Of）。
 *
 * @author car-monit-backend-java-v3
 */
public class CacheMeta
{
    /** 命中层级：L1 / L2 / MISS / STALE / DEGRADED */
    private String level;

    /** 数据年龄（秒） */
    private long dataAgeSeconds;

    /** 数据来源：API / LEGACY_DB / REDIS / LOCAL */
    private String source;

    /** 降级原因，正常为空 */
    private String degradeReason;

    /** 数据截止时间 */
    private Date dataAsOf;

    public String getLevel()
    {
        return level;
    }

    public void setLevel(String level)
    {
        this.level = level;
    }

    public long getDataAgeSeconds()
    {
        return dataAgeSeconds;
    }

    public void setDataAgeSeconds(long dataAgeSeconds)
    {
        this.dataAgeSeconds = dataAgeSeconds;
    }

    public String getSource()
    {
        return source;
    }

    public void setSource(String source)
    {
        this.source = source;
    }

    public String getDegradeReason()
    {
        return degradeReason;
    }

    public void setDegradeReason(String degradeReason)
    {
        this.degradeReason = degradeReason;
    }

    public Date getDataAsOf()
    {
        return dataAsOf;
    }

    public void setDataAsOf(Date dataAsOf)
    {
        this.dataAsOf = dataAsOf;
    }
}
