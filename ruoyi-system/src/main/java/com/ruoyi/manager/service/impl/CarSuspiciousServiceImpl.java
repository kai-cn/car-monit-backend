package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarSuspiciousMapper;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.service.ICarSuspiciousService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;

/**
 * 可疑车辆Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarSuspiciousServiceImpl extends ServiceImpl<CarSuspiciousMapper, CarSuspicious> implements ICarSuspiciousService {

    @Autowired
    private CarSuspiciousMapper carSuspiciousMapper;

    /**
     * 查询可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 可疑车辆
     */
    @Override
    public CarSuspicious selectCarSuspiciousById(String id) {
        return carSuspiciousMapper.selectCarSuspiciousById(id);
    }

    /**
     * 查询可疑车辆列表
     *
     * @param carSuspicious 可疑车辆
     * @return 可疑车辆
     */
    @Override
    public List<CarSuspicious> selectCarSuspiciousList(CarSuspicious carSuspicious) {
        return carSuspiciousMapper.selectCarSuspiciousList(carSuspicious);
    }


    /**
     * 新增或者修改可疑车辆
     *
     * @param carSuspicious 可疑车辆
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarSuspicious(CarSuspicious carSuspicious)
    {
        if (CommonUtil.isNotBlank(carSuspicious.getId()))
        {
            // 修改
            carSuspiciousMapper.updateById(carSuspicious);
        }
        else
        {
            // 新增 主键
            carSuspiciousMapper.insert(carSuspicious);
        }
        return AjaxResult.success("操作成功！",carSuspicious.getId());
    }

    /**
     * 批量删除可疑车辆
     *
     * @param ids 需要删除的可疑车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarSuspiciousByIds(String[] ids)
    {
        int count = carSuspiciousMapper.deleteCarSuspiciousByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除可疑车辆信息
     *
     * @param id 可疑车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSuspiciousById(String id)
    {
        int count = carSuspiciousMapper.deleteCarSuspiciousById(id);
        return AjaxResult.success(count);
    }

    @Override
    public List<CarSuspicious> selectCarSuspiciousListLimit10() {
        return carSuspiciousMapper.selectCarSuspiciousListLimit10();
    }
}
