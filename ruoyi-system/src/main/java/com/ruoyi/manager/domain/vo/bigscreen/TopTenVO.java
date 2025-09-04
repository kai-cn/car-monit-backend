package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/10:35
 * @Description:
 */
@Data
public class TopTenVO {
    @ApiModelProperty("路段名称")
    private String sectionName;
    @ApiModelProperty("车辆数量")
    private Integer carNum;
    @ApiModelProperty("排名")
    private Integer rank;
    @ApiModelProperty("百分比")
    private String rate;
}
