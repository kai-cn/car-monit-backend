package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.CarWarningConfigMapper;
import com.ruoyi.base.domain.CarWarningConfig;
import com.ruoyi.base.service.ICarWarningConfigService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 服务区判定规则Service业务层处理
 *
 * @author ruoyi
 * @date 2026-01-27
 */
@Service
public class CarWarningConfigServiceImpl extends ServiceImpl<CarWarningConfigMapper, CarWarningConfig> implements ICarWarningConfigService {

    @Autowired
    private CarWarningConfigMapper carWarningConfigMapper;

    /**
     * 查询服务区判定规则
     *
     * @param id 服务区判定规则ID
     * @return 服务区判定规则
     */
    @Override
    public CarWarningConfig selectCarWarningConfigById(String id) {
        return carWarningConfigMapper.selectCarWarningConfigById(id);
    }

    /**
     * 查询服务区判定规则列表
     *
     * @param carWarningConfig 服务区判定规则
     * @return 服务区判定规则
     */
    @Override
    public List<CarWarningConfig> selectCarWarningConfigList(CarWarningConfig carWarningConfig) {
        return carWarningConfigMapper.selectCarWarningConfigList(carWarningConfig);
    }


    /**
     * 新增或者修改服务区判定规则
     *
     * @param carWarningConfig 服务区判定规则
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarWarningConfig(CarWarningConfig carWarningConfig)
    {
        if (CommonUtil.isNotBlank(carWarningConfig.getId()))
        {
            // 修改
            carWarningConfigMapper.updateById(carWarningConfig);
        }
        else
        {
            // 新增 主键
            carWarningConfigMapper.insert(carWarningConfig);
        }
        return AjaxResult.success("操作成功！",carWarningConfig.getId());
    }

    /**
     * 批量删除服务区判定规则
     *
     * @param ids 需要删除的服务区判定规则ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarWarningConfigByIds(String[] ids)
    {
        int count = carWarningConfigMapper.deleteCarWarningConfigByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除服务区判定规则信息
     *
     * @param id 服务区判定规则ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarWarningConfigById(String id)
    {
        int count = carWarningConfigMapper.deleteCarWarningConfigById(id);
        return AjaxResult.success(count);
    }



}
