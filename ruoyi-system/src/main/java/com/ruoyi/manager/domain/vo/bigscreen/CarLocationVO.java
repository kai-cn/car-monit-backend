package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@ApiModel(description = "车辆位置Vo")
@Data
public class CarLocationVO {

    @ApiModelProperty("主键id")
    private String id;

    @ApiModelProperty("车牌号")
    private String carNo;

    @ApiModelProperty("车型")
    private String carType;

    @ApiModelProperty("最后通行经度")
    private BigDecimal lon;

    @ApiModelProperty("最后通行维度")
    private BigDecimal lat;

    private String lonStr;

    private String latStr;

}
