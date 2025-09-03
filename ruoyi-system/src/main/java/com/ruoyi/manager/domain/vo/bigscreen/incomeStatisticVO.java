package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/15:39
 * @Description:
 */
@Data
public class incomeStatisticVO {
    @ApiModelProperty("机构名称")
    private String orgName;
    @ApiModelProperty("金额")
    private BigDecimal amount;
    @ApiModelProperty("车辆数量")
    private Integer carNum;
}
