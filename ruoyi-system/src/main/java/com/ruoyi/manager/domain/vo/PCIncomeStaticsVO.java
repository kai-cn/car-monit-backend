package com.ruoyi.manager.domain.vo;

import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/14:29
 * @Description:
 */
@Data
public class PCIncomeStaticsVO {

    private String orgId;
    /**
     * 机构名称
     */
    private String orgName;

    /**
     * 金额
     */
    private BigDecimal amount;

    /**
     * 车辆数量
     */
    private Integer carNum;
}
