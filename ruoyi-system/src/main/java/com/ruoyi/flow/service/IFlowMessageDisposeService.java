package com.ruoyi.flow.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowMessageDispose;

import java.util.List;

/**
 * 系统消息处理人Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowMessageDisposeService 
{
    /**
     * 查询系统消息处理人
     * 
     * @param id 系统消息处理人ID
     * @return 系统消息处理人
     */
    public FlowMessageDispose selectFlowMessageDisposeById(String id);

    /**
     * 查询系统消息处理人列表
     * 
     * @param flowMessageDispose 系统消息处理人
     * @return 系统消息处理人集合
     */
    public List<FlowMessageDispose> selectFlowMessageDisposeList(FlowMessageDispose flowMessageDispose);

    /**
     * 新增或者修改系统消息处理人
     * 
     * @param flowMessageDispose 系统消息处理人
     * @return 结果
     */
    public AjaxResult saveFlowMessageDispose(FlowMessageDispose flowMessageDispose);

    /**
     * 批量删除系统消息处理人
     * 
     * @param ids 需要删除的系统消息处理人ID
     * @return 结果
     */
    public AjaxResult deleteFlowMessageDisposeByIds(String[] ids);

    /**
     * 删除系统消息处理人信息
     * 
     * @param id 系统消息处理人ID
     * @return 结果
     */
    public AjaxResult deleteFlowMessageDisposeById(String id);


    /**
     * 根据mid：删除系统消息处理人信息 -- 自己
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult removeFlowMessage(String mid,String bussId);

    /**
     * 根据mid：系统消息处理人信息设置只读 --自己
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult saveSzzdFlowMessage(String mid,String bussId);



    /**
     * 根据mid：把全部处理人修改成自己 并且设置为已读  -全部
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult saveSzzdFlowMessageAll(String mid,String bussId);


    /**
     * 新增或者修改系统消息处理人
     *
     * @param  mid：外键 和
     * @return 结果
     */
    public void saveFlowList(String mid,String[] userIds);

}
