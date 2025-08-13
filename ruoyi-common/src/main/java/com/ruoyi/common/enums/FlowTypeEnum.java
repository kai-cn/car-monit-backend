package com.ruoyi.common.enums;


import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @CLASSNAME FlowTypeEnum
 * @Description
 * @Auther JanHezz
 * @DATE 2021/3/18 15:36
 */

@Getter
@AllArgsConstructor
public enum FlowTypeEnum {
    /**
     * 起草中
     */
    SUBMIT(1, "1","起草中"),
    /**
     * 审批中
     */
    APPROVE(2, "2", "审批中"),

    /**
     * 审批通过
     */
    END(3, "3", "审批通过"),
    /**
     * 退回
     */
    RETURN(4, "4", "退回修改"),

    /**
     * 审批拒绝
     */
    STOP(5, "5","审批拒绝");

    private final int code;
    private final String codeString;
    private final String info;

}
