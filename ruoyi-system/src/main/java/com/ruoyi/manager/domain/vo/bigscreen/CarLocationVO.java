package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@Data
public class CarLocationVO {

    /**
     * 主键id
     */
    private String id;

    /**
     * 车牌号
     */
    private String carNo;

    /**
     * 车型
     */
    private String carType;

    /**
     * 最后通行经度
     */
    private BigDecimal lon;

    /**
     * 最后通行维度
     */
    private BigDecimal lat;

    /**
     * 最后通行经度
     */
    private String lonStr;

    /**
     * 最后通行维度
     */
    private String latStr;

}
