package com.ruoyi.flow.mapper;

import java.util.List;
import com.ruoyi.flow.domain.FlowMessageInfo;
import org.springframework.stereotype.Repository;

/**
 * 系统内部消息Mapper接口
 * 
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowMessageInfoMapper 
{
    /**
     * 查询系统内部消息
     * 
     * @param id 系统内部消息ID
     * @return 系统内部消息
     */
    public FlowMessageInfo selectFlowMessageInfoById(String id);

    /**
     * 查询系统内部消息列表
     * 
     * @param flowMessageInfo 系统内部消息
     * @return 系统内部消息集合
     */
    public List<FlowMessageInfo> selectFlowMessageInfoList(FlowMessageInfo flowMessageInfo);

    /**
     * 新增系统内部消息
     * 
     * @param flowMessageInfo 系统内部消息
     * @return 结果
     */
    public int insertFlowMessageInfo(FlowMessageInfo flowMessageInfo);

    /**
     * 修改系统内部消息
     * 
     * @param flowMessageInfo 系统内部消息
     * @return 结果
     */
    public int updateFlowMessageInfo(FlowMessageInfo flowMessageInfo);

    /**
     * 删除系统内部消息
     * 
     * @param id 系统内部消息ID
     * @return 结果
     */
    public int deleteFlowMessageInfoById(String id);

    /**
     * 批量删除系统内部消息
     * 
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowMessageInfoByIds(String[] ids);
}
