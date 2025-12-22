package com.ruoyi.base.domain;

import com.alibaba.fastjson2.annotation.JSONField;
import lombok.Data;

import java.util.Date;
import java.util.List;

@Data
public class TrailInfo {

    //  轨迹ID
    @JSONField(name = "轨迹ID")
    private String trailUuid;

    /**
     * 进入时间（分区键，月度分区粒度）
     */
    @JSONField(name = "进入时间")
    private Date enterTime;

    // 轨迹对象
    @JSONField(name = "轨迹对象")
    private ZdataTrailTracks tracks;

    /**
     * 轨迹详情
     */
    @JSONField(name = "轨迹详情")
    private List<TrailBo> trailList;


    /**
     * 路线轨迹
     */
    @JSONField(name = "路线轨迹")
    private List<Geometry> raodTrailList;

    /**
     * 设备集合
     */
    @JSONField(name = "设备集合")
    private TrailDevCountBO trailDevCountBO;

}
