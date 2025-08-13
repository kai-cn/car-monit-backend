package com.ruoyi.common.flow;

import java.util.HashMap;
import java.util.Map;

/**
 * @author gl
 * @version 1.0
 * @description
 * @date 2023/2/27 9:45
 */

public interface Audit {

    /**
     * 默认处理函数
     */
    String DEFAULT_DEAL_METHOD = "endCallback";

    /**
     * 获取流程key
     * @return
     */
    String getKey();

    /**
     * 流程结束回调
     * @param businessId 业务id
     * @param flowStatus 流程状态
     */
    void endCallback(String businessId, String flowStatus);

    /**
     * 获取-key对应的处理函数
     * Map<String, String> dealMap => {
     *     key => flowKey 流程key
     *     value => 对应的处理函数名称
     * }
     *
     * 注意: 如果重写这个函数 需要将 getKey() 对应的处理函数放入map中
     * @return
     */
    default Map<String, String> getDealMap() {
        Map<String, String> dealMap = new HashMap<>(1);
        dealMap.put(getKey(), DEFAULT_DEAL_METHOD);
        return dealMap;
    }

}
