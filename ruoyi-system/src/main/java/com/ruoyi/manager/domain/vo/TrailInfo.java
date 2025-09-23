package com.ruoyi.manager.domain.vo;

import lombok.Data;

import java.util.List;

@Data
public class TrailInfo {

    //  轨迹ID
    private String trailUuid;

    /**
     * 轨迹详情
     */
    private List<TrailBo> trailList;

}
