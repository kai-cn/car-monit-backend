package com.ruoyi.base.service.forest;

import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.ruoyi.base.domain.*;

import java.util.List;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
public interface HttpBaseInfoApiService {

    /**
     * 获取机构信息
     * @return
     */
    @Get("/base/org/listAll")
    List<OdsYhglVBaseOrg> getOrgInfoList();

    /**
     * 获取路段信息
     * @return
     */
    @Get("/base/section/listAll")
    List<OdsSzdnSection> getSectionInfoList();


    /**
     * 获取门架信息
     * @return
     */
    @Get("/base/gantry/listAll")
    List<OdsSzdnGantry> getGantryInfoList();


    /**
     * 获取服务区基础信息
     * @return
     */
    @Get("/base/fwqjcxx/listAll")
    List<DwdLcztFwqjcxx> getServiceAreaInfoList();

    /**
     * 获取收费所信息
     * @return
     */
    @Get("/base/sfsjcxx/listAll")
    List<DwdLcztSfsjcxx> getTollBoothInfoList();

    /**
     * 获取收费站基础信息位置
     * @return
     */
    @Get(url = "/base/sfzjcxx/listAll")
    List<DwdLcztSfzjcxx> getSfzjcxxInfoList();

    /**
     * 获取收费站信息
     * @return
     */
    @Get("/base/toll/listAll")
    List<OdsSzdnToll> getTollStationInfoList();


}
