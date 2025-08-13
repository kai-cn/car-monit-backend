package com.ruoyi.common.flow;

import com.ruoyi.common.core.domain.AjaxResult;

/**
 * @author gl
 * @description 流程操作接口
 * @date 2022-02-23
 */

public interface Flow {

    /**
     * 提交流程
     * @param flowAttribute 流程操作相关属性
     * @return
     */
     AjaxResult submitFlow(FlowAttribute flowAttribute);

    /**
     * 流程回调
     * @param id 业务id
     * @param flowStatus 流程状态
     * @return
     */
    AjaxResult callbackMethod(String id, String flowStatus);

}