package com.ruoyi.common.enums;

/**
 * @author gl
 * @description 业务状态
 * @date 2022-02-12
 */

public enum BusinessStatusEnum {

    NO_DEAL_WITH(0, "0", "未处理"),
    DEAL_WITH(1, "1", "已处理"),

    NO_REPLY(0, "0", "未回复"),
    REPLIED(1, "1","已回复"),

    NOT_READ(0, "0", "未阅读"),
    READ(1, "1", "已阅读"),

    NO_DELETE(0, "0", "未删除"),
    DELETED(1, "1", "已删除"),

    NO_SHOW(0, "0", "不显示"),
    SHOW(1, "1", "显示")

    ;

    private final Integer code;
    private final String codeString;
    private final String info;

    public Integer getCode() {
        return code;
    }

    public String getInfo() {
        return info;
    }

    public String getCodeString() {
        return codeString;
    }

    BusinessStatusEnum(Integer code, String codeString, String info) {
        this.code = code;
        this.codeString = codeString;
        this.info = info;
    }

}