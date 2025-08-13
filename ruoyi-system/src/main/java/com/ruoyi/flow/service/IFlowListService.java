package com.ruoyi.flow.service;

import java.util.List;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowList;

/**
 * 审核历史记录Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowListService 
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
     * 新增或者修改审核历史记录
     * 
     * @param flowList 审核历史记录
     * @return 结果
     */
    public AjaxResult saveFlowList(FlowList flowList);

    /**
     * 批量删除审核历史记录
     * 
     * @param ids 需要删除的审核历史记录ID
     * @return 结果
     */
    public AjaxResult deleteFlowListByIds(String[] ids);

    /**
     * 删除审核历史记录信息
     * 
     * @param id 审核历史记录ID
     * @return 结果
     */
    public AjaxResult deleteFlowListById(String id);


    /**
     * 查询审核历史记录列表
     *
     * @param flowList 审核历史记录
     * @return 审核历史记录集合
     */
    public List<FlowList> selectFlowListListNew(FlowList flowList);
}
