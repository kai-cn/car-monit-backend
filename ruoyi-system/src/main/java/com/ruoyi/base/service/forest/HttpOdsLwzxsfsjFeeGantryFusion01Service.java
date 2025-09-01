package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.ruoyi.base.domain.model.OdsLwzxsfsjFeeGantryFusion01Model;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsLwzxsfsjFeeGantryFusion01Service {

    @Get("/feeGantry/list")
    JSONObject getOdsLwzxsfsjFeeGantryFusion01Page(@Query OdsLwzxsfsjFeeGantryFusion01Model odsLwzxsfsjFeeGantryFusion01Model);

}
