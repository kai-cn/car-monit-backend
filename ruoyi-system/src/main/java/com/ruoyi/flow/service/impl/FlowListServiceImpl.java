package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.flow.mapper.FlowListMapper;
import com.ruoyi.flow.domain.FlowList;
import com.ruoyi.flow.service.IFlowListService;

import java.util.List;

/**
 * 审核历史记录Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowListServiceImpl implements IFlowListService 
{
    @Autowired
    private FlowListMapper flowListMapper;

    /**
     * 查询审核历史记录
     * 
     * @param id 审核历史记录ID
     * @return 审核历史记录
     */
    @Override
    public FlowList selectFlowListById(String id)
    {
        return flowListMapper.selectFlowListById(id);
    }

    /**
     * 查询审核历史记录列表
     * 
     * @param flowList 审核历史记录
     * @return 审核历史记录
     */
    @Override
    public List<FlowList> selectFlowListList(FlowList flowList)
    {
        return flowListMapper.selectFlowListList(flowList);
    }

    /**
     * 新增或者修改审核历史记录
     *
     * @param flowList 审核历史记录
     * @return 结果
     */
    public AjaxResult saveFlowList(FlowList flowList)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowList.getId()))
        {
            // 修改
            flowList.setUpdateBy(userId); // 更新人
            flowList.setUpdateTime(curDate); // 更新时间
            flowListMapper.updateFlowList(flowList);
        }
        else
        {
            // 新增
            flowList.setId(StringUtils.getUUID()); // 主键
            flowList.setDelFlag("0");
            flowList.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowList.setCreateBy(userId); // 创建人
            flowList.setCreateTime(curDate); // 创建时间
            flowList.setUpdateBy(userId); // 更新人
            flowList.setUpdateTime(curDate); // 更新时间
            flowListMapper.insertFlowList(flowList);
        }
        return AjaxResult.success("操作成功！",flowList.getId());
    }


    /**
     * 批量删除审核历史记录
     * 
     * @param ids 需要删除的审核历史记录ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowListByIds(String[] ids)
    {
        int count = flowListMapper.deleteFlowListByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除审核历史记录信息
     * 
     * @param id 审核历史记录ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowListById(String id)
    {
        int count = flowListMapper.deleteFlowListById(id);
        return AjaxResult.success(count);
    }

    /**
     * 查询审核历史记录列表
     *
     * @param flowList 审核历史记录
     * @return 审核历史记录
     */
    @Override
    public List<FlowList> selectFlowListListNew(FlowList flowList)
    {
        return flowListMapper.selectFlowListListNew(flowList);

    }
}
