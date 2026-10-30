package com.ruoyi.base.service.forest;

import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.Get;
import com.dtflys.forest.annotation.Query;
import com.dtflys.forest.annotation.Var;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.common.core.page.TableDataInfo;

import java.util.Date;
import java.util.List;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}")
public interface HttpOdsRtSzdnSnapshotFlowAddcodeService {


    @Get("/base/snapshotflow/list")
    TableDataInfo getOdsRtSzdnSnapshotFlowAddcodePage(@Query OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);

    @Get("/base/snapshotflow/listToExport")
    List<OdsRtSzdnSnapshotFlowAddcode> getOdsRtSzdnSnapshotFlowAddcodeListToExport(@Query OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode);


    @Get("/base/snapshotflow/{bigId}")
    OdsRtSzdnSnapshotFlowAddcode selectOdsRtSzdnSnapshotFlowAddcodeById(@Var("bigId") String bigId);

    /**
     * 查询GaussDB中最早的snapshottime
     * 
     * @return 最早的抓拍时间
     */
    @Get("/base/snapshotflow/earliest-time")
    Date getEarliestSnapshottime();
}
