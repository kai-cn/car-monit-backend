package com.ruoyi.base.domain;

import lombok.Data;

@Data
public class CarVO {

    /** 车牌id */
    private String carId;

    /** 车牌号 */
    private String carNo;

    /** 行驶轨迹id */
    private String trackId;

    /** 行驶轨迹josn */
    private String trackJosn;

    /** 是否有数据 */
    private String flag;
}
