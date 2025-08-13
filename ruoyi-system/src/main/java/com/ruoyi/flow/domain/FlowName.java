package com.ruoyi.flow.domain;

import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseUuidEntity;
import com.ruoyi.common.enums.FlowBusinessTypeEnum;
import lombok.Data;

/**
 * 流程名称对象 flow_name
 *
 * @author ruoyi
 * @date 2021-05-07
 */

@Data
public class FlowName extends BaseUuidEntity {
    /**
     * 流程KEY
     */
    @Excel(name = "流程KEY")
    private String flowKey;

    /**
     * 流程名称
     */
    @Excel(name = "流程名称")
    private String flowTitle;

    /**
     * 内容
     */
    @Excel(name = "内容")
    private String flowContext;

    /**
     * 流程名称
     */
    @Excel(name = "业务名称")
    private String bussName;

    /**
     * 单位名称
     */
    @Excel(name = "单位名称")
    private String tenantName;

    /**
     * 流程业务类型
     * @see FlowBusinessTypeEnum#getCodeString()
     */
    private String flowBusinessType;

}
