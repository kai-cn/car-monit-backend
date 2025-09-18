package com.ruoyi.base.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure;

import java.util.List;

/**
 * 省界称重Service接口
 *
 * @author ruoyi
 * @date 2025-09-18
 */
public interface IOdsSzdnProvinceBorderVehicleWeightNewstructureService extends IService<OdsSzdnProvinceBorderVehicleWeightNewstructure> {
    /**
     * 查询省界称重
     *
     * @param dataSource 省界称重ID
     * @return 省界称重
     */
    OdsSzdnProvinceBorderVehicleWeightNewstructure selectOdsSzdnProvinceBorderVehicleWeightNewstructureById(String dataSource);

    /**
     * 查询省界称重列表
     *
     * @param odsSzdnProvinceBorderVehicleWeightNewstructure 省界称重
     * @return 省界称重集合
     */
    List<OdsSzdnProvinceBorderVehicleWeightNewstructure> selectOdsSzdnProvinceBorderVehicleWeightNewstructureList(OdsSzdnProvinceBorderVehicleWeightNewstructure odsSzdnProvinceBorderVehicleWeightNewstructure);



}
