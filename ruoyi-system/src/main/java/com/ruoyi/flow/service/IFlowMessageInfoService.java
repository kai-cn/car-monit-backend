package com.ruoyi.flow.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.flow.domain.FlowMessageInfo;

import java.util.List;

/**
 * 系统内部消息Service接口
 *
 * @author ruoyi
 * @date 2021-05-07
 */
public interface IFlowMessageInfoService {
    /**
     * 查询系统内部消息
     *
     * @param id 系统内部消息ID
     * @return 系统内部消息
     */
    FlowMessageInfo selectFlowMessageInfoById(String id);

    /**
     * 查询系统内部消息列表
     *
     * @param flowMessageInfo 系统内部消息
     * @return 系统内部消息集合
     */
    List<FlowMessageInfo> selectFlowMessageInfoList(FlowMessageInfo flowMessageInfo);

    /**
     * 新增或者修改系统内部消息
     *
     * @param flowMessageInfo 系统内部消息
     * @return 结果
     */
    String saveFlowMessageInfo(FlowMessageInfo flowMessageInfo);

    /**
     * 批量删除系统内部消息
     *
     * @param ids 需要删除的系统内部消息ID
     * @return 结果
     */
    AjaxResult deleteFlowMessageInfoByIds(String[] ids);

    /**
     * 删除系统内部消息信息
     *
     * @param id 系统内部消息ID
     * @return 结果
     */
    AjaxResult deleteFlowMessageInfoById(String id);

   /* *//**
     * 发送业务消息
     * @param businessId 业务id
     * @param baseProcess 租户流程-下一个流程
     * @param dealUserId 处理人id, 多个使用逗号拼接
     * @param messageDisposeId 当前流程派发消息的id
     * @param businessTitle 业务标题
     * @return
     *//*
    boolean sendBusinessMessageInfo(String businessId, BaseProcess baseProcess, String dealUserId,
                                    String messageDisposeId, String businessTitle);

    *//**
     * 添加业务消息
     * @param businessId 业务id
     * @param dealUserId 处理人id, 多个使用逗号拼接
     * @param baseProcess 租户流程
     * @param businessTitle 业务标题
     *//*
    void addBusinessMessageInfo(String businessId, String dealUserId, BaseProcess baseProcess, String businessTitle);*/

    /**
     * 处理业务消息
     * @param messageDisposeId
     */
    void dealBusinessMessage(String messageDisposeId);

}
