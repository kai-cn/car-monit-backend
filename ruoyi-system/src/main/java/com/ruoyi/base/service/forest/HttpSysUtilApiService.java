package com.ruoyi.base.service.forest;


import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.JSONBody;
import com.dtflys.forest.annotation.Post;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.TrailBo;

import java.util.List;
import java.util.Map;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base/sysutil")
public interface HttpSysUtilApiService {

    /**
     * 同步轨迹
     * @return
     */
    @Post("/syncTrack")
    Map<String, List<TrailBo>> syncTrack(@JSONBody CarParaVO carParaVO);


    /**
     * 同步可疑车俩
     * @return
     */
    @Post("/syncSuspiciousCar")
    Map<String, List<TrailBo>> syncSuspiciousCar(@JSONBody CarParaVO carParaVO);




}
