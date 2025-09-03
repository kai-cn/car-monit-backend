package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpBaseInfoApiService {

    /**
     * 获取机构信息
     * @return
     */
    @Get("/org/listAll")
    JSONObject getOrgInfoList();

    /**
     * 获取路段信息
     * @return
     */
    @Get("/section/listAll")
    JSONObject getSectionInfoList();


    /**
     * 获取门架信息
     * @return
     */
    @Get("/gantry/listAll")
    JSONObject getGantryInfoList();


    /**
     * 获取服务区基础信息
     * @return
     */
    @Get("/fwqjcxx/listAll")
    JSONObject getServiceAreaInfoList();

    /**
     * 获取收费所信息
     * @return
     */
    @Get("/sfsjcxx/listAll")
    JSONObject getTollBoothInfoList();

    /**
     * 获取收费站基础信息位置
     * @return
     */
    @Get(url = "/sfzjcxx/listAll")
    JSONObject getSfzjcxxInfoList();

    /**
     * 获取收费站信息
     * @return
     */
    @Get("/toll/listAll")
    JSONObject getTollStationInfoList();


}
