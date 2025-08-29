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
@ApiModel(description = "车辆信息Vo")
@Data
public class CarInfoVO {
    /** 车牌号 */
    @ApiModelProperty("车牌号")
    private String carNo;
    /** 车型 */
    @ApiModelProperty("车型")
    private String carType;
    /** 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂） */
    @ApiModelProperty("逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂")
    private String escapedType;
    /** 逃费金额（元） */
    @ApiModelProperty("逃费金额（元）")
    private BigDecimal escapedAmount;
}
