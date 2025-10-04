package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

@Data
public class TrailInfo {

    //  轨迹ID
    private String trailUuid;

    // 轨迹对象
    private ZdataTrailTracks tracks;

    /**
     * 轨迹详情
     */
    private List<TrailBo> trailList;


    /**
     * 路线轨迹
     */
    private List<Geometry> raodTrailList;

}
