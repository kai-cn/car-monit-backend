package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseServiceAreaInfoMapper;
import com.ruoyi.base.domain.BaseServiceAreaInfo;
import com.ruoyi.base.service.IBaseServiceAreaInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 服务区基础信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseServiceAreaInfoServiceImpl extends ServiceImpl<BaseServiceAreaInfoMapper, BaseServiceAreaInfo> implements IBaseServiceAreaInfoService {

    @Autowired
    private BaseServiceAreaInfoMapper baseServiceAreaInfoMapper;

    /**
     * 查询服务区基础信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 服务区基础信息
     */
    @Override
    public BaseServiceAreaInfo selectBaseServiceAreaInfoById(String agentPk) {
        return baseServiceAreaInfoMapper.selectBaseServiceAreaInfoById(agentPk);
    }

    /**
     * 查询服务区基础信息列表
     *
     * @param baseServiceAreaInfo 服务区基础信息
     * @return 服务区基础信息
     */
    @Override
    public List<BaseServiceAreaInfo> selectBaseServiceAreaInfoList(BaseServiceAreaInfo baseServiceAreaInfo) {
        return baseServiceAreaInfoMapper.selectBaseServiceAreaInfoList(baseServiceAreaInfo);
    }


    /**
     * 新增或者修改服务区基础信息
     *
     * @param baseServiceAreaInfo 服务区基础信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseServiceAreaInfo(BaseServiceAreaInfo baseServiceAreaInfo)
    {
        if (CommonUtil.isNotBlank(baseServiceAreaInfo.getId()))
        {
            // 修改
            baseServiceAreaInfoMapper.updateById(baseServiceAreaInfo);
        }
        else
        {
            // 新增 主键
            baseServiceAreaInfoMapper.insert(baseServiceAreaInfo);
        }
        return AjaxResult.success("操作成功！",baseServiceAreaInfo.getId());
    }

    /**
     * 批量删除服务区基础信息
     *
     * @param agentPks 需要删除的服务区基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseServiceAreaInfoByIds(String[] agentPks)
    {
        int count = baseServiceAreaInfoMapper.deleteBaseServiceAreaInfoByIds(agentPks);
        return AjaxResult.success(count);
    }

    /**
     * 删除服务区基础信息信息
     *
     * @param agentPk 服务区基础信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseServiceAreaInfoById(String agentPk)
    {
        int count = baseServiceAreaInfoMapper.deleteBaseServiceAreaInfoById(agentPk);
        return AjaxResult.success(count);
    }



}
