package com.ruoyi.manager.domain.vo.bigscreen;

import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 大屏导出请求。展示字段路径（display）与全字段路径（full）共用，但校验规则不同。
 *
 * @author car-monit-backend-java-v3
 */
@Data
public class ExportRequest
{
    /** 表类型：snapshot / fee / trail */
    private String type;

    /** 开始时间 yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss */
    private String startTime;

    /** 结束时间 yyyy-MM-dd 或 yyyy-MM-dd HH:mm:ss */
    private String endTime;

    /** 模糊过滤字段（key=逻辑字段名，value=关键词） */
    private Map<String, String> fuzzyFields;

    /** 展示字段（仅 display 路径生效；为空时使用默认展示字段） */
    private List<String> fields;

    /** 全字段导出的用途说明（full 路径必填） */
    private String purpose;
}
