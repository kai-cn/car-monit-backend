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

    /** 下载令牌请求头：优先于历史 query 参数，避免令牌进入 URL。 */
    public static final String DOWNLOAD_TOKEN_HEADER = "X-Export-Download-Token";

    /** 审批 CAS 占位时长：覆盖一次 api 提交的最坏耗时（6s）+ 缓冲，失败自动过期。 */
    private static final long APPROVAL_CAS_SECONDS = 120L;

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
        requireExportSwitch();
        ExportPolicy.validateMode(request.getType(), mode);
        Long userId = SecurityUtils.getUserId();
        String username = SecurityUtils.getUsername();
        // 与控制器注解双重校验：控制器挡住未授权入口，服务层挡住内部调用/未来新增入口
        checkExportPermission(mode);
        // 服务端收敛机构范围：非管理员只能导出本机构数据
        request.setFuzzyFields(ExportPolicy.applyOrgScope(request.getType(),
                request.getFuzzyFields(), SecurityUtils.isAdmin(userId),
                SecurityUtils.getDeptSubCode()));
        request.setTenantId(safeTenantId());
        ExportPolicy.validateFuzzy(request.getFuzzyFields());
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
        return submitInternal(request, mode, userId, username, 1);
    }

    private Map<String, Object> submitInternal(ExportRequest request, String mode,
                                               Long userId, String username, int attempts)
    {
        Map<String, Object> body = new LinkedHashMap<String, Object>();
        // 与 api 现有 /api/v1/large/export/submit 契约兼容：api 读取 fuzzyFields.xxx 形式的键
        if (request.getFuzzyFields() != null)
        {
            for (Map.Entry<String, String> entry : request.getFuzzyFields().entrySet())
            {
                body.put("fuzzyFields." + (entry.getKey() == null ? "" : entry.getKey().trim()),
                        entry.getValue());
            }
        }
        if (ExportPolicy.MODE_FULL.equals(mode))
        {
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
        meta.setOrgCode(orgCodeOf(request));
        meta.setAdminScope(SecurityUtils.isAdmin(userId));
        meta.setTenantId(request.getTenantId());
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
        approval.setOrgCode(orgCodeOf(request));
        approval.setTenantId(request.getTenantId());
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
            Collection<String> keys = redisCache.scan(
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
     * 审批通过：先 CAS 抢占“审批中”，再按原申请人身份提交 api。
     *
     * <p>提交导出不是幂等操作（每次生成新 taskId 与文件），因此用 Redis
     * {@code setIfAbsent} 把并发审批收敛为一次；提交失败回退 pending 允许重试。</p>
     */
    public Map<String, Object> approve(String requestId, Long approverId)
    {
        requireExportSwitch();
        String casKey = approvalKey(requestId) + ":cas";
        Boolean acquired = redisCache.setCacheObjectIfAbsent(casKey, String.valueOf(approverId),
                APPROVAL_CAS_SECONDS, TimeUnit.SECONDS);
        if (!Boolean.TRUE.equals(acquired))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                    "审批正在处理中，请勿重复提交");
        }
        try
        {
            ExportApprovalRequest request = findApproval(requestId);
            if (request == null)
            {
                throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportApproval",
                        "审批请求不存在或已过期");
            }
            if (ExportApprovalStateMachine.APPROVING.equals(request.getStatus()))
            {
                // 上次提交可能在「api 已生成任务」与「写回 approved」之间中断，
                // 此时不允许重入，避免同一申请生成多份全量导出文件。
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                        "审批正在处理中或上次提交结果未知，请核查后重新提交申请，禁止重复审批");
            }
            if (!ExportApprovalStateMachine.canTransition(request.getStatus(),
                    ExportApprovalStateMachine.APPROVING))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                        "审批请求状态不允许通过: " + request.getStatus());
            }
            // 先落“审批中”，即使进程中断也不会被重复提交
            request.setStatus(ExportApprovalStateMachine.APPROVING);
            request.setApprovedBy(approverId);
            request.setApprovedAt(System.currentTimeMillis());
            redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                    (int) retentionSeconds(), TimeUnit.SECONDS);

            ExportRequest exportRequest = new ExportRequest();
            exportRequest.setType(request.getType());
            exportRequest.setStartTime(request.getStartTime());
            exportRequest.setEndTime(request.getEndTime());
            exportRequest.setPurpose(request.getPurpose());
            // 审批快照里的机构范围必须原样保留，不能被审批人的机构覆盖或悄悄丢弃
            Map<String, String> scoped = scopedFiltersForResubmit(request.getType(),
                    request.getFuzzyFields(), false, request.getOrgCode(), approverId,
                    false, "exportApproval");
            ExportPolicy.validateFuzzy(scoped);
            // 不再重复 validateFullFilters：过滤条件是入队时已校验并冻结的快照，
            // 审批阶段重探 api 能力矩阵（5 分钟缓存过期/404）只会新增失败点，
            // 让正常审批因探测抖动被回退成 PENDING。
            exportRequest.setFuzzyFields(scoped);
            exportRequest.setTenantId(request.getTenantId());

            Map<String, Object> result;
            try
            {
                result = submitInternal(exportRequest, request.getMode(),
                        request.getUserId(), request.getUsername(), 1);
            }
            catch (RuntimeException e)
            {
                // 提交失败回退 pending，允许审批人重试
                request.setStatus(ExportApprovalStateMachine.PENDING);
                redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                        (int) retentionSeconds(), TimeUnit.SECONDS);
                throw e;
            }

            request.setStatus(ExportApprovalStateMachine.APPROVED);
            request.setTaskId(String.valueOf(result.get("taskId")));
            redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                    (int) retentionSeconds(), TimeUnit.SECONDS);
            MetricsRegistry.increment("export.approval.approved");
            result.put("requestId", requestId);
            result.put("status", ExportApprovalStateMachine.APPROVED);
            return result;
        }
        finally
        {
            redisCache.deleteObject(casKey);
        }
    }

    public void reject(String requestId, Long approverId, String reason)
    {
        String casKey = approvalKey(requestId) + ":cas";
        Boolean acquired = redisCache.setCacheObjectIfAbsent(casKey, String.valueOf(approverId),
                APPROVAL_CAS_SECONDS, TimeUnit.SECONDS);
        if (!Boolean.TRUE.equals(acquired))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                    "审批正在处理中，请勿重复提交");
        }
        try
        {
            ExportApprovalRequest request = findApproval(requestId);
            if (request == null)
            {
                throw new ApiClientException(ApiErrorCode.NOT_FOUND, "exportApproval",
                        "审批请求不存在或已过期");
            }
            if (!ExportApprovalStateMachine.canTransition(request.getStatus(),
                    ExportApprovalStateMachine.REJECTED))
            {
                throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportApproval",
                        "审批请求状态不允许驳回: " + request.getStatus());
            }
            request.setStatus(ExportApprovalStateMachine.REJECTED);
            request.setApprovedBy(approverId);
            request.setApprovedAt(System.currentTimeMillis());
            request.setRejectReason(reason);
            redisCache.setCacheObject(approvalKey(requestId), JSON.toJSONString(request),
                    (int) retentionSeconds(), TimeUnit.SECONDS);
            MetricsRegistry.increment("export.approval.rejected");
        }
        finally
        {
            redisCache.deleteObject(casKey);
        }
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
     *
     * <p>重试不是管控盲区：重新校验 V3 开关、提交权限、限流与机构范围；
     * 全字段导出在审批开关打开时重新进入审批队列，不能凭历史审批无限重提。</p>
     */
    public Map<String, Object> retry(String taskId, Long requesterId)
    {
        requireExportSwitch();
        ExportTaskMeta meta = requireAccessibleTask(taskId, requesterId);
        // 角色可能在任务提交后被回收，重试必须重新校验
        checkExportPermission(meta.getMode());
        if (!meta.isAdminScope() && isBlank(meta.getOrgCode()))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportRetry",
                    "历史任务缺少机构范围，无法安全重试，请重新提交导出");
        }
        Map<String, Object> statusResponse = trafficApiClient.exportStatus(taskId);
        String status = statusResponse == null || statusResponse.get("status") == null
                ? "" : String.valueOf(statusResponse.get("status")).toLowerCase();
        if (!"failed".equals(status) && !"canceled".equals(status)
                && !"cancelled".equals(status) && !"paused".equals(status))
        {
            throw new ApiClientException(ApiErrorCode.INVALID_ARGUMENT, "exportRetry",
                    "仅 failed/canceled/paused 任务可重试，当前状态: " + status);
        }
        if (!rateLimiter.tryAcquire("retry", requesterId, SUBMIT_LIMIT_PER_HOUR, 3600))
        {
            throw new ApiClientException(ApiErrorCode.RATE_LIMITED, "exportRetry",
                    "重试过于频繁，请稍后再试");
        }
        // 机构范围必须按「重试时的账号」重新收敛，不能原样复用历史过滤条件：
        // 否则调岗/解除机构绑定的账号可凭旧 taskId 反复导出原机构数据。
        Map<String, String> scoped = scopedFiltersForResubmit(meta.getType(), meta.getFuzzyFields(),
                meta.isAdminScope(), meta.getOrgCode(), requesterId, true, "exportRetry");
        ExportPolicy.validateFuzzy(scoped);
        ExportRequest request = new ExportRequest();
        request.setType(meta.getType());
        request.setStartTime(meta.getStartTime());
        request.setEndTime(meta.getEndTime());
        request.setPurpose(meta.getPurpose());
        request.setFuzzyFields(scoped);
        request.setFields(meta.getFields());
        request.setTenantId(meta.getTenantId());

        // 审批开启时，非管理员的全字段重试重新走审批，避免“审批一次后无限重试”
        if (ExportPolicy.MODE_FULL.equals(meta.getMode())
                && featureSwitchService.isEnabled(FeatureSwitchService.EXPORT_APPROVAL)
                && !SecurityUtils.isAdmin(meta.getUserId()))
        {
            ExportPolicy.validatePurpose(request.getPurpose());
            ExportPolicy.validateFullFilters(request.getType(), request.getFuzzyFields(),
                    capabilityService.current());
            Map<String, Object> approval = createApproval(request, meta.getMode(),
                    meta.getUserId(), meta.getUsername());
            approval.put("retriedFrom", taskId);
            approval.put("resumeMode", "reapproval");
            MetricsRegistry.increment("export.retry");
            return approval;
        }

        Map<String, Object> result = submitInternal(request, meta.getMode(),
                meta.getUserId(), meta.getUsername(), Math.max(1, meta.getAttempts()) + 1);
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
        // 令牌不再拼进 URL：前端通过短生命周期请求头传递，避免出现在访问日志/Referer/代理缓存中
        result.put("url", "/manager/bigScreen/export/download/" + taskId);
        result.put("downloadToken", token);
        result.put("tokenHeader", DOWNLOAD_TOKEN_HEADER);
        result.put("expiresIn", downloadTokenService.getTokenTtlSeconds());
        return result;
    }

    public void download(String taskId, String token, HttpServletResponse response)
    {
        validateTaskId(taskId);
        // 下载响应不应被缓存，也不应把 URL（含历史 query token）带给第三方
        response.setHeader("Referrer-Policy", "no-referrer");
        response.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
        response.setHeader("Pragma", "no-cache");
        Long loginUserId = SecurityUtils.getUserId();
        // 签名令牌是每次下载的必需凭证：既限定 15 分钟时效，也把下载绑定到登录用户
        if (token == null || token.trim().isEmpty())
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload",
                    "缺少下载令牌，请先调用 download-url 获取签名令牌");
        }
        Long tokenUserId = downloadTokenService.verify(token, taskId);
        if (!tokenUserId.equals(loginUserId))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload",
                    "下载令牌与当前登录用户不匹配");
        }
        ExportTaskMeta meta = requireAccessibleTask(taskId, loginUserId);
        if (!meta.getUserId().equals(loginUserId) && !SecurityUtils.isAdmin(loginUserId))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportDownload", "无权下载该导出任务");
        }
        if (!rateLimiter.tryAcquire("download", loginUserId, downloadLimitPerMinute, 60))
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

    /**
     * 提交权限：展示导出需 {@code manager:bigscreen:export}；
     * 全字段导出还需 {@code manager:bigscreen:exportFull}。
     */
    private void checkExportPermission(String mode)
    {
        if (!SecurityUtils.hasPermi("manager:bigscreen:export"))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportSubmit",
                    "无导出权限（manager:bigscreen:export）");
        }
        if (ExportPolicy.MODE_FULL.equals(mode)
                && !SecurityUtils.hasPermi("manager:bigscreen:exportFull"))
        {
            throw new ApiClientException(ApiErrorCode.FORBIDDEN, "exportSubmit",
                    "全字段导出需要权限 manager:bigscreen:exportFull");
        }
    }

    private void requireExportSwitch()
    {
        if (!featureSwitchService.isEnabled(FeatureSwitchService.EXPORT_V3))
        {
            throw new ApiClientException(ApiErrorCode.UNAVAILABLE, "exportSubmit",
                    "V3 导出已通过开关关闭，请使用旧导出入口");
        }
    }

    /**
     * 重提（retry/resume/approve）时的机构范围收敛。
     *
     * <p>retry/resume 走 {@link ExportPolicy#applyOrgScope} 按「当前登录账号」重新收敛：
     * 调岗、机构解绑、机构不一致、非管理员导出 trail 都会被拒绝，且不会沿用历史 orgcode。
     * approve 走「申请时的授权快照」：非管理员申请必须有有效机构快照并原样保留，
     * 不允许审批人（可能属于其它机构）扩大范围。</p>
     */
    private Map<String, String> scopedFiltersForResubmit(String type, Map<String, String> fuzzyFields,
                                                         boolean adminScope, String storedOrgCode,
                                                         Long requesterId, boolean enforceRequesterScope,
                                                         String endpoint)
    {
        Map<String, String> scoped = new LinkedHashMap<String, String>();
        if (fuzzyFields != null)
        {
            for (Map.Entry<String, String> entry : fuzzyFields.entrySet())
            {
                if (entry.getKey() == null || entry.getKey().trim().isEmpty())
                {
                    continue;
                }
                scoped.put(entry.getKey().trim(), entry.getValue());
            }
        }
        if (enforceRequesterScope)
        {
            return ExportPolicy.applyOrgScope(type, scoped,
                    SecurityUtils.isAdmin(requesterId), SecurityUtils.getDeptSubCode());
        }
        if (!adminScope)
        {
            if (isBlank(storedOrgCode) || "-1".equals(storedOrgCode.trim()))
            {
                throw new ApiClientException(ApiErrorCode.FORBIDDEN, endpoint,
                        "审批请求缺少有效机构范围，无法安全提交，请重新申请");
            }
            scoped.put("orgcode", storedOrgCode.trim());
        }
        return ExportPolicy.applyOrgScope(type, scoped, true, null);
    }

    private String orgCodeOf(ExportRequest request)
    {
        if (request.getFuzzyFields() == null)
        {
            return null;
        }
        for (Map.Entry<String, String> entry : request.getFuzzyFields().entrySet())
        {
            if (entry.getKey() != null && "orgcode".equalsIgnoreCase(entry.getKey().trim()))
            {
                String value = entry.getValue();
                return value == null || value.trim().isEmpty() ? null : value.trim();
            }
        }
        return null;
    }

    private Long safeTenantId()
    {
        try
        {
            return SecurityUtils.getTenantId();
        }
        catch (RuntimeException e)
        {
            return null;
        }
    }

    private boolean isBlank(String value)
    {
        return value == null || value.trim().isEmpty();
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
