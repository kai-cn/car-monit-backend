package com.ruoyi.manager.domain.vo.bigscreen;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/09/02/17:15
 * @Description:
 */
@Data
public class OrgVO {
    @ApiModelProperty("管理中心编码")
    private String orgCode;

    @ApiModelProperty("管理中心名称")
    private String orgName;
}
