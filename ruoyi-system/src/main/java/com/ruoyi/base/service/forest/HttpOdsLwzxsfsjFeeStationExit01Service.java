package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsLwzxsfsjFeeStationExit01Service {



    @Get("/feestationexit/list")
    JSONObject getOdsLwzxsfsjFeeStationExit01Page(@Query OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01);

    @Get("/feestationexit/{bigId}")
    JSONObject selectOdsLwzxsfsjFeeStationExit01ById(@Var("bigId") String bigId);
}
