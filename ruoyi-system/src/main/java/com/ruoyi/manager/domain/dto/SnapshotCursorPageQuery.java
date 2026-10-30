package com.ruoyi.manager.domain.dto;

import java.io.Serializable;
import java.util.Date;

/**
 * 分区表跨月份 Keyset 游标分页请求 DTO
 *
 * 使用方式：
 *   1. 首次查询：只传 startTime / endTime / 其他筛选条件 / pageSize
 *              （不需要传 lastSnapshottime 和 lastBigId）
 *   2. 后续翻页：把上一页响应对象中返回的游标值
 *              （nextCursorSnapshottime / nextCursorBigId）
 *              填回本请求对象，继续调用
 *
 * 设计要点：
 *   - startTime / endTime 必须用半开区间 [startTime, endTime)
 *   - 分区表查询必须走分区剪枝，所以 snapshottime 上不包任何函数
 *   - Keyset 游标用 (时间 + 主键) 组合排序，保证排序唯一，避免跳数据
 *   - 查 LIMIT + 1 条（比请求多一条），用来判断是否有下一页
 */
public class SnapshotCursorPageQuery implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 车牌（可选） */
    private String platenumber;

    /** 门架编号（可选） */
    private String gantrycode;

    /** 路段编号（可选） */
    private String sectioncode;

    /** 起始时间（必填，>=） */
    private Date startTime;

    /** 结束时间（必填，<） */
    private Date endTime;

    /** 每页条数（默认20，最大1000） */
    private Integer pageSize = 20;

    /** 上一页最后一条记录的 snapshottime（首次查询传 null） */
    private Date lastSnapshottime;

    /** 上一页最后一条记录的 big_id（首次查询传 null） */
    private Long lastBigId;

    // ============= 业务校验方法 =============

    /** 校验必填项 */
    public void validate() {
        if (startTime == null || endTime == null) {
            throw new IllegalArgumentException("startTime 和 endTime 不能为空");
        }
        if (!startTime.before(endTime)) {
            throw new IllegalArgumentException("startTime 必须早于 endTime");
        }
        if (pageSize == null || pageSize <= 0) {
            pageSize = 20;
        }
        if (pageSize > 1000) {
            pageSize = 1000;
        }
    }

    /** 是否首次查询（没有游标） */
    public boolean isFirstPage() {
        return lastSnapshottime == null || lastBigId == null;
    }

    // ============= getter / setter =============

    public String getPlatenumber() { return platenumber; }
    public void setPlatenumber(String platenumber) { this.platenumber = platenumber; }

    public String getGantrycode() { return gantrycode; }
    public void setGantrycode(String gantrycode) { this.gantrycode = gantrycode; }

    public String getSectioncode() { return sectioncode; }
    public void setSectioncode(String sectioncode) { this.sectioncode = sectioncode; }

    public Date getStartTime() { return startTime; }
    public void setStartTime(Date startTime) { this.startTime = startTime; }

    public Date getEndTime() { return endTime; }
    public void setEndTime(Date endTime) { this.endTime = endTime; }

    public Integer getPageSize() { return pageSize; }
    public void setPageSize(Integer pageSize) { this.pageSize = pageSize; }

    public Date getLastSnapshottime() { return lastSnapshottime; }
    public void setLastSnapshottime(Date lastSnapshottime) { this.lastSnapshottime = lastSnapshottime; }

    public Long getLastBigId() { return lastBigId; }
    public void setLastBigId(Long lastBigId) { this.lastBigId = lastBigId; }
}
