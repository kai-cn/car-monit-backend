package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.FlowMessageDispose;
import com.ruoyi.flow.domain.FlowMessageInfo;
import com.ruoyi.flow.mapper.FlowMessageDisposeMapper;
import com.ruoyi.flow.mapper.FlowMessageInfoMapper;
import com.ruoyi.flow.service.IFlowMessageDisposeService;
import com.ruoyi.flow.service.IFlowMessageInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 系统内部消息Service业务层处理
 *
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowMessageInfoServiceImpl implements IFlowMessageInfoService
{
    @Autowired
    private FlowMessageInfoMapper flowMessageInfoMapper;

    @Autowired
    private FlowMessageDisposeMapper flowMessageDisposeMapper;

    @Autowired
    private IFlowMessageDisposeService flowMessageDisposeService;

    /**
     * 查询系统内部消息
     *
     * @param id 系统内部消息ID
     * @return 系统内部消息
     */
    @Override
    public FlowMessageInfo selectFlowMessageInfoById(String id)
    {
        return flowMessageInfoMapper.selectFlowMessageInfoById(id);
    }

    /**
     * 查询系统内部消息列表
     *
     * @param flowMessageInfo 系统内部消息
     * @return 系统内部消息
     */
    @Override
    public List<FlowMessageInfo> selectFlowMessageInfoList(FlowMessageInfo flowMessageInfo)
    {
        return flowMessageInfoMapper.selectFlowMessageInfoList(flowMessageInfo);
    }

    /**
     * 新增或者修改系统内部消息
     *
     * @param flowMessageInfo 系统内部消息
     * @return 结果
     */
    @Override
    public String saveFlowMessageInfo(FlowMessageInfo flowMessageInfo)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();

        // 根据billOid查询是否有消息，要加上BussType否则会得到别的类型的数据
        FlowMessageInfo querybo = new FlowMessageInfo();
        querybo.setBillOid(flowMessageInfo.getBillOid());
        // 消息类型(1:通知业务，2:办理业务)
        querybo.setMsgType(flowMessageInfo.getMsgType());
        querybo.setBussType(flowMessageInfo.getBussType());
        List<FlowMessageInfo> queryList = this.selectFlowMessageInfoList(querybo);
        if (queryList.size() > 0){
            flowMessageInfo.setId(queryList.get(0).getId());
        }

        if (StringUtils.isNotEmpty(flowMessageInfo.getId()))
        {
            // 修改
            flowMessageInfo.setUpdateBy(userId); // 更新人
            flowMessageInfo.setUpdateTime(curDate); // 更新时间
            flowMessageInfoMapper.updateFlowMessageInfo(flowMessageInfo);
        }
        else
        {
            // 新增
            flowMessageInfo.setId(StringUtils.getUUID()); // 主键
            flowMessageInfo.setDelFlag("0");
            flowMessageInfo.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowMessageInfo.setCreateBy(userId); // 创建人
            flowMessageInfo.setCreateTime(curDate); // 创建时间
            flowMessageInfo.setUpdateBy(userId); // 更新人
            flowMessageInfo.setUpdateTime(curDate); // 更新时间
            flowMessageInfoMapper.insertFlowMessageInfo(flowMessageInfo);
        }
        // 新增明细
        List<FlowMessageDispose> disposeList = flowMessageInfo.getDisposeList();
        if (null !=disposeList && disposeList.size() > 0){
            for (int i=0;i<disposeList.size();i++){
                FlowMessageDispose disposeBo = disposeList.get(i);
                disposeBo.setMid(flowMessageInfo.getId()); // 外键
                disposeBo.setMsgStatus("2"); // 未处理
                // disposeBo.setBussId(); 处理人usr
                flowMessageDisposeService.saveFlowMessageDispose(disposeBo);
            }
        }
        return flowMessageInfo.getId();
    }


    /**
     * 批量删除系统内部消息
     *
     * @param ids 需要删除的系统内部消息ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowMessageInfoByIds(String[] ids)
    {
        int count = flowMessageInfoMapper.deleteFlowMessageInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除系统内部消息信息
     *
     * @param id 系统内部消息ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowMessageInfoById(String id)
    {
        int count = flowMessageInfoMapper.deleteFlowMessageInfoById(id);
        return AjaxResult.success(count);
    }




    @Override
    public void dealBusinessMessage(String messageDisposeId) {
        FlowMessageDispose flowMessageDispose = flowMessageDisposeService.selectFlowMessageDisposeById(messageDisposeId);
        if (flowMessageDispose != null) {
            String messageId = flowMessageDispose.getMid();
            // 更新所有的消息详情信息
            FlowMessageDispose updateBo = new FlowMessageDispose();
            // 处理人
            updateBo.setBussName(String.valueOf(SecurityUtils.getUserId()));
            // 消息状态 1 => 已办理, 2 => 未办理
            updateBo.setMsgStatus("1");
            // 处理时间
            updateBo.setHangTime(DateUtils.getTimestamp());
            // 消息id
            updateBo.setMid(messageId);

            // 更新处理消息
            flowMessageDisposeMapper.updateBusinessByMessageId(updateBo);
        }
    }

}
