package com.ruoyi.generator.domain;

import lombok.Data;

import java.util.List;

/**
 * @author gl
 * @version 1.0
 * @description 列表对话框信息
 * @date 2022/9/9 17:43
 */

@Data
public class GenColumnDialog {

    /**
     * 列表对话框数量
     */
    private Integer dialogNumber;

    /**
     * 多选对话框数量
     */
    private Integer checkboxNumber;

    /**
     * 单选对话框数量
     */
    private Integer radioNumber;

    /**
     * 对话框列表
     */
    private List<GenTableColumn> dialogColumnList;

    /**
     * 多选对话框列表
     */
    private List<GenTableColumn> checkBoxColumnList;

    /**
     * 单选对话框列表
     */
    private List<GenTableColumn> radioColumnList;

    /**
     * 全部-表字段列表
     */
    private List<LinkTableField> tableFieldList;

    /**
     * 全部-自定义字段列表
     */
    private List<LinkTableField> customFieldList;

    /**
     * 全部-字段列表信息
     */
    private List<LinkTableField> fieldList;

}
