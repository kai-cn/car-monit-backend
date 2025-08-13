package com.ruoyi.common.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @author gl
 * @version 1.0
 * @description 流程业务类型
 * @date 2023/2/20 11:29
 */

@Getter
@AllArgsConstructor
public enum FlowBusinessTypeEnum {

    /**
     * 工作流类型
     */
    WORKFLOW(1, "1", "工作流类型"),

    /**
     * 业务流类型
     */
    BUSINESS(2, "2", "业务流类型")

    ;

    private final Integer code;
    private final String codeString;
    private final String info;

}
