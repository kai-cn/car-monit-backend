package com.ruoyi.base.service.forest;

import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeGantryFusion01;
import com.ruoyi.common.core.page.TableDataInfo;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
public interface HttpOdsLwzxsfsjFeeGantryFusion01Service {

    @Get("/base/feeGantry/list")
    TableDataInfo getOdsLwzxsfsjFeeGantryFusion01Page(@Query OdsLwzxsfsjFeeGantryFusion01 odsLwzxsfsjFeeGantryFusion01);

    @Get("/base/feeGantry/{bigId}")
    OdsLwzxsfsjFeeGantryFusion01 selectOdsLwzxsfsjFeeGantryFusion01ById(@Var("bigId") String bigId);

}
