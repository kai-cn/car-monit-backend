package com.ruoyi.base.service.forest;


import com.dtflys.forest.annotation.BaseRequest;
import com.dtflys.forest.annotation.JSONBody;
import com.dtflys.forest.annotation.Post;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.TrailBo;

import java.util.List;
import java.util.Map;

@BaseRequest(baseURL = "#{vehicleMonitor.baseUrl}/base/sysutil")
public interface HttpSysUtilApiService {

    /**
     * 同步车俩实时轨迹
     */
    @Post("/syncTrack")
    Map<ZdataTrailTracks, List<TrailBo>> syncTrack(@JSONBody CarParaVO carParaVO);


    /**
     * 同步可疑车俩
     * @return
     */
    @Post("/syncSuspiciousCar")
    Map<ZdataTrailTracks, List<TrailBo>>  syncSuspiciousCar(@JSONBody CarParaVO carParaVO);


    /**
     * 车俩历史轨迹 ：根据车牌号查询
     * @param carParaVO
     * @return
     */
    @Post("/carTrackQueryByCarNo")
    Map<ZdataTrailTracks, List<TrailBo>>  carTrackQueryByCarNo(@JSONBody CarParaVO carParaVO);


    /**
     * 车俩历史轨迹 ：根据时间查询
     * @param carParaVO
     * @return
     */
    @Post("/carTrackQueryByTime")
    Map<ZdataTrailTracks, List<TrailBo>>  carTrackQueryByTime(@JSONBody CarParaVO carParaVO);




}
