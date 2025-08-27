package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseSectionInfoMapper;
import com.ruoyi.base.domain.BaseSectionInfo;
import com.ruoyi.base.service.IBaseSectionInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 路段信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseSectionInfoServiceImpl extends ServiceImpl<BaseSectionInfoMapper, BaseSectionInfo> implements IBaseSectionInfoService {

    @Autowired
    private BaseSectionInfoMapper baseSectionInfoMapper;

    /**
     * 查询路段信息
     *
     * @param id 路段信息ID
     * @return 路段信息
     */
    @Override
    public BaseSectionInfo selectBaseSectionInfoById(String id) {
        return baseSectionInfoMapper.selectBaseSectionInfoById(id);
    }

    /**
     * 查询路段信息列表
     *
     * @param baseSectionInfo 路段信息
     * @return 路段信息
     */
    @Override
    public List<BaseSectionInfo> selectBaseSectionInfoList(BaseSectionInfo baseSectionInfo) {
        return baseSectionInfoMapper.selectBaseSectionInfoList(baseSectionInfo);
    }


    /**
     * 新增或者修改路段信息
     *
     * @param baseSectionInfo 路段信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseSectionInfo(BaseSectionInfo baseSectionInfo)
    {
        if (CommonUtil.isNotBlank(baseSectionInfo.getId()))
        {
            // 修改
            baseSectionInfoMapper.updateById(baseSectionInfo);
        }
        else
        {
            // 新增 主键
            baseSectionInfoMapper.insert(baseSectionInfo);
        }
        return AjaxResult.success("操作成功！",baseSectionInfo.getId());
    }

    /**
     * 批量删除路段信息
     *
     * @param ids 需要删除的路段信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseSectionInfoByIds(String[] ids)
    {
        int count = baseSectionInfoMapper.deleteBaseSectionInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除路段信息信息
     *
     * @param id 路段信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseSectionInfoById(String id)
    {
        int count = baseSectionInfoMapper.deleteBaseSectionInfoById(id);
        return AjaxResult.success(count);
    }



}
