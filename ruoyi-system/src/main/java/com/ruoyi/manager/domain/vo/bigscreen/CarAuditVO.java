package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:19
 * @Description:
 */
@Data
public class CarAuditVO {
    /**
     * 追缴总次数
     */
    private Integer totalCount = 0;

    /**
     * 追缴已完成次数
     */
    private Integer finishedCount = 0;

    /**
     * 追缴费用（元）
     */
    private BigDecimal totalAmount = BigDecimal.ZERO;

    /**
     * 追缴已完成费用（元）
     */
    private BigDecimal finishedAmount = BigDecimal.ZERO;
}
