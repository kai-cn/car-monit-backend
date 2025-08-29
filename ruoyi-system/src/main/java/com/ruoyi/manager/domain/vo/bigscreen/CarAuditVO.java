package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:19
 * @Description:
 */
@ApiModel(description = "追缴Vo")
@Data
public class CarAuditVO {
    @ApiModelProperty("追缴总次数")
    private Integer count;
    @ApiModelProperty("追缴已完成次数")
    private Integer finishedCount;
    @ApiModelProperty("追缴费用（元）")
    private BigDecimal amount;
    @ApiModelProperty("追缴已完成费用（元）")
    private BigDecimal finishedAmount;
}
