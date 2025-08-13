package com.ruoyi.generator.domain;

import lombok.Data;
import lombok.experimental.Accessors;

/**
 * @author gl
 * @version 1.0
 * @description 字典信息
 * @date 2022/8/23 16:59
 */

@Data
@Accessors(chain = true)
public class DictionaryInfo {

    /**
     * 字典键名称
     */
    private String dictionaryKey;

    /**
     * 字典键名称-驼峰形式
     */
    private String dictionaryKeyCamelCase;

}
