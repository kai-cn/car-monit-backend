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
public class TollVO {

    @ApiModelProperty("所属收费站编码")
    private String tollCode;

    @ApiModelProperty("所属收费站名称")
    private String tollName;

}
