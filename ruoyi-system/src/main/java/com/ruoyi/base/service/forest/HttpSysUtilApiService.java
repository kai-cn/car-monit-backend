package com.ruoyi.base.service.forest;


import com.alibaba.fastjson2.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.JSONBody;
import com.dtflys.forest.annotation.Post;
import com.ruoyi.manager.domain.vo.CarParaVO;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base/sysutil")
public interface HttpSysUtilApiService {

    /**
     * 同步轨迹
     * @return
     */
    @Post("/syncTrack")
    JSONObject syncTrack(@JSONBody CarParaVO carParaVO);


    /**
     * 同步可疑车俩
     * @return
     */
    @Post("/syncSuspiciousCar")
    JSONObject syncSuspiciousCar(@JSONBody CarParaVO carParaVO);




}
