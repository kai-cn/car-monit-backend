package com.ruoyi.generator.domain;

import lombok.Data;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author gl
 * @version 1.0
 * @description 富文本信息
 * @date 2022/8/26 15:27
 */

@Data
@Accessors(chain = true)
public class GenerateRichTextInfo {

    /**
     * 富文本组件数量
     */
    private Integer richTextCount;

    /**
     * 富文本组件字段列表
     */
    private List<GenTableColumn> columnList;

}
