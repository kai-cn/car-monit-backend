package com.ruoyi.manager.domain.vo.bigscreen;

import java.io.Serializable;
import java.util.Map;

/**
 * 全字段导出审批请求（待审批时存 Redis，审批通过后再提交 api）。
 *
 * @author car-monit-backend-java-v3
 */
public class ExportApprovalRequest implements Serializable
{
    private static final long serialVersionUID = 1L;

    private String requestId;

    private Long userId;

    private String username;

    private String type;

    private String mode;

    private String startTime;

    private String endTime;

    private String purpose;

    private Map<String, String> fuzzyFields;

    /** pending / approved / rejected */
    private String status;

    private long createdAt;

    private Long approvedBy;

    private long approvedAt;

    private String rejectReason;

    private String taskId;

    public String getRequestId()
    {
        return requestId;
    }

    public void setRequestId(String requestId)
    {
        this.requestId = requestId;
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

    public Map<String, String> getFuzzyFields()
    {
        return fuzzyFields;
    }

    public void setFuzzyFields(Map<String, String> fuzzyFields)
    {
        this.fuzzyFields = fuzzyFields;
    }

    public String getStatus()
    {
        return status;
    }

    public void setStatus(String status)
    {
        this.status = status;
    }

    public long getCreatedAt()
    {
        return createdAt;
    }

    public void setCreatedAt(long createdAt)
    {
        this.createdAt = createdAt;
    }

    public Long getApprovedBy()
    {
        return approvedBy;
    }

    public void setApprovedBy(Long approvedBy)
    {
        this.approvedBy = approvedBy;
    }

    public long getApprovedAt()
    {
        return approvedAt;
    }

    public void setApprovedAt(long approvedAt)
    {
        this.approvedAt = approvedAt;
    }

    public String getRejectReason()
    {
        return rejectReason;
    }

    public void setRejectReason(String rejectReason)
    {
        this.rejectReason = rejectReason;
    }

    public String getTaskId()
    {
        return taskId;
    }

    public void setTaskId(String taskId)
    {
        this.taskId = taskId;
    }
}
