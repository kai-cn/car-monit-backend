package com.ruoyi.flow.service.impl;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.flow.domain.FlowApplyInfo;
import com.ruoyi.flow.mapper.FlowApplyInfoMapper;
import com.ruoyi.flow.service.IFlowApplyInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 我的申请Service业务层处理
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Service
public class FlowApplyInfoServiceImpl implements IFlowApplyInfoService
{
    @Autowired
    private FlowApplyInfoMapper flowApplyInfoMapper;

    /**
     * 查询我的申请
     * 
     * @param id 我的申请ID
     * @return 我的申请
     */
    @Override
    public FlowApplyInfo selectFlowApplyInfoById(String id)
    {
        return flowApplyInfoMapper.selectFlowApplyInfoById(id);
    }

    /**
     * 查询我的申请列表
     * 
     * @param flowApplyInfo 我的申请
     * @return 我的申请
     */
    @Override
    public List<FlowApplyInfo> selectFlowApplyInfoList(FlowApplyInfo flowApplyInfo)
    {
        return flowApplyInfoMapper.selectFlowApplyInfoList(flowApplyInfo);
    }

    /**
     * 新增或者修改我的申请
     *
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    @Override
    public AjaxResult saveFlowApplyInfo(FlowApplyInfo flowApplyInfo)
    {
        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();
        if (StringUtils.isNotEmpty(flowApplyInfo.getId()))
        {
            // 修改
            flowApplyInfo.setUpdateBy(userId); // 更新人
            flowApplyInfo.setUpdateTime(curDate); // 更新时间
            flowApplyInfoMapper.updateFlowApplyInfo(flowApplyInfo);
        }
        else
        {
            // 新增
            flowApplyInfo.setId(StringUtils.getUUID()); // 主键
            flowApplyInfo.setDelFlag("0");
            flowApplyInfo.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowApplyInfo.setCreateBy(userId); // 创建人
            flowApplyInfo.setCreateTime(curDate); // 创建时间
            flowApplyInfo.setUpdateBy(userId); // 更新人
            flowApplyInfo.setUpdateTime(curDate); // 更新时间
            flowApplyInfoMapper.insertFlowApplyInfo(flowApplyInfo);
        }
        return AjaxResult.success("操作成功！",flowApplyInfo.getId());
    }


    /**
     * 批量删除我的申请
     * 
     * @param ids 需要删除的我的申请ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowApplyInfoByIds(String[] ids)
    {
        int count = flowApplyInfoMapper.deleteFlowApplyInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除我的申请信息
     * 
     * @param id 我的申请ID
     * @return 结果
     */
    @Override
    public AjaxResult deleteFlowApplyInfoById(String id)
    {
        int count = flowApplyInfoMapper.deleteFlowApplyInfoById(id);
        return AjaxResult.success(count);
    }

    /**
     * 新增或者修改我的申请
     *
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    @Override
    public String saveFlowApplyInfoNew(FlowApplyInfo flowApplyInfo){

        Long userId = SecurityUtils.getUserId();
        java.sql.Timestamp curDate = DateUtils.getTimestamp();

        // 根据业务查询是否有记录
        FlowApplyInfo querybo = new FlowApplyInfo();
        querybo.setBillOid(flowApplyInfo.getBillOid());
        List<FlowApplyInfo> queryList = this.selectFlowApplyInfoList(querybo);
        if (queryList.size() > 0){
            flowApplyInfo.setId(queryList.get(0).getId());
        }

        if (StringUtils.isNotEmpty(flowApplyInfo.getId()))
        {
            // 修改
            flowApplyInfo.setUpdateBy(userId); // 更新人
            flowApplyInfo.setUpdateTime(curDate); // 更新时间
            flowApplyInfoMapper.updateFlowApplyInfo(flowApplyInfo);
        }
        else
        {
            // 新增
            flowApplyInfo.setId(StringUtils.getUUID()); // 主键
            flowApplyInfo.setDelFlag("0");
            flowApplyInfo.setEpsId(SecurityUtils.getEpsId()); // 当前人所在的部门
            flowApplyInfo.setCreateBy(userId); // 创建人
            flowApplyInfo.setCreateTime(curDate); // 创建时间
            flowApplyInfo.setUpdateBy(userId); // 更新人
            flowApplyInfo.setUpdateTime(curDate); // 更新时间
            flowApplyInfoMapper.insertFlowApplyInfo(flowApplyInfo);
        }
        return flowApplyInfo.getId();
    }

    /**
     * 根据业务id查询对应的信息
     * @param billId
     * @return
     */
    @Override
    public FlowApplyInfo selectByBillId(String billId) {
        return flowApplyInfoMapper.selectByBillId(billId);
    }

}
