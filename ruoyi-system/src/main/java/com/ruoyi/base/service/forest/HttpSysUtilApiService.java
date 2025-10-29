package com.ruoyi.base.service.forest;


import com.dtflys.forest.annotation.*;
import com.ruoyi.base.domain.CarParaVO;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.common.core.page.TableDataInfo;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base/sysutil")
public interface HttpSysUtilApiService {

 /*   *//**
     * 同步车俩实时轨迹
     *//*
    @Post("/syncTrack")
    Map<String, List<TrailBo>> syncTrack(@JSONBody CarParaVO carParaVO);


    *//**
     * 同步可疑车俩
     * @return
     *//*
    @Post("/syncSuspiciousCar")
    Map<String, List<TrailBo>>  syncSuspiciousCar(@JSONBody CarParaVO carParaVO);*/


    /**
     * 车俩历史轨迹 ：根据车牌号查询
     * @param carParaVO
     * @return
     */
    @Get("/carTrackQueryByCarNo")
    TableDataInfo carTrackQueryByCarNo(@Query CarParaVO carParaVO);


    /**
     * 俩历史轨迹 ：根据时间查询
     * @param carParaVO
     * @return
     */
    @Get("/carTrackQueryByTime")
    TableDataInfo carTrackQueryByTime(@Query CarParaVO carParaVO);


  /*  *//**
     * 数据转换------------------
     *
     * @param
     * @return
     *//*
    @Post("/changeTrailInfo")
    TrailInfo changeTrailInfo(@JSONBody TrailInfo trailInfo);*/

    @Get("/getByTrailBo")
    TrailBo getByTrailBo(@Query TrailBo trailBo);


}
