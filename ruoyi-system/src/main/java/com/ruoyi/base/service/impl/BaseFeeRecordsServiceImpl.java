package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseFeeRecordsMapper;
import com.ruoyi.base.domain.BaseFeeRecords;
import com.ruoyi.base.service.IBaseFeeRecordsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 基础-收费流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseFeeRecordsServiceImpl extends ServiceImpl<BaseFeeRecordsMapper, BaseFeeRecords> implements IBaseFeeRecordsService {

    @Autowired
    private BaseFeeRecordsMapper baseFeeRecordsMapper;

    /**
     * 查询基础-收费流水
     *
     * @param bigId 基础-收费流水ID
     * @return 基础-收费流水
     */
    @Override
    public BaseFeeRecords selectBaseFeeRecordsById(String bigId) {
        return baseFeeRecordsMapper.selectBaseFeeRecordsById(bigId);
    }

    /**
     * 查询基础-收费流水列表
     *
     * @param baseFeeRecords 基础-收费流水
     * @return 基础-收费流水
     */
    @Override
    public List<BaseFeeRecords> selectBaseFeeRecordsList(BaseFeeRecords baseFeeRecords) {
        return baseFeeRecordsMapper.selectBaseFeeRecordsList(baseFeeRecords);
    }


    /**
     * 新增或者修改基础-收费流水
     *
     * @param baseFeeRecords 基础-收费流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseFeeRecords(BaseFeeRecords baseFeeRecords)
    {
        if (CommonUtil.isNotBlank(baseFeeRecords.getId()))
        {
            // 修改
            baseFeeRecordsMapper.updateById(baseFeeRecords);
        }
        else
        {
            // 新增 主键
            baseFeeRecordsMapper.insert(baseFeeRecords);
        }
        return AjaxResult.success("操作成功！",baseFeeRecords.getId());
    }

    /**
     * 批量删除基础-收费流水
     *
     * @param bigIds 需要删除的基础-收费流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseFeeRecordsByIds(String[] bigIds)
    {
        int count = baseFeeRecordsMapper.deleteBaseFeeRecordsByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除基础-收费流水信息
     *
     * @param bigId 基础-收费流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseFeeRecordsById(String bigId)
    {
        int count = baseFeeRecordsMapper.deleteBaseFeeRecordsById(bigId);
        return AjaxResult.success(count);
    }



}
