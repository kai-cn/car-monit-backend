package com.ruoyi.base.service.forest;


import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.JSONBody;
import com.ruoyi.base.domain.CarParaVO;
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
    TableDataInfo carTrackQueryByCarNo(@JSONBody CarParaVO carParaVO);


    /**
     * 车俩历史轨迹 ：根据时间查询
     * @param carParaVO
     * @return
     */
    @Get("/carTrackQueryByTime")
    TableDataInfo  carTrackQueryByTime(@JSONBody CarParaVO carParaVO);




}
