package com.ruoyi.flow.mapper;

import java.util.List;
import com.ruoyi.flow.domain.FlowList;
import org.springframework.stereotype.Repository;

/**
 * 审核历史记录Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowListMapper 
{
    /**
     * 查询审核历史记录
     * 
     * @param id 审核历史记录ID
     * @return 审核历史记录
     */
    public FlowList selectFlowListById(String id);

    /**
     * 查询审核历史记录列表
     * 
     * @param flowList 审核历史记录
     * @return 审核历史记录集合
     */
    public List<FlowList> selectFlowListList(FlowList flowList);

    /**
     * 新增审核历史记录
     * 
     * @param flowList 审核历史记录
     * @return 结果
     */
    public int insertFlowList(FlowList flowList);

    /**
     * 修改审核历史记录
     * 
     * @param flowList 审核历史记录
     * @return 结果
     */
    public int updateFlowList(FlowList flowList);

    /**
     * 删除审核历史记录
     * 
     * @param id 审核历史记录ID
     * @return 结果
     */
    public int deleteFlowListById(String id);

    /**
     * 批量删除审核历史记录
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowListByIds(String[] ids);


    /**
     * 查询审核历史记录列表
     *
     * @param flowList 审核历史记录
     * @return 审核历史记录集合
     */
    public List<FlowList> selectFlowListListNew(FlowList flowList);
}
