package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.BaseConfigServiceAreaMapper;
import com.ruoyi.base.domain.BaseConfigServiceArea;
import com.ruoyi.base.service.IBaseConfigServiceAreaService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 服务区Service业务层处理
 *
 * @author ruoyi
 * @date 2026-02-02
 */
@Service
public class BaseConfigServiceAreaServiceImpl extends ServiceImpl<BaseConfigServiceAreaMapper, BaseConfigServiceArea> implements IBaseConfigServiceAreaService {

    @Autowired
    private BaseConfigServiceAreaMapper baseConfigServiceAreaMapper;

    /**
     * 查询服务区
     *
     * @param fwqbm 服务区ID
     * @return 服务区
     */
    @Override
    public BaseConfigServiceArea selectBaseConfigServiceAreaById(String fwqbm) {
        return baseConfigServiceAreaMapper.selectBaseConfigServiceAreaById(fwqbm);
    }

    /**
     * 查询服务区列表
     *
     * @param baseConfigServiceArea 服务区
     * @return 服务区
     */
    @Override
    public List<BaseConfigServiceArea> selectBaseConfigServiceAreaList(BaseConfigServiceArea baseConfigServiceArea) {
        return baseConfigServiceAreaMapper.selectBaseConfigServiceAreaList(baseConfigServiceArea);
    }


    /**
     * 新增或者修改服务区
     *
     * @param baseConfigServiceArea 服务区
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveBaseConfigServiceArea(BaseConfigServiceArea baseConfigServiceArea)
    {
        if (CommonUtil.isNotBlank(baseConfigServiceArea.getId()))
        {
            // 修改
            baseConfigServiceAreaMapper.updateById(baseConfigServiceArea);
        }
        else
        {
            // 新增 主键
            baseConfigServiceAreaMapper.insert(baseConfigServiceArea);
        }
        return AjaxResult.success("操作成功！",baseConfigServiceArea.getId());
    }

    /**
     * 批量删除服务区
     *
     * @param fwqbms 需要删除的服务区ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteBaseConfigServiceAreaByIds(String[] fwqbms)
    {
        int count = baseConfigServiceAreaMapper.deleteBaseConfigServiceAreaByIds(fwqbms);
        return AjaxResult.success(count);
    }

    /**
     * 删除服务区信息
     *
     * @param fwqbm 服务区ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteBaseConfigServiceAreaById(String fwqbm)
    {
        int count = baseConfigServiceAreaMapper.deleteBaseConfigServiceAreaById(fwqbm);
        return AjaxResult.success(count);
    }



}
