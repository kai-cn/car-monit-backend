package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;

import javax.xml.ws.FaultAction;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsRtSzdnSnapshotFlowAddcodeService {


    @Get("/snapshotflow/list")
    JSONObject getOdsRtSzdnSnapshotFlowAddcodePage(@Query OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    @Get("/snapshotflow/{bigId}")
    JSONObject selectOdsRtSzdnSnapshotFlowAddcodeById(@Var("bigId") String bigId);
}
