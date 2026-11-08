package com.ruoyi.manager.domain.vo.bigscreen;

import java.util.List;
import java.util.Map;

/**
 * 导出任务元数据（backend 侧保存，用于任务归属与下载鉴权；文件本身由 api/对象存储持有）。
 *
 * <p>同时保存原提交参数，用于失败重试与“断点续传”（api 无续传接口时按原参数重新提交）。</p>
 *
 * @author car-monit-backend-java-v3
 */
public class ExportTaskMeta
{
    private String taskId;

    private Long userId;

    private String username;

    private String type;

    private String mode;

    private String startTime;

    private String endTime;

    private String purpose;

    /** 原提交过滤条件，重试时复用 */
    private Map<String, String> fuzzyFields;

    /** 原提交展示字段，重试时复用 */
    private List<String> fields;

    /** 最近一次查询到的 api 状态 */
    private String status;

    /** 提交次数（重试 +1） */
    private int attempts;

    /** 最近更新时间 */
    private long updatedAt;

    /** 最近一次错误 */
    private String lastError;

    private long submittedAt;

    public String getTaskId()
    {
        return taskId;
    }

    public void setTaskId(String taskId)
    {
        this.taskId = taskId;
    }

    public Long getUserId()
    {
        return userId;
    }

    public void setUserId(Long userId)
    {
        this.userId = userId;
    }

    public String getUsername()
    {
        return username;
    }

    public void setUsername(String username)
    {
        this.username = username;
    }

    public String getType()
    {
        return type;
    }

    public void setType(String type)
    {
        this.type = type;
    }

    public String getMode()
    {
        return mode;
    }

    public void setMode(String mode)
    {
        this.mode = mode;
    }

    public String getStartTime()
    {
        return startTime;
    }

    public void setStartTime(String startTime)
    {
        this.startTime = startTime;
    }

    public String getEndTime()
    {
        return endTime;
    }

    public void setEndTime(String endTime)
    {
        this.endTime = endTime;
    }

    public String getPurpose()
    {
        return purpose;
    }

    public void setPurpose(String purpose)
    {
        this.purpose = purpose;
    }

    public long getSubmittedAt()
    {
        return submittedAt;
    }

    public void setSubmittedAt(long submittedAt)
    {
        this.submittedAt = submittedAt;
    }

    public Map<String, String> getFuzzyFields()
    {
        return fuzzyFields;
    }

    public void setFuzzyFields(Map<String, String> fuzzyFields)
    {
        this.fuzzyFields = fuzzyFields;
    }

    public List<String> getFields()
    {
        return fields;
    }

    public void setFields(List<String> fields)
    {
        this.fields = fields;
    }

    public String getStatus()
    {
        return status;
    }

    public void setStatus(String status)
    {
        this.status = status;
    }

    public int getAttempts()
    {
        return attempts;
    }

    public void setAttempts(int attempts)
    {
        this.attempts = attempts;
    }

    public long getUpdatedAt()
    {
        return updatedAt;
    }

    public void setUpdatedAt(long updatedAt)
    {
        this.updatedAt = updatedAt;
    }

    public String getLastError()
    {
        return lastError;
    }

    public void setLastError(String lastError)
    {
        this.lastError = lastError;
    }
}
