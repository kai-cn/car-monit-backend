package com.ruoyi.generator.domain;

import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.generator.util.enumeration.LinkTableFiledTypeEnum;
import lombok.Data;

/**
 * @author gl
 * @version 1.0
 * @description 关联表字段映射信息
 * @date 2022/9/13 10:26
 */

@Data
public class LinkTableField {

    /**
     * 字段类型
     * 如果是 LinkTableFiledTypeEnum.TABLE.getCode类型获取 currentTableFileId 中的值
     * 如果是 LinkTableFiledTypeEnum.CUSTOM_FIELD.getCode类型获取 customFieldName 中的值
     * @see LinkTableFiledTypeEnum#getCode()
     */
    private String fieldType;

    /**
     * 当前表字段id
     */
    private Long currentTableFileId;

    /**
     * 关联表字段id
     */
    private Long linkTableFieldId;

    /**
     * 自定义字段名称
     */
    private String customFieldName;

    /**
     * 自定义字段注释
     */
    private String customFileComment;

    /**
     * 表字段别名, 将id转换成name
     */
    private String tableFileAlias;

    /**
     * 表字段信息
     */
    private GenTableColumn tableFileInfo;

    /**
     * 关联表字段信息
     */
    private GenTableColumn linkTableFieldInfo;

    public String getCustomFileComment() {
        if (StringUtils.isEmpty(customFileComment)) {
            return Constants.CHAR_BLANK;
        }

        return customFileComment;
    }

}
