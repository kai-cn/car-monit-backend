package com.ruoyi.web.controller.manager.bigscreen;

import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import com.ruoyi.manager.domain.vo.bigscreen.ExportApprovalRequest;
import com.ruoyi.manager.domain.vo.bigscreen.ExportRequest;
import com.ruoyi.manager.service.bigscreen.BigScreenExportService;
import com.alibaba.fastjson2.JSON;
import io.swagger.annotations.ApiOperation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletResponse;
import java.util.Map;

/**
 * 大屏导出编排接口。
 *
 * <p>两条路径：{@code /display} 展示字段快速导出（ES PIT）；{@code /full} 全字段海量导出（GaussDB 游标）。
 * 导出均为异步任务，返回 taskId；下载通过 15 分钟签名 URL，并受用户归属与限流约束。</p>
 *
 * @author car-monit-backend-java-v3
 */
@ApiOperation("大屏导出")
@RestController
@RequestMapping("/manager/bigScreen/export")
public class BigScreenExportController extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenExportController.class);

    @Autowired
    private BigScreenExportService bigScreenExportService;

    @ApiOperation("提交展示字段快速导出")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:export')")
    @PostMapping("/display")
    public AjaxResult display(@RequestBody ExportRequest request)
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.submit(request, "display"));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("提交全字段海量导出")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:export') and @ss.hasPermi('manager:bigscreen:exportFull')")
    @PostMapping("/full")
    public AjaxResult full(@RequestBody ExportRequest request)
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.submit(request, "full"));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("查询导出任务状态")
    @GetMapping("/status/{taskId}")
    public AjaxResult status(@PathVariable String taskId)
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.status(taskId));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("失败任务重试/按原参数重新提交")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:export')")
    @PostMapping("/{taskId}/retry")
    public AjaxResult retry(@PathVariable String taskId)
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.retry(taskId, getUserId()));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("断点续传（api 不支持时按原参数重新提交）")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:export')")
    @PostMapping("/{taskId}/resume")
    public AjaxResult resume(@PathVariable String taskId)
    {
        try
        {
            Map<String, Object> result = bigScreenExportService.retry(taskId, getUserId());
            result.put("resume", true);
            result.put("message", "api 不支持字节级续传，已按原参数重新提交任务");
            return AjaxResult.success(result);
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("生成下载签名 URL")
    @PostMapping("/{taskId}/download-url")
    public AjaxResult downloadUrl(@PathVariable String taskId)
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.createDownloadInfo(taskId));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("下载导出文件")
    @GetMapping("/download/{taskId}")
    public void download(@PathVariable String taskId,
                         @RequestHeader(name = BigScreenExportService.DOWNLOAD_TOKEN_HEADER,
                                 required = false) String headerToken,
                         HttpServletResponse response)
    {
        try
        {
            // 令牌只走请求头：query 参数会进入浏览器历史/代理日志/Referer，不再兼容
            bigScreenExportService.download(taskId, headerToken, response);
        }
        catch (ApiClientException e)
        {
            log.warn("[导出下载] code={} msg={}", e.getCode(), e.getMessage());
            if (response.isCommitted())
            {
                return;
            }
            response.setStatus(e.getCode() == ApiErrorCode.FORBIDDEN ? 403 : 404);
            response.setContentType("application/json;charset=UTF-8");
            try
            {
                response.getWriter().write(JSON.toJSONString(AjaxResult.error(e.getMessage())));
            }
            catch (Exception ignored)
            {
                // 响应已不可写，忽略
            }
        }
    }

    // ------------------------------------------------------------------
    // 全字段导出审批（阶段三）
    // ------------------------------------------------------------------

    @ApiOperation("查询待审批导出列表")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:exportApprove')")
    @GetMapping("/approvals")
    public AjaxResult approvals()
    {
        try
        {
            return AjaxResult.success(bigScreenExportService.pendingApprovals());
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("审批通过全字段导出")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:exportApprove')")
    @PostMapping("/approvals/{requestId}/approve")
    public AjaxResult approve(@PathVariable String requestId)
    {
        try
        {
            ExportApprovalRequest approval = bigScreenExportService.findApproval(requestId);
            if (approval == null)
            {
                return AjaxResult.error(404, "审批请求不存在或已过期");
            }
            return AjaxResult.success(bigScreenExportService.approve(requestId, getUserId()));
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    @ApiOperation("驳回全字段导出")
    @PreAuthorize("@ss.hasPermi('manager:bigscreen:exportApprove')")
    @PostMapping("/approvals/{requestId}/reject")
    public AjaxResult reject(@PathVariable String requestId,
                             @RequestParam(name = "reason", required = false) String reason)
    {
        try
        {
            bigScreenExportService.reject(requestId, getUserId(), reason);
            return AjaxResult.success();
        }
        catch (ApiClientException e)
        {
            return error(e);
        }
    }

    private AjaxResult error(ApiClientException e)
    {
        log.warn("[导出] endpoint={} code={} msg={}", e.getEndpoint(), e.getCode(), e.getMessage());
        int code = 500;
        if (e.getCode() == ApiErrorCode.INVALID_ARGUMENT)
        {
            code = 400;
        }
        else if (e.getCode() == ApiErrorCode.NOT_FOUND)
        {
            code = 404;
        }
        else if (e.getCode() == ApiErrorCode.FORBIDDEN)
        {
            code = 403;
        }
        else if (e.getCode() == ApiErrorCode.RATE_LIMITED)
        {
            code = 429;
        }
        else if (e.getCode() == ApiErrorCode.UNAVAILABLE || e.getCode() == ApiErrorCode.CIRCUIT_OPEN
                || e.getCode() == ApiErrorCode.TIMEOUT || e.getCode() == ApiErrorCode.UPSTREAM_ERROR)
        {
            code = 503;
        }
        return AjaxResult.error(code, e.getMessage());
    }
}
