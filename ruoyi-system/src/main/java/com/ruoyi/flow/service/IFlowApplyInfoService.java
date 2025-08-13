package com.ruoyi.flow.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowApplyInfo;

import java.util.List;

/**
 * 我的申请Service接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowApplyInfoService {
    /**
     * 查询我的申请
     * 
     * @param id 我的申请ID
     * @return 我的申请
     */
    FlowApplyInfo selectFlowApplyInfoById(String id);

    /**
     * 查询我的申请列表
     * 
     * @param flowApplyInfo 我的申请
     * @return 我的申请集合
     */
    List<FlowApplyInfo> selectFlowApplyInfoList(FlowApplyInfo flowApplyInfo);

    /**
     * 新增或者修改我的申请
     * 
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    AjaxResult saveFlowApplyInfo(FlowApplyInfo flowApplyInfo);

    /**
     * 批量删除我的申请
     * 
     * @param ids 需要删除的我的申请ID
     * @return 结果
     */
    AjaxResult deleteFlowApplyInfoByIds(String[] ids);

    /**
     * 删除我的申请信息
     * 
     * @param id 我的申请ID
     * @return 结果
     */
    AjaxResult deleteFlowApplyInfoById(String id);

    /**
     * 新增或者修改我的申请
     *
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    String saveFlowApplyInfoNew(FlowApplyInfo flowApplyInfo);

    /**
     * 根据业务id查询对应的信息
     * @param billId
     * @return
     */
    FlowApplyInfo selectByBillId(String billId);

}
