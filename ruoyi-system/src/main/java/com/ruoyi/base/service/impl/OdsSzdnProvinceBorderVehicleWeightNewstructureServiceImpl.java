package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure;
import com.ruoyi.base.mapper.OdsSzdnProvinceBorderVehicleWeightNewstructureMapper;
import com.ruoyi.base.service.IOdsSzdnProvinceBorderVehicleWeightNewstructureService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 省界称重Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@Service
public class OdsSzdnProvinceBorderVehicleWeightNewstructureServiceImpl extends ServiceImpl<OdsSzdnProvinceBorderVehicleWeightNewstructureMapper, OdsSzdnProvinceBorderVehicleWeightNewstructure> implements IOdsSzdnProvinceBorderVehicleWeightNewstructureService {

    @Autowired
    private OdsSzdnProvinceBorderVehicleWeightNewstructureMapper odsSzdnProvinceBorderVehicleWeightNewstructureMapper;

    /**
     * 查询省界称重
     *
     * @param dataSource 省界称重ID
     * @return 省界称重
     */
    @Override
    public OdsSzdnProvinceBorderVehicleWeightNewstructure selectOdsSzdnProvinceBorderVehicleWeightNewstructureById(String dataSource) {
        return odsSzdnProvinceBorderVehicleWeightNewstructureMapper.selectOdsSzdnProvinceBorderVehicleWeightNewstructureById(dataSource);
    }

    /**
     * 查询省界称重列表
     *
     * @param odsSzdnProvinceBorderVehicleWeightNewstructure 省界称重
     * @return 省界称重
     */
    @Override
    public List<OdsSzdnProvinceBorderVehicleWeightNewstructure> selectOdsSzdnProvinceBorderVehicleWeightNewstructureList(OdsSzdnProvinceBorderVehicleWeightNewstructure odsSzdnProvinceBorderVehicleWeightNewstructure) {
        return odsSzdnProvinceBorderVehicleWeightNewstructureMapper.selectOdsSzdnProvinceBorderVehicleWeightNewstructureList(odsSzdnProvinceBorderVehicleWeightNewstructure);
    }





}
