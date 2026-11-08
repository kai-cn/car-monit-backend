package com.ruoyi.integration.api;

import java.util.List;

/**
 * api 分页结果（统一 backend 内部使用的形态，避免直接暴露 api 的 TableDataInfo 原始结构）。
 *
 * @author car-monit-backend-java-v3
 */
public class ApiPageResult<T>
{
    private List<T> rows;

    private long total;

    private int pageNum;

    private int pageSize;

    public ApiPageResult()
    {
    }

    public ApiPageResult(List<T> rows, long total, int pageNum, int pageSize)
    {
        this.rows = rows;
        this.total = total;
        this.pageNum = pageNum;
        this.pageSize = pageSize;
    }

    public List<T> getRows()
    {
        return rows;
    }

    public void setRows(List<T> rows)
    {
        this.rows = rows;
    }

    public long getTotal()
    {
        return total;
    }

    public void setTotal(long total)
    {
        this.total = total;
    }

    public int getPageNum()
    {
        return pageNum;
    }

    public void setPageNum(int pageNum)
    {
        this.pageNum = pageNum;
    }

    public int getPageSize()
    {
        return pageSize;
    }

    public void setPageSize(int pageSize)
    {
        this.pageSize = pageSize;
    }
}
