package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.common.core.page.TableDataInfo;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
public interface HttpOdsLwzxsfsjFeeRecords01Service {

    @Get("/base/feerecords/list")
    TableDataInfo getOdsLwzxsfsjFeeRecords01Page(@Query OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01);

    @Get("/base/feerecords/{bigId}")
    OdsLwzxsfsjFeeRecords01 selectOdsLwzxsfsjFeeRecords01ById(@Var("bigId") String bigId);
}
