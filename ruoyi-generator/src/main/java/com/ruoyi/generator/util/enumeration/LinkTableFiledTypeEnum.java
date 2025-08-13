package com.ruoyi.generator.util.enumeration;

import lombok.Getter;

/**
 * @author gl
 * @version 1.0
 * @description 关联表字段类型枚举
 * @date 2022/9/13 10:29
 */

@Getter
public enum LinkTableFiledTypeEnum {

    /**
     * 表中的字段
     */
    TABLE("10", "表中的字段"),

    /**
     * 自定义字段
     */
    CUSTOM_FIELD("20", "自定义字段")

    ;

    private final String code;
    private final String info;

    LinkTableFiledTypeEnum(String code, String info) {
        this.code = code;
        this.info = info;
    }

}
