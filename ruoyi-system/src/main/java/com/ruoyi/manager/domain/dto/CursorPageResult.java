package com.ruoyi.manager.domain.dto;

import java.io.Serializable;
import java.util.Date;
import java.util.List;

/**
 * Keyset 游标分页响应 DTO
 *
 * 与传统 PageInfo 的区别：
 *   - 不返回 total / totalPage（千万级数据 COUNT(*) 很慢，避免每次都扫）
 *   - 返回 nextCursorXXX，前端/调用方用这个值继续翻下一页
 *   - hasNextPage 通过"多查 1 条"来判断，避免 COUNT(*)
 *
 * @param <T> 记录类型
 */
public class CursorPageResult<T> implements Serializable {

    private static final long serialVersionUID = 1L;

    /** 当前页数据 */
    private List<T> list;

    /** 每页条数 */
    private Integer pageSize;

    /** 是否有下一页 */
    private Boolean hasNextPage;

    /** 是否第一页 */
    private Boolean isFirstPage;

    /** 下一页的游标时间（等于本页最后一条的 snapshottime） */
    private Date nextCursorTime;

    /** 下一页的游标主键（等于本页最后一条的 big_id） */
    private Long nextCursorId;

    public CursorPageResult() {}

    /**
     * 构建分页结果
     *
     * @param rawList  原始查询结果（数量 = pageSize + 1，多的一条用来判断 hasNextPage）
     * @param pageSize 每页条数
     */
    public CursorPageResult(List<T> rawList, Integer pageSize) {
        this.pageSize = pageSize;
        if (rawList == null || rawList.isEmpty()) {
            this.list = rawList;
            this.hasNextPage = false;
            this.isFirstPage = true;
            this.nextCursorTime = null;
            this.nextCursorId = null;
            return;
        }

        // 如果查询到的数量 > pageSize，说明还有下一页
        this.hasNextPage = rawList.size() > pageSize;

        // 只保留 pageSize 条记录返回
        if (this.hasNextPage) {
            this.list = rawList.subList(0, pageSize);
        } else {
            this.list = rawList;
        }
    }

    // ============= getter / setter =============

    public List<T> getList() { return list; }
    public void setList(List<T> list) { this.list = list; }

    public Integer getPageSize() { return pageSize; }
    public void setPageSize(Integer pageSize) { this.pageSize = pageSize; }

    public Boolean getHasNextPage() { return hasNextPage; }
    public void setHasNextPage(Boolean hasNextPage) { this.hasNextPage = hasNextPage; }

    public Boolean getIsFirstPage() { return isFirstPage; }
    public void setIsFirstPage(Boolean isFirstPage) { this.isFirstPage = isFirstPage; }

    public Date getNextCursorTime() { return nextCursorTime; }
    public void setNextCursorTime(Date nextCursorTime) { this.nextCursorTime = nextCursorTime; }

    public Long getNextCursorId() { return nextCursorId; }
    public void setNextCursorId(Long nextCursorId) { this.nextCursorId = nextCursorId; }
}
