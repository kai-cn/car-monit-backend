package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/14:29
 * @Description:
 */
@ApiModel(description = "车辆统计Vo")
@Data
public class CarStatisticsVO {
    /**
     * 逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
     */

    @ApiModelProperty("逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）")
    private String escapedType;

    /**
     * 逃费类型名称
     */
    @ApiModelProperty("逃费类型名称")
    private String escapedTypeName;

    @ApiModelProperty("车辆数量")
    private Integer number;

    @ApiModelProperty("逃费金额")
    private BigDecimal escapedAmount;
}
