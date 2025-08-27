package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseOrgInfoMapper;
import com.ruoyi.base.domain.BaseOrgInfo;
import com.ruoyi.base.service.IBaseOrgInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 机构信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseOrgInfoServiceImpl extends ServiceImpl<BaseOrgInfoMapper, BaseOrgInfo> implements IBaseOrgInfoService {

    @Autowired
    private BaseOrgInfoMapper baseOrgInfoMapper;

    /**
     * 查询机构信息
     *
     * @param bigId 机构信息ID
     * @return 机构信息
     */
    @Override
    public BaseOrgInfo selectBaseOrgInfoById(String bigId) {
        return baseOrgInfoMapper.selectBaseOrgInfoById(bigId);
    }

    /**
     * 查询机构信息列表
     *
     * @param baseOrgInfo 机构信息
     * @return 机构信息
     */
    @Override
    public List<BaseOrgInfo> selectBaseOrgInfoList(BaseOrgInfo baseOrgInfo) {
        return baseOrgInfoMapper.selectBaseOrgInfoList(baseOrgInfo);
    }


    /**
     * 新增或者修改机构信息
     *
     * @param baseOrgInfo 机构信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseOrgInfo(BaseOrgInfo baseOrgInfo)
    {
        if (CommonUtil.isNotBlank(baseOrgInfo.getId()))
        {
            // 修改
            baseOrgInfoMapper.updateById(baseOrgInfo);
        }
        else
        {
            // 新增 主键
            baseOrgInfoMapper.insert(baseOrgInfo);
        }
        return AjaxResult.success("操作成功！",baseOrgInfo.getId());
    }

    /**
     * 批量删除机构信息
     *
     * @param bigIds 需要删除的机构信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseOrgInfoByIds(String[] bigIds)
    {
        int count = baseOrgInfoMapper.deleteBaseOrgInfoByIds(bigIds);
        return AjaxResult.success(count);
    }

    /**
     * 删除机构信息信息
     *
     * @param bigId 机构信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseOrgInfoById(String bigId)
    {
        int count = baseOrgInfoMapper.deleteBaseOrgInfoById(bigId);
        return AjaxResult.success(count);
    }



}
