package com.ruoyi.integration.api;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/**
 * backend → api 调用预算配置。
 *
 * <p>超时预算原则：backend 读超时 > api 侧处理超时 + 缓冲；重试只用于幂等 GET，
 * POST（导出提交）不重试；熔断窗口独立于超时。</p>
 *
 * @author car-monit-backend-java-v3
 */
@Component
@ConfigurationProperties(prefix = "traffic-api")
public class TrafficApiProperties
{
    /** 连接超时（所有场景） */
    private int connectTimeoutMs = 1000;

    /** 列表读超时（api 列表 SLO ≤2s） */
    private int listReadTimeoutMs = 2500;

    /** 扩展流水列表读超时（api 侧走 GaussDB 分页） */
    private int flowExtendedReadTimeoutMs = 5000;

    /** 轨迹在线查询读超时（ES 元数据 + 轨迹点批量回查） */
    private int trailReadTimeoutMs = 6000;

    /** 统计读超时（api traffic.bigscreen.query-timeout-ms=2000，留 1s 缓冲） */
    private int statsReadTimeoutMs = 3000;

    /** 实时预警列表读超时 */
    private int warningListReadTimeoutMs = 2000;

    /** 导出提交读超时（仅提交任务，不等待文件生成） */
    private int exportSubmitReadTimeoutMs = 6000;

    /** 导出状态读超时 */
    private int exportStatusReadTimeoutMs = 2000;

    /** 旧同步导出读超时（listToExport 会同步扫库） */
    private int legacyExportReadTimeoutMs = 30000;

    /** 列表/默认重试次数（幂等 GET） */
    private int retryCount = 1;

    /** 统计重试次数：默认 0，超时即降级，避免叠加重试延迟 */
    private int statsRetryCount = 0;

    /** 扩展流水重试次数：api 侧分页查询较重，不重试 */
    private int flowExtendedRetryCount = 0;

    /** 轨迹在线查询重试次数：api 侧含二次 DB 查询，不重试 */
    private int trailRetryCount = 0;

    /** 实时预警列表重试次数 */
    private int warningListRetryCount = 0;

    /** 导出提交重试次数：非幂等，固定 0 */
    private int exportSubmitRetryCount = 0;

    /** 导出状态重试次数 */
    private int exportStatusRetryCount = 1;

    /** 旧同步导出重试次数 */
    private int legacyExportRetryCount = 0;

    /** 重试退避基数（按尝试次数线性增长） */
    private long retryBackoffMs = 200;

    /** 熔断失败阈值 */
    private int circuitFailureThreshold = 5;

    /** 熔断打开窗口 */
    private long circuitOpenMs = 30000;

    /** 半开探测并发许可 */
    private int circuitHalfOpenPermits = 1;

    /** 404（契约未实现）冷却时间 */
    private long contractProbeIntervalMs = 60000;

    public int readTimeoutMs(TrafficApiScenario scenario)
    {
        switch (scenario)
        {
            case STATS:
                return statsReadTimeoutMs;
            case WARNING_LIST:
                return warningListReadTimeoutMs;
            case EXPORT_SUBMIT:
                return exportSubmitReadTimeoutMs;
            case EXPORT_STATUS:
                return exportStatusReadTimeoutMs;
            case LEGACY_EXPORT:
                return legacyExportReadTimeoutMs;
            case FLOW_EXTENDED:
                return flowExtendedReadTimeoutMs;
            case TRAIL:
                return trailReadTimeoutMs;
            case LIST:
            default:
                return listReadTimeoutMs;
        }
    }

    public int retries(TrafficApiScenario scenario)
    {
        switch (scenario)
        {
            case STATS:
                return statsRetryCount;
            case WARNING_LIST:
                return warningListRetryCount;
            case EXPORT_SUBMIT:
                return exportSubmitRetryCount;
            case EXPORT_STATUS:
                return exportStatusRetryCount;
            case LEGACY_EXPORT:
                return legacyExportRetryCount;
            case FLOW_EXTENDED:
                return flowExtendedRetryCount;
            case TRAIL:
                return trailRetryCount;
            case LIST:
            default:
                return retryCount;
        }
    }

    public int getConnectTimeoutMs()
    {
        return connectTimeoutMs;
    }

    public void setConnectTimeoutMs(int connectTimeoutMs)
    {
        this.connectTimeoutMs = connectTimeoutMs;
    }

    public int getListReadTimeoutMs()
    {
        return listReadTimeoutMs;
    }

    public void setListReadTimeoutMs(int listReadTimeoutMs)
    {
        this.listReadTimeoutMs = listReadTimeoutMs;
    }

    public int getFlowExtendedReadTimeoutMs()
    {
        return flowExtendedReadTimeoutMs;
    }

