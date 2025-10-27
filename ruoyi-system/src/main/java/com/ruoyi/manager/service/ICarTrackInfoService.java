package com.ruoyi.manager.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailDevCountBO;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarTrackInfo;

import java.util.List;

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
     * 轨迹同步：当前轨迹
     *
     * @return 结果
     */
    AjaxResult syncCurrentTrack();


    /**
     * 轨迹同步：历史轨迹全部
     *
     * @return 结果
     */
    AjaxResult syncHistoryTrack();


    /**
     * 轨迹同步：没有记录的车辆
     *
     * @return 结果
     */
     AjaxResult syncHistoryTrackNoCar();

    /**
     * 根据桩号转换轨迹经纬度
     * @param josnList
     * @return
     */
    List<Geometry> getCarGeometry(ZdataTrailTracks tracksBo,List<TrailBo> josnList);

    /**
     * 根据桩号转换轨迹经纬度：先通过腾讯API转换
     * @param josnList
     * @return
     */
    List<Geometry> getCarGeometryByPlan(ZdataTrailTracks tracksBo,List<TrailBo> josnList);


    /**
     * 根据桩号转换轨迹经纬度
     * @param josnList
     * @return
     */
    TrailDevCountBO getTrailDevBO(List<TrailBo> josnList);

}
