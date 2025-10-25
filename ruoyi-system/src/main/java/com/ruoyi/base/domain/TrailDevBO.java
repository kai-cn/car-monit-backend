package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

@Data
public class TrailDevBO {

    //  状态：0 正常 1异常
    private String status;

    //  设备信息
    private String devName;

    /**
     * 轨迹详情
     */
    private List<TrailBo> trailList;

}
