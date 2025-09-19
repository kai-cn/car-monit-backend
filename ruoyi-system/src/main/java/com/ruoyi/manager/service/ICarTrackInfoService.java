package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarTrackInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 车辆行驶轨迹Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarTrackInfoService extends IService<CarTrackInfo> {

    /**
     * 查询车辆行驶轨迹
     *
     * @param id 车辆行驶轨迹ID
     * @return 车辆行驶轨迹
     */
    CarTrackInfo selectCarTrackInfoById(String id);

    /**
     * 查询车辆行驶轨迹列表
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 车辆行驶轨迹集合
     */
    List<CarTrackInfo> selectCarTrackInfoList(CarTrackInfo carTrackInfo);


    /**
     * 新增或者修改车辆行驶轨迹
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 结果
     */
    AjaxResult saveCarTrackInfo(CarTrackInfo carTrackInfo);

    /**
     * 批量删除车辆行驶轨迹
     *
     * @param ids 需要删除的车辆行驶轨迹ID
     * @return 结果
     */
    AjaxResult deleteCarTrackInfoByIds(String[] ids);


    /**
     * 轨迹同步
     *
     * @return 结果
     */
    AjaxResult sync();

    /**
     * 可疑车俩
     *
     * @return 结果
     */
    AjaxResult syncSuspiciousCar();

}
