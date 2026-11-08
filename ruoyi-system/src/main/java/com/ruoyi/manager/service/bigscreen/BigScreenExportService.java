package com.ruoyi.manager.service.bigscreen;

import com.alibaba.fastjson2.JSON;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.metrics.MetricsRegistry;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import com.ruoyi.integration.api.TrafficApiClient;
import com.ruoyi.integration.api.TrafficQueryContract;
import com.ruoyi.manager.domain.vo.bigscreen.ExportApprovalRequest;
import com.ruoyi.manager.domain.vo.bigscreen.ExportRequest;
import com.ruoyi.manager.domain.vo.bigscreen.ExportTaskMeta;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestTemplate;

import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/**
 * 大屏导出编排：
 * <ul>
 *   <li>display：展示字段快速导出（api 走 ES PIT）；</li>
 *   <li>full：全字段海量导出（api 走 GaussDB 分区游标，异步、限流、需用途与权限）；</li>
 *   <li>任务元数据落 Redis（7 天），下载前校验归属；</li>
 *   <li>下载令牌 HMAC 15 分钟 + 每分钟限流。</li>
 * </ul>
 *
 * @author car-monit-backend-java-v3
 */
@Service
public class BigScreenExportService
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenExportService.class);

    private static final int SUBMIT_LIMIT_PER_HOUR = 10;

    /** 导出任务元数据/审批请求保留期（天），默认 7 天，到期由 Redis TTL 清理。 */
    @Value("${export.retention-days:7}")
    private int retentionDays;

    @Value("${export.download.rate-limit-per-minute:6}")
    private int downloadLimitPerMinute;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private RedisCache redisCache;

    @Autowired
    private DownloadTokenService downloadTokenService;

    @Autowired
    private ExportRateLimiter rateLimiter;

    @Autowired
    private ExportCapabilityService capabilityService;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    /** 提交后仍在 api 侧运行的任务，用于积压指标（status 轮询到终态后移除）。 */
    private final Map<String, Long> activeTasks = new ConcurrentHashMap<String, Long>();

    @Value("${vehicleMonitor.baseUrl}")
    private String apiBaseUrl;

    @Value("${spring.profiles.active:dev}")
    private String env;

    @Autowired
    @Qualifier("trafficApiDownloadRestTemplate")
    private RestTemplate downloadRestTemplate;

    public Map<String, Object> submit(ExportRequest request, String mode)
    {
        if (!featureSwitchService.isEnabled(FeatureSwitchService.EXPORT_V3))
        {
            throw new ApiClientException(ApiErrorCode.UNAVAILABLE, "exportSubmit",
                    "V3 导出已通过开关关闭，请使用旧导出入口");
        }
        ExportPolicy.validateMode(request.getType(), mode);
        ExportPolicy.validateFuzzy(request.getFuzzyFields());
        Long userId = SecurityUtils.getUserId();
        String username = SecurityUtils.getUsername();
        if (!rateLimiter.tryAcquire("submit:" + mode, userId, SUBMIT_LIMIT_PER_HOUR, 3600))
        {
            throw new ApiClientException(ApiErrorCode.RATE_LIMITED, "exportSubmit",
                    "导出提交过于频繁，请稍后再试");
        }

        // 审批开关打开时，非 admin 的全字段导出先进入待审批队列，不调用 api
        if (ExportPolicy.MODE_FULL.equals(mode)
                && featureSwitchService.isEnabled(FeatureSwitchService.EXPORT_APPROVAL)
                && !SecurityUtils.isAdmin(userId))
        {
            // 入队前先校验用途与过滤能力，避免审批通过后才失败
            ExportPolicy.validatePurpose(request.getPurpose());
            ExportPolicy.validateFullFilters(request.getType(), request.getFuzzyFields(),
                    capabilityService.current());
            return createApproval(request, mode, userId, username);
        }
        return submitInternal(request, mode, userId, username, false, 1);
    }

    private Map<String, Object> submitInternal(ExportRequest request, String mode,
                                               Long userId, String username,
                                               boolean approvalBypassed, int attempts)
    {
        Map<String, Object> body = new LinkedHashMap<String, Object>();
        // 与 api 现有 /api/v1/large/export/submit 契约兼容：api 读取 fuzzyFields.xxx 形式的键
        if (request.getFuzzyFields() != null)
        {
            for (Map.Entry<String, String> entry : request.getFuzzyFields().entrySet())
            {
                body.put("fuzzyFields." + entry.getKey(), entry.getValue());
            }
        }
        if (ExportPolicy.MODE_FULL.equals(mode))
        {
            if (!approvalBypassed)
            {
                checkFullExportPermission(userId);
            }
            ExportPolicy.validatePurpose(request.getPurpose());
            ExportCapabilityService.Capabilities capabilities = capabilityService.current();
            ExportPolicy.validateFullFilters(request.getType(), request.getFuzzyFields(),
                    capabilities);
            body.put("fields", Collections.emptyList());
            body.put("purpose", request.getPurpose());
        }
        else
        {
            ExportCapabilityService.Capabilities capabilities = capabilityService.current();
            List<String> fields = ExportPolicy.resolveDisplayFields(request.getType(),
                    request.getFields(), capabilities.supportsPlateColorName(request.getType()));
            body.put("fields", fields);
            body.put("purpose", request.getPurpose());
        }

        Map<String, Object> response = trafficApiClient.submitExport(request.getType(),
                request.getStartTime(), request.getEndTime(), mode, body);
        String taskId = String.valueOf(response.get("taskId"));

        ExportTaskMeta meta = new ExportTaskMeta();
        meta.setTaskId(taskId);
        meta.setUserId(userId);
        meta.setUsername(username);
        meta.setType(request.getType());
        meta.setMode(mode);
        meta.setStartTime(request.getStartTime());
        meta.setEndTime(request.getEndTime());
        meta.setPurpose(request.getPurpose());
        meta.setFuzzyFields(request.getFuzzyFields());
        meta.setFields(request.getFields());
        meta.setSubmittedAt(System.currentTimeMillis());
        meta.setUpdatedAt(meta.getSubmittedAt());
        meta.setStatus("pending");
        meta.setAttempts(attempts);
        redisCache.setCacheObject(taskKey(taskId), JSON.toJSONString(meta),
                (int) retentionSeconds(), TimeUnit.SECONDS);

        activeTasks.put(taskId, System.currentTimeMillis());
        MetricsRegistry.increment("export.submitted");
        MetricsRegistry.setGauge("export.active", activeTasks.size());
        if (ExportPolicy.MODE_FULL.equals(mode))
        {
            MetricsRegistry.increment("export.full.submitted");
        }

        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("taskId", taskId);
        result.put("mode", mode);
        result.put("status", "pending");
        result.put("message", "导出任务已提交");
        return result;
    }

    // ------------------------------------------------------------------
    // 全字段导出审批（阶段三）
    // ------------------------------------------------------------------

    private Map<String, Object> createApproval(ExportRequest request, String mode,
                                               Long userId, String username)
    {
        ExportApprovalRequest approval = new ExportApprovalRequest();
        approval.setRequestId(UUID.randomUUID().toString().replace("-", ""));
        approval.setUserId(userId);
        approval.setUsername(username);
        approval.setType(request.getType());
        approval.setMode(mode);
        approval.setStartTime(request.getStartTime());
        approval.setEndTime(request.getEndTime());
        approval.setPurpose(request.getPurpose());
        approval.setFuzzyFields(request.getFuzzyFields());
        approval.setStatus("pending");
        approval.setCreatedAt(System.currentTimeMillis());
        redisCache.setCacheObject(approvalKey(approval.getRequestId()),
                JSON.toJSONString(approval), (int) retentionSeconds(), TimeUnit.SECONDS);

        MetricsRegistry.increment("export.approval.pending");
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("requestId", approval.getRequestId());
        result.put("mode", mode);
        result.put("status", "pending_approval");
        result.put("message", "全字段导出已提交审批，审批通过后自动提交任务");
        return result;
    }

    public ExportApprovalRequest findApproval(String requestId)
    {
        if (requestId == null || !requestId.matches("[A-Za-z0-9_-]{1,64}"))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                    "非法审批请求 ID");
        }
        Object raw = redisCache.getCacheObject(approvalKey(requestId));
        return raw == null ? null : JSON.parseObject(String.valueOf(raw),
                ExportApprovalRequest.class);
    }

    public List<ExportApprovalRequest> pendingApprovals()
    {
        List<ExportApprovalRequest> result = new ArrayList<ExportApprovalRequest>();
        try
        {
            Collection<String> keys = redisCache.keys(
                    "cm:" + env + ":export:approval:*");
            if (keys == null)
            {
                return result;
            }
            for (String key : keys)
            {
                Object raw = redisCache.getCacheObject(key);
                if (raw == null)
                {
                    continue;
                }
                ExportApprovalRequest request = JSON.parseObject(String.valueOf(raw),
                        ExportApprovalRequest.class);
                if (request != null && "pending".equals(request.getStatus()))
                {
                    result.add(request);
                }
            }
        }
        catch (RuntimeException e)
        {
            log.warn("[导出审批] 查询待审批列表失败: {}", e.getMessage());
        }
        return result;
    }

    /**
     * 审批通过：按原申请人身份提交 api，并把 taskId 回写到审批记录。
     */
    public Map<String, Object> approve(String requestId, Long approverId)
    {
        ExportApprovalRequest request = findApproval(requestId);
        if (request == null)
        {
            throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportApproval",
                    "审批请求不存在或已过期");
        }
        if (!"pending".equals(request.getStatus()))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                    "审批请求状态非 pending: " + request.getStatus());
        }
        ExportRequest exportRequest = new ExportRequest();
        exportRequest.setType(request.getType());
        exportRequest.setStartTime(request.getStartTime());
        exportRequest.setEndTime(request.getEndTime());
        exportRequest.setPurpose(request.getPurpose());
        exportRequest.setFuzzyFields(request.getFuzzyFields());

        Map<String, Object> result = submitInternal(exportRequest, request.getMode(),
                request.getUserId(), request.getUsername(), true, 1);
        request.setStatus("approved");
        request.setApprovedBy(approverId);
        request.setApprovedAt(System.currentTimeMillis());
        request.setTaskId(String.valueOf(result.get("taskId")));
        redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                (int) retentionSeconds(), TimeUnit.SECONDS);
        MetricsRegistry.increment("export.approval.approved");
        result.put("requestId", requestId);
        result.put("status", "approved");
        return result;
    }

    public void reject(String requestId, Long approverId, String reason)
    {
        ExportApprovalRequest request = findApproval(requestId);
        if (request == null)
        {
            throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportApproval",
                    "审批请求不存在或已过期");
        }
        if (!"pending".equals(request.getStatus()))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                    "审批请求状态非 pending: " + request.getStatus());
        }
        request.setStatus("rejected");
        request.setApprovedBy(approverId);
        request.setApprovedAt(System.currentTimeMillis());
        request.setRejectReason(reason);
        redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                (int) retentionSeconds(), TimeUnit.SECONDS);
        MetricsRegistry.increment("export.approval.rejected");
    }

    private String approvalKey(String requestId)
    {
        return "cm:" + env + ":export:approval:" + requestId;
    }

    private long retentionSeconds()
    {
        return Math.max(1, retentionDays) * 24L * 3600L;
    }

    public Map<String, Object> status(String taskId)
    {
        ExportTaskMeta meta = requireAccessibleTask(taskId, SecurityUtils.getUserId());
        Map<String, Object> response = trafficApiClient.exportStatus(taskId);
        Map<String, Object> result = new LinkedHashMap<String, Object>(response);
        result.put("mode", meta.getMode());
        result.put("type", meta.getType());
        result.put("submittedAt", meta.getSubmittedAt());
        Object statusValue = response.get("status");
        if (statusValue != null)
        {
            meta.setStatus(String.valueOf(statusValue));
            meta.setUpdatedAt(System.currentTimeMillis());
            Object error = response.get("error");
            if (error != null)
            {
                meta.setLastError(String.valueOf(error));
            }
            redisCache.setCacheObject(taskKey(taskId), JSON.toJSONString(meta),
                    (int) retentionSeconds(), TimeUnit.SECONDS);
        }
        trackTerminal(taskId, response);
        return result;
    }

    /**
     * 失败重试 / 断点续传：api 无续传接口时按原参数重新提交（新 taskId），
     * 仅允许失败/取消/暂停任务；原任务元数据保留用于审计。
     */
    public Map<String, Object> retry(String taskId, Long requesterId)
    {
        ExportTaskMeta meta = requireAccessibleTask(taskId, requesterId);
        Map<String, Object> statusResponse = trafficApiClient.exportStatus(taskId);
        String status = statusResponse == null || statusResponse.get("status") == null
                ? "" : String.valueOf(statusResponse.get("status")).toLowerCase();
        if (!"failed".equals(status) && !"canceled".equals(status)
                && !"cancelled".equals(status) && !"paused".equals(status))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportRetry",
                    "仅 failed/canceled/paused 任务可重试，当前状态: " + status);
        }
        ExportRequest request = new ExportRequest();
        request.setType(meta.getType());
        request.setStartTime(meta.getStartTime());
        request.setEndTime(meta.getEndTime());
        request.setPurpose(meta.getPurpose());
        request.setFuzzyFields(meta.getFuzzyFields());
        request.setFields(meta.getFields());
        Map<String, Object> result = submitInternal(request, meta.getMode(),
                meta.getUserId(), meta.getUsername(), true, Math.max(1, meta.getAttempts()) + 1);
        result.put("retriedFrom", taskId);
        result.put("resumeMode", "resubmit");
        MetricsRegistry.increment("export.retry");
        return result;
    }

    /**
     * 清理长时间未轮询到终态的本地积压指标（Redis 元数据由 TTL 清理）。
     */
    public int cleanupStaleTasks()
    {
        long cutoff = System.currentTimeMillis() - retentionSeconds() * 1000L;
        int removed = 0;
        for (Map.Entry<String, Long> entry : activeTasks.entrySet())
        {
            if (entry.getValue() < cutoff && activeTasks.remove(entry.getKey()) != null)
            {
                removed++;
            }
        }
        if (removed > 0)
        {
            MetricsRegistry.add("export.cleanup", removed);
            MetricsRegistry.setGauge("export.active", activeTasks.size());
            log.info("[导出] 清理过期运行中任务 {} 个", removed);
        }
        return removed;
    }

    /**
     * 轮询到终态时更新导出积压/完成/失败指标；同一 taskId 只计一次。
     */
    private void trackTerminal(String taskId, Map<String, Object> response)
    {
        Object statusValue = response == null ? null : response.get("status");
        if (statusValue == null)
        {
            return;
        }
        String status = String.valueOf(statusValue).toLowerCase();
        boolean terminal = "done".equals(status) || "failed".equals(status)
                || "canceled".equals(status) || "cancelled".equals(status);
        if (!terminal || activeTasks.remove(taskId) == null)
        {
            return;
        }
        if ("done".equals(status))
        {
            MetricsRegistry.increment("export.completed");
        }
        else if ("failed".equals(status))
        {
            MetricsRegistry.increment("export.failed");
        }
        MetricsRegistry.setGauge("export.active", activeTasks.size());
    }

    public Map<String, Object> createDownloadInfo(String taskId)
    {
        ExportTaskMeta meta = requireAccessibleTask(taskId, SecurityUtils.getUserId());
        String token = downloadTokenService.sign(taskId, meta.getUserId());
        Map<String, Object> result = new LinkedHashMap<String, Object>();
        result.put("url", "/manager/bigScreen/export/download/" + taskId + "?token=" + token);
        result.put("expiresIn", downloadTokenService.getTokenTtlSeconds());
        return result;
    }

    public void download(String taskId, String token, HttpServletResponse response)
    {
        validateTaskId(taskId);
        Long requester = token != null && !token.trim().isEmpty()
                ? downloadTokenService.verify(token, taskId)
                : SecurityUtils.getUserId();
        ExportTaskMeta meta = requireAccessibleTask(taskId, requester);
        if (!meta.getUserId().equals(requester) && !SecurityUtils.isAdmin(requester))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "无权下载该导出任务");
        }
        if (!rateLimiter.tryAcquire("download", requester, downloadLimitPerMinute, 60))
        {
            writeError(response, 429,
                    "下载过于频繁，请稍后再试");
            return;
        }

        String url = apiBaseUrl + "/api/v1/large/export/download/" + taskId;
        try
        {
            downloadRestTemplate.execute(url, HttpMethod.GET, null,
                    (org.springframework.http.client.ClientHttpResponse resp) ->
                    {
                        response.setStatus(resp.getRawStatusCode());
                        MediaType contentType = resp.getHeaders().getContentType();
                        response.setContentType(contentType == null
                                ? "application/octet-stream" : contentType.toString());
                        String disposition = resp.getHeaders().getFirst("Content-Disposition");
                        if (disposition != null)
                        {
                            response.setHeader("Content-Disposition", disposition);
                        }
                        copy(resp.getBody(), response.getOutputStream());
                        return null;
                    });
        }
        catch (HttpStatusCodeException e)
        {
            log.warn("[导出下载] api 返回异常 taskId={} status={}", taskId, e.getRawStatusCode());
            writeError(response, e.getRawStatusCode(), "导出文件暂不可下载");
        }
        catch (ResourceAccessException e)
        {
            log.warn("[导出下载] api 不可达 taskId={} reason={}", taskId, e.getMessage());
            writeError(response, HttpServletResponse.SC_GATEWAY_TIMEOUT, "导出文件服务暂不可用");
        }
        catch (org.springframework.web.client.RestClientException e)
        {
            log.warn("[导出下载] 下载失败 taskId={} reason={}", taskId, e.getMessage());
            if (!response.isCommitted())
            {
                writeError(response, HttpServletResponse.SC_INTERNAL_SERVER_ERROR, "下载失败");
            }
        }
    }

    public String taskKey(String taskId)
    {
        return "cm:" + env + ":export:task:" + taskId;
    }

    public ExportTaskMeta findTask(String taskId)
    {
        validateTaskId(taskId);
        Object raw = redisCache.getCacheObject(taskKey(taskId));
        if (raw == null)
        {
            return null;
        }
        return JSON.parseObject(String.valueOf(raw), ExportTaskMeta.class);
    }

    private void validateTaskId(String taskId)
    {
        if (taskId == null || !taskId.matches("[A-Za-z0-9_-]{1,64}"))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportTask",
                    "非法 taskId");
        }
    }

    private ExportTaskMeta requireAccessibleTask(String taskId, Long userId)
    {
        ExportTaskMeta meta = findTask(taskId);
        if (meta == null)
        {
            throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportStatus",
                    "导出任务不存在或已过期");
        }
        if (!meta.getUserId().equals(userId) && !SecurityUtils.isAdmin(userId))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportStatus", "无权访问该导出任务");
        }
        return meta;
    }

    private void checkFullExportPermission(Long userId)
    {
        if (SecurityUtils.isAdmin(userId))
        {
            return;
        }
        boolean allowed = SecurityUtils.hasPermi("manager:bigscreen:exportFull")
                || SecurityUtils.hasPermi("manager:bigscreen:export");
        if (!allowed)
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportSubmit",
                    "全字段导出需要审批权限");
        }
    }

    private void copy(InputStream inputStream, OutputStream outputStream) throws IOException
    {
        if (inputStream == null)
        {
            return;
        }
        byte[] buffer = new byte[8192];
        int read;
        while ((read = inputStream.read(buffer)) != -1)
        {
            outputStream.write(buffer, 0, read);
        }
        outputStream.flush();
    }

    private void writeError(HttpServletResponse response, int status, String message)
    {
        if (response.isCommitted())
        {
            return;
        }
        try
        {
            response.setStatus(status);
            response.setCharacterEncoding(StandardCharsets.UTF_8.name());
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write(JSON.toJSONString(AjaxResult.error(message)));
            response.getWriter().flush();
        }
        catch (IOException e)
        {
            log.warn("[导出下载] 写错误响应失败: {}", e.getMessage());
        }
    }
}
