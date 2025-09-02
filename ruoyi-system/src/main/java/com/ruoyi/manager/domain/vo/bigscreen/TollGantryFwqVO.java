package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@ApiModel(description = "收费站Vo")
@Data
public class TollGantryFwqVO {

    @ApiModelProperty("1收费站、2门架、3服务区")
    private String type;

    @ApiModelProperty("编码")
    private String code;

    @ApiModelProperty("名称")
    private String name;

}
