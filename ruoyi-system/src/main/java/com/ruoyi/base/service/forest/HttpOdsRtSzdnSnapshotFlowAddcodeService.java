package com.ruoyi.base.service.forest;

import cn.hutool.json.JSONObject;
import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.ruoyi.base.domain.model.OdsRtSzdnSnapshotFlowAddcodeModel;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base")
public interface HttpOdsRtSzdnSnapshotFlowAddcodeService {


    @Get("/snapshotflow/list")
    JSONObject getOdsRtSzdnSnapshotFlowAddcodePage(@Query OdsRtSzdnSnapshotFlowAddcodeModel odsRtSzdnSnapshotFlowAddcodeModel);
}
