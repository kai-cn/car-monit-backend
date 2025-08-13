package com.ruoyi.common.flow;

import lombok.Builder;
import lombok.Data;

import java.util.Map;

/**
 * @author gl
 * @description 流程操作相关属性
 * @date 2022-02-23
 */

@Data
@Builder
public class FlowAttribute {

    /**
     * 业务id
     */
    private String businessId;

    /**
     * 业务标题
     */
    private String businessTitle;

    /**
     * 流程状态
     */
    private String flowStatus;

    /**
     * 流程键
     */
    private String flowKey;

    /**
     * 扩展属性map
     */
    private Map<String, Object> extraMap;

}