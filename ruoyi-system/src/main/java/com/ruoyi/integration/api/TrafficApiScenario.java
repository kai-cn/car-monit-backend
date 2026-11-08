package com.ruoyi.integration.api;

/**
 * api 调用场景：用于选择连接/读超时与重试次数。
 *
 * <p>超时预算必须与 api 侧超时保持“backend 读超时 > api 处理超时”，避免 backend 先超时导致误降级。</p>
 *
 * @author car-monit-backend-java-v3
 */
public enum TrafficApiScenario
{
    /** 列表查询（门架/收费） */
    LIST,

    /**
     * 扩展流水列表（省界/收费站抓拍、称重、服务区、出入口等）。
     * api 侧仍走 GaussDB 分页，读超时比三表 ES 列表更宽。
     */
    FLOW_EXTENDED,

    /** 轨迹在线查询（api 侧 ES 元数据 + GaussDB 轨迹点批量回查） */
    TRAIL,

    /** 大屏预聚合统计（api query-timeout 2s，backend 读 3s） */
    STATS,

    /** 大屏实时预警列表（api 尚未实现） */
    WARNING_LIST,

    /** 导出任务提交（异步，返回 taskId） */
    EXPORT_SUBMIT,

    /** 导出任务状态查询 */
    EXPORT_STATUS,

    /** 旧同步导出（listToExport，1 万条上限） */
    LEGACY_EXPORT
}