    public void setFlowExtendedReadTimeoutMs(int flowExtendedReadTimeoutMs)
    {
        this.flowExtendedReadTimeoutMs = flowExtendedReadTimeoutMs;
    }

    public int getTrailReadTimeoutMs()
    {
        return trailReadTimeoutMs;
    }

    public void setTrailReadTimeoutMs(int trailReadTimeoutMs)
    {
        this.trailReadTimeoutMs = trailReadTimeoutMs;
    }

    public int getStatsReadTimeoutMs()
    {
        return statsReadTimeoutMs;
    }

    public void setStatsReadTimeoutMs(int statsReadTimeoutMs)
    {
        this.statsReadTimeoutMs = statsReadTimeoutMs;
    }

    public int getWarningListReadTimeoutMs()
    {
        return warningListReadTimeoutMs;
    }

    public void setWarningListReadTimeoutMs(int warningListReadTimeoutMs)
    {
        this.warningListReadTimeoutMs = warningListReadTimeoutMs;
    }

    public int getExportSubmitReadTimeoutMs()
    {
        return exportSubmitReadTimeoutMs;
    }

    public void setExportSubmitReadTimeoutMs(int exportSubmitReadTimeoutMs)
    {
        this.exportSubmitReadTimeoutMs = exportSubmitReadTimeoutMs;
    }

    public int getExportStatusReadTimeoutMs()
    {
        return exportStatusReadTimeoutMs;
    }

    public void setExportStatusReadTimeoutMs(int exportStatusReadTimeoutMs)
    {
        this.exportStatusReadTimeoutMs = exportStatusReadTimeoutMs;
    }

    public int getLegacyExportReadTimeoutMs()
    {
        return legacyExportReadTimeoutMs;
    }

    public void setLegacyExportReadTimeoutMs(int legacyExportReadTimeoutMs)
    {
        this.legacyExportReadTimeoutMs = legacyExportReadTimeoutMs;
    }

    public int getRetryCount()
    {
        return retryCount;
    }

    public void setRetryCount(int retryCount)
    {
        this.retryCount = retryCount;
    }

    public int getStatsRetryCount()
    {
        return statsRetryCount;
    }

    public void setStatsRetryCount(int statsRetryCount)
    {
        this.statsRetryCount = statsRetryCount;
    }

    public int getFlowExtendedRetryCount()
    {
        return flowExtendedRetryCount;
    }

    public void setFlowExtendedRetryCount(int flowExtendedRetryCount)
    {
        this.flowExtendedRetryCount = flowExtendedRetryCount;
    }

    public int getTrailRetryCount()
    {
        return trailRetryCount;
    }

    public void setTrailRetryCount(int trailRetryCount)
    {
        this.trailRetryCount = trailRetryCount;
    }

    public int getWarningListRetryCount()
    {
        return warningListRetryCount;
    }

    public void setWarningListRetryCount(int warningListRetryCount)
    {
        this.warningListRetryCount = warningListRetryCount;
    }

    public int getExportSubmitRetryCount()
    {
        return exportSubmitRetryCount;
    }

    public void setExportSubmitRetryCount(int exportSubmitRetryCount)
    {
        this.exportSubmitRetryCount = exportSubmitRetryCount;
    }

    public int getExportStatusRetryCount()
    {
        return exportStatusRetryCount;
    }

    public void setExportStatusRetryCount(int exportStatusRetryCount)
    {
        this.exportStatusRetryCount = exportStatusRetryCount;
    }

    public int getLegacyExportRetryCount()
    {
        return legacyExportRetryCount;
    }

    public void setLegacyExportRetryCount(int legacyExportRetryCount)
    {
        this.legacyExportRetryCount = legacyExportRetryCount;
    }

    public long getRetryBackoffMs()
    {
        return retryBackoffMs;
    }

    public void setRetryBackoffMs(long retryBackoffMs)
    {
        this.retryBackoffMs = retryBackoffMs;
    }

    public int getCircuitFailureThreshold()
    {
        return circuitFailureThreshold;
    }

    public void setCircuitFailureThreshold(int circuitFailureThreshold)
    {
        this.circuitFailureThreshold = circuitFailureThreshold;
    }

    public long getCircuitOpenMs()
    {
        return circuitOpenMs;
    }

    public void setCircuitOpenMs(long circuitOpenMs)
    {
        this.circuitOpenMs = circuitOpenMs;
    }

    public int getCircuitHalfOpenPermits()
    {
        return circuitHalfOpenPermits;
    }

    public void setCircuitHalfOpenPermits(int circuitHalfOpenPermits)
    {
        this.circuitHalfOpenPermits = circuitHalfOpenPermits;
    }

    public long getContractProbeIntervalMs()
    {
        return contractProbeIntervalMs;
    }

    public void setContractProbeIntervalMs(long contractProbeIntervalMs)
    {
        this.contractProbeIntervalMs = contractProbeIntervalMs;
    }
}
