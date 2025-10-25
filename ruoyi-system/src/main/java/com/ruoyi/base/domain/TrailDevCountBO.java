package com.ruoyi.base.domain;

import lombok.Data;

import java.util.List;

@Data
public class TrailDevCountBO {

    //  设备信息
    private Integer exceptNum;

    // 设备集合
    private List<TrailDevBO> TrailDevList;

}
