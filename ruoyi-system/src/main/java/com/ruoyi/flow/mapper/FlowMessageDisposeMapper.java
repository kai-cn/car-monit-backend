package com.ruoyi.flow.mapper;

import com.ruoyi.flow.domain.FlowMessageDispose;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 系统消息处理人Mapper接口
 *
 * @author ruoyi
 * @date 2021-05-07
 */
@Repository
public interface FlowMessageDisposeMapper
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
     * 新增系统消息处理人
     *
     * @param flowMessageDispose 系统消息处理人
     * @return 结果
     */
    public int insertFlowMessageDispose(FlowMessageDispose flowMessageDispose);

    /**
     * 修改系统消息处理人
     *
     * @param flowMessageDispose 系统消息处理人
     * @return 结果
     */
    public int updateFlowMessageDispose(FlowMessageDispose flowMessageDispose);

    /**
     * 删除系统消息处理人
     *
     * @param id 系统消息处理人ID
     * @return 结果
     */
    public int deleteFlowMessageDisposeById(String id);

    /**
     * 批量删除系统消息处理人
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    public int deleteFlowMessageDisposeByIds(String[] ids);


    /**
     * 根据mid：删除系统消息处理人信息
     *
     * @param flowMessageDispose:消息主键
     * @return 结果
     */
    public int removeFlowMessage(FlowMessageDispose flowMessageDispose);

    /**
     * 根据mid：系统消息处理人信息
     *
     * @param flowMessageDispose:消息主键
     * @return 结果
     */
    public int saveSzzdFlowMessage(FlowMessageDispose flowMessageDispose);


    /**
     * 根据mid：系统消息处理人信息 (全部变成自己)
     *
     * @param flowMessageDispose:消息主键
     * @return 结果
     */
    public int saveSzzdFlowMessageAll(FlowMessageDispose flowMessageDispose);

    /**
     * 根据消息id更新业务流消息信息
     * @param flowMessageDispose
     */
    void updateBusinessByMessageId(FlowMessageDispose flowMessageDispose);

}
