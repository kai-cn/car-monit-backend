package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseGantryInfoMapper;
import com.ruoyi.base.domain.BaseGantryInfo;
import com.ruoyi.base.service.IBaseGantryInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 门架信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-26
 */
@Service
public class BaseGantryInfoServiceImpl extends ServiceImpl<BaseGantryInfoMapper, BaseGantryInfo> implements IBaseGantryInfoService {

    @Autowired
    private BaseGantryInfoMapper baseGantryInfoMapper;

    /**
     * 查询门架信息
     *
     * @param id 门架信息ID
     * @return 门架信息
     */
    @Override
    public BaseGantryInfo selectBaseGantryInfoById(String id) {
        return baseGantryInfoMapper.selectBaseGantryInfoById(id);
    }

    /**
     * 查询门架信息列表
     *
     * @param baseGantryInfo 门架信息
     * @return 门架信息
     */
    @Override
    public List<BaseGantryInfo> selectBaseGantryInfoList(BaseGantryInfo baseGantryInfo) {
        return baseGantryInfoMapper.selectBaseGantryInfoList(baseGantryInfo);
    }


    /**
     * 新增或者修改门架信息
     *
     * @param baseGantryInfo 门架信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseGantryInfo(BaseGantryInfo baseGantryInfo)
    {
        if (CommonUtil.isNotBlank(baseGantryInfo.getId()))
        {
            // 修改
            baseGantryInfoMapper.updateById(baseGantryInfo);
        }
        else
        {
            // 新增 主键
            baseGantryInfoMapper.insert(baseGantryInfo);
        }
        return AjaxResult.success("操作成功！",baseGantryInfo.getId());
    }

    /**
     * 批量删除门架信息
     *
     * @param ids 需要删除的门架信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseGantryInfoByIds(String[] ids)
    {
        int count = baseGantryInfoMapper.deleteBaseGantryInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除门架信息信息
     *
     * @param id 门架信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseGantryInfoById(String id)
    {
        int count = baseGantryInfoMapper.deleteBaseGantryInfoById(id);
        return AjaxResult.success(count);
    }



}
