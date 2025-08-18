package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 车辆信息Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarInfoService extends IService<CarInfo> {
    /**
     * 查询车辆信息
     *
     * @param id 车辆信息ID
     * @return 车辆信息
     */
    CarInfo selectCarInfoById(String id);

    /**
     * 查询车辆信息列表
     *
     * @param carInfo 车辆信息
     * @return 车辆信息集合
     */
    List<CarInfo> selectCarInfoList(CarInfo carInfo);


    /**
     * 新增或者修改车辆信息
     *
     * @param carInfo 车辆信息
     * @return 结果
     */
    AjaxResult saveCarInfo(CarInfo carInfo);

    /**
     * 批量删除车辆信息
     *
     * @param ids 需要删除的车辆信息ID
     * @return 结果
     */
    AjaxResult deleteCarInfoByIds(String[] ids);

}
