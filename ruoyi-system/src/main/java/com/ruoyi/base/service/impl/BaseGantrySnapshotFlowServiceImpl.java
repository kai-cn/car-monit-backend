package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseGantrySnapshotFlowMapper;
import com.ruoyi.base.domain.BaseGantrySnapshotFlow;
import com.ruoyi.base.service.IBaseGantrySnapshotFlowService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架抓拍流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseGantrySnapshotFlowServiceImpl extends ServiceImpl<BaseGantrySnapshotFlowMapper, BaseGantrySnapshotFlow> implements IBaseGantrySnapshotFlowService {

    @Autowired
    private BaseGantrySnapshotFlowMapper baseGantrySnapshotFlowMapper;

    /**
     * 查询门架抓拍流水
     *
     * @param bigId 门架抓拍流水ID
     * @return 门架抓拍流水
     */
    @Override
    public BaseGantrySnapshotFlow selectBaseGantrySnapshotFlowById(String bigId) {
        return baseGantrySnapshotFlowMapper.selectBaseGantrySnapshotFlowById(bigId);
    }

    /**
     * 查询门架抓拍流水列表
     *
     * @param baseGantrySnapshotFlow 门架抓拍流水
     * @return 门架抓拍流水
     */
    @Override
    public List<BaseGantrySnapshotFlow> selectBaseGantrySnapshotFlowList(BaseGantrySnapshotFlow baseGantrySnapshotFlow) {
        return baseGantrySnapshotFlowMapper.selectBaseGantrySnapshotFlowList(baseGantrySnapshotFlow);
    }


    /**
     * 新增或者修改门架抓拍流水
     *
     * @param baseGantrySnapshotFlow 门架抓拍流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseGantrySnapshotFlow(BaseGantrySnapshotFlow baseGantrySnapshotFlow)
    {
        if (CommonUtil.isNotBlank(baseGantrySnapshotFlow.getId()))
        {
            // 修改
            baseGantrySnapshotFlowMapper.updateById(baseGantrySnapshotFlow);
        }
        else
        {
            // 新增 主键
            baseGantrySnapshotFlowMapper.insert(baseGantrySnapshotFlow);
        }
        return AjaxResult.success("操作成功！",baseGantrySnapshotFlow.getId());
    }

    /**
     * 批量删除门架抓拍流水
     *
     * @param bigIds 需要删除的门架抓拍流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseGantrySnapshotFlowByIds(String[] bigIds)
    {
        int count = baseGantrySnapshotFlowMapper.deleteBaseGantrySnapshotFlowByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除门架抓拍流水信息
     *
     * @param bigId 门架抓拍流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseGantrySnapshotFlowById(String bigId)
    {
        int count = baseGantrySnapshotFlowMapper.deleteBaseGantrySnapshotFlowById(bigId);
        return AjaxResult.success(count);
    }



}
