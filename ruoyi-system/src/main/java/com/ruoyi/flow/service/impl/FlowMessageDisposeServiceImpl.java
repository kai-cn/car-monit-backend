package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.FlowMessageDispose;
import com.ruoyi.flow.mapper.FlowMessageDisposeMapper;
import com.ruoyi.flow.service.IFlowMessageDisposeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 系统消息处理人Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowMessageDisposeServiceImpl implements IFlowMessageDisposeService 
{
    @Autowired
    private FlowMessageDisposeMapper flowMessageDisposeMapper;

    /**
     * 查询系统消息处理人
     * 
     * @param id 系统消息处理人ID
     * @return 系统消息处理人
     */
    @Override
    public FlowMessageDispose selectFlowMessageDisposeById(String id)
    {
        return flowMessageDisposeMapper.selectFlowMessageDisposeById(id);
    }

    /**
     * 查询系统消息处理人列表
     * 
     * @param flowMessageDispose 系统消息处理人
     * @return 系统消息处理人
     */
    @Override
    public List<FlowMessageDispose> selectFlowMessageDisposeList(FlowMessageDispose flowMessageDispose)
    {
        return flowMessageDisposeMapper.selectFlowMessageDisposeList(flowMessageDispose);
    }

    /**
     * 新增或者修改系统消息处理人
     *
     * @param flowMessageDispose 系统消息处理人
     * @return 结果
     */
    public AjaxResult saveFlowMessageDispose(FlowMessageDispose flowMessageDispose)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowMessageDispose.getId()))
        {
            // 修改
            flowMessageDispose.setUpdateBy(userId); // 更新人
            flowMessageDispose.setUpdateTime(curDate); // 更新时间
            flowMessageDisposeMapper.updateFlowMessageDispose(flowMessageDispose);
        }
        else
        {
            // 新增
            flowMessageDispose.setId(StringUtils.getUUID()); // 主键
            flowMessageDispose.setDelFlag("0");
            flowMessageDispose.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowMessageDispose.setCreateBy(userId); // 创建人
            flowMessageDispose.setCreateTime(curDate); // 创建时间
            flowMessageDispose.setUpdateBy(userId); // 更新人
            flowMessageDispose.setUpdateTime(curDate); // 更新时间
            flowMessageDisposeMapper.insertFlowMessageDispose(flowMessageDispose);
        }
        return AjaxResult.success("操作成功！",flowMessageDispose.getId());
    }


    /**
     * 批量删除系统消息处理人
     * 
     * @param ids 需要删除的系统消息处理人ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowMessageDisposeByIds(String[] ids)
    {
        int count = flowMessageDisposeMapper.deleteFlowMessageDisposeByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除系统消息处理人信息
     * 
     * @param id 系统消息处理人ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowMessageDisposeById(String id)
    {
        int count = flowMessageDisposeMapper.deleteFlowMessageDisposeById(id);
        return AjaxResult.success(count);
    }


    /**
     * 根据mid：删除系统消息处理人信息 -- 自己
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult removeFlowMessage(String mid,String bussId){
        FlowMessageDispose flowMessageDispose = new FlowMessageDispose();
        if (StringUtils.isEmpty(mid)){
            mid = "-1";
        }
        flowMessageDispose.setMid(mid);
        if (StringUtils.isNotEmpty(bussId)){
            flowMessageDispose.setBussId(bussId);
        }
        int count = flowMessageDisposeMapper.removeFlowMessage(flowMessageDispose);
        return AjaxResult.success(count);
    }

    /**
     * 根据mid：系统消息处理人信息 设置只读 -- 自己
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult saveSzzdFlowMessage(String mid,String bussId){
        FlowMessageDispose flowMessageDispose = new FlowMessageDispose();
        if (StringUtils.isEmpty(mid)){
            mid = "-1";
        }
        flowMessageDispose.setMid(mid);
        if (StringUtils.isNotEmpty(bussId)){
            flowMessageDispose.setBussId(bussId);
        }
        int count = flowMessageDisposeMapper.saveSzzdFlowMessage(flowMessageDispose);
        return AjaxResult.success(count);
    }

    /**
     * 根据mid：把全部处理人修改成自己 并且设置为已读  --全部
     *
     * @param mid:消息主键
     * @return 结果
     */
    public AjaxResult saveSzzdFlowMessageAll(String mid,String bussId){
        FlowMessageDispose flowMessageDispose = new FlowMessageDispose();
        if (StringUtils.isEmpty(mid)){
            mid = "-1";
        }
        flowMessageDispose.setMid(mid);
        if (StringUtils.isNotEmpty(bussId)){
            flowMessageDispose.setBussId(bussId);
        }
        else
        {
            flowMessageDispose.setBussId("-1");
        }
        int count = flowMessageDisposeMapper.saveSzzdFlowMessageAll(flowMessageDispose);
        return AjaxResult.success(count);
    }

    /**
     * 新增或者修改系统消息处理人
     *
     * @param  mid：外键 和
     * @return 结果
     */
    public void saveFlowList(String mid,String[] userIds){
        for (int i=0;i<userIds.length;i++){
            FlowMessageDispose disposeBo = new FlowMessageDispose();
            disposeBo.setMid(mid); // 外键
            disposeBo.setMsgStatus("2"); // 未处理
            disposeBo.setBussId(userIds[i]); // 处理人usr
            // 先删除
            this.removeFlowMessage(mid,userIds[i]);
            // 在新增
            this.saveFlowMessageDispose(disposeBo);
        }
    }
}
