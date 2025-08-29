package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@ApiModel(description = "路段Vo")
@Data
public class SectionVO {

    @ApiModelProperty("所属路段编码")
    private String sectionCode;

    @ApiModelProperty("所属路段名称")
    private String sectionName;

}
