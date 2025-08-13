package com.ruoyi.generator.domain;

import lombok.Data;
import lombok.experimental.Accessors;

import java.util.List;

/**
 * @author gl
 * @version 1.0
 * @description 上传组件信息
 * @date 2022/8/25 15:59
 */

@Data
@Accessors(chain = true)
public class GenerateUploadInfo {

    /**
     * 上传组件个数
     */
    private Integer uploadCount;

    /**
     * 上传组件的列信息
     */
    private List<GenTableColumn> uploadColumn;

    /**
     * 上传组件的字段名称, 如果存在多个, 则使用,号拼接
     */
    private String uploadFiledNames;

}
