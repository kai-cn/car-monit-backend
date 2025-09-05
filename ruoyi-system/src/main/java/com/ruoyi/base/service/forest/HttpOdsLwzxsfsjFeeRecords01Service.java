package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsLwzxsfsjFeeRecords01Service {

    @Get("/feerecords/list")
    JSONObject getOdsLwzxsfsjFeeRecords01Page(@Query OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01);

    @Get("/feerecords/{bigId}")
    JSONObject selectOdsLwzxsfsjFeeRecords01ById(@Var("bigId") String bigId);
}
