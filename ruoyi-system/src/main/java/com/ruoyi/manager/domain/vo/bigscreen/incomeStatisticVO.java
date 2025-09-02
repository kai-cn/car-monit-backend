package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/15:39
 * @Description:
 */
@Data
public class incomeStatisticVO {
    private String orgName;
    private BigDecimal amount;
    private Integer carNum;
}
