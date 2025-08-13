package com.ruoyi.flow.mapper;

import com.ruoyi.flow.domain.FlowApplyInfo;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 我的申请Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowApplyInfoMapper 
{
    /**
     * 查询我的申请
     * 
     * @param id 我的申请ID
     * @return 我的申请
     */
    public FlowApplyInfo selectFlowApplyInfoById(String id);

    /**
     * 查询我的申请列表
     * 
     * @param flowApplyInfo 我的申请
     * @return 我的申请集合
     */
    public List<FlowApplyInfo> selectFlowApplyInfoList(FlowApplyInfo flowApplyInfo);

    /**
     * 新增我的申请
     * 
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    public int insertFlowApplyInfo(FlowApplyInfo flowApplyInfo);

    /**
     * 修改我的申请
     * 
     * @param flowApplyInfo 我的申请
     * @return 结果
     */
    public int updateFlowApplyInfo(FlowApplyInfo flowApplyInfo);

    /**
     * 删除我的申请
     * 
     * @param id 我的申请ID
     * @return 结果
     */
    public int deleteFlowApplyInfoById(String id);

    /**
     * 批量删除我的申请
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowApplyInfoByIds(String[] ids);

    /**
     * 根据业务id查询对应的信息
     * @param billId
     * @return
     */
    FlowApplyInfo selectByBillId(String billId);

}
