package com.ruoyi.flow.domain;

import com.alibaba.fastjson2.annotation.JSONField;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * @author gl
 * @description 流程委派信息
 * @date 2022-03-24
 */

@Data
public class EntrustInfo {

    /**
     * 操作人id
     */
    private String operatorUserId;

    /**
     * 操作人名称
     */
    private String operatorUserName;

    /**
     * 委托人id
     */
    private String entrustUserId;

    /**
     * 委托人名称
     */
    private String entrustUserName;

    /**
     * 流程id, flow_name表的id字段
     */
    private String flowId;

    /**
     * 流程键, flow_name表中的flow_key字段
     */
    private String flowKey;

    /**
     * 流程模板id, flow_template表的id字段
     */
    private String flowTemplateId;

    /**
     * 操作时间
     */
    @JSONField(format = "yyyy-MM-dd HH:mm:ss.SS")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime operationTime;

}