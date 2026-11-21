package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

/**
 * @Author: zhukai
 * @Date: 2025/08/28/15:00
 * @Description:
 */
@Data
public class SectionVO {

    /**
     * 所属路段编码
     */
    private String sectionCode;

    /**
     * 所属路段名称
     */
    private String sectionName;

    /**
     * 所属路线名称（流水列表/导出回填用）
     */
    private String roadName;

}
