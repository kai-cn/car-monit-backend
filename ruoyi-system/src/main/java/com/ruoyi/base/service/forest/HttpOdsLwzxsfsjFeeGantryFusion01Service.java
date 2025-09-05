package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsLwzxsfsjFeeGantryFusion01Service {

    @Get("/feeGantry/list")
    JSONObject getOdsLwzxsfsjFeeGantryFusion01Page(@Query OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01);

    @Get("/feeGantry/{bigId}")
    JSONObject selectOdsLwzxsfsjFeeGantryFusion01ById(@Var("bigId") String bigId);

}
