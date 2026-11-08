package com.ruoyi.web.controller.base;

import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiErrorCode;
import com.ruoyi.integration.api.ApiPageResult;

import java.util.ArrayList;

/**
 * 流水接口 api 化后的统一响应/错误映射。
 *
 * <p>api 业务错误在 backend 统一转换为 TableDataInfo 的 code/msg，避免各控制器各写一套。</p>
 *
 * @author car-monit-backend-java-v3
 */
public final class FlowApiSupport
{
    private FlowApiSupport()
    {
    }

    public static TableDataInfo page(ApiPageResult<?> page)
    {
        TableDataInfo rsp = new TableDataInfo();
        rsp.setCode(HttpStatus.SUCCESS);
        rsp.setMsg("查询成功");
        rsp.setRows(page == null || page.getRows() == null ? new ArrayList<Object>() : page.getRows());
        rsp.setTotal(page == null ? 0L : page.getTotal());
        return rsp;
    }

    public static TableDataInfo error(ApiClientException e)
    {
        TableDataInfo rsp = new TableDataInfo();
        rsp.setCode(statusFor(e));
        rsp.setMsg(messageFor(e));
        rsp.setRows(new ArrayList<Object>());
        rsp.setTotal(0L);
        return rsp;
    }

    public static int statusFor(ApiClientException e)
    {
        if (e == null || e.getCode() == null)
        {
            return HttpStatus.ERROR;
        }
        switch (e.getCode())
        {
            case INVALID_ARGUMENT:
                return HttpStatus.BAD_REQUEST;
            case UNAUTHORIZED:
                return HttpStatus.UNAUTHORIZED;
            case FORBIDDEN:
                return HttpStatus.FORBIDDEN;
            case NOT_FOUND:
                return HttpStatus.NOT_FOUND;
            case RATE_LIMITED:
                return 429;
            default:
                return HttpStatus.ERROR;
        }
    }

    public static String messageFor(ApiClientException e)
    {
        if (e == null || e.getCode() == null)
        {
            return "数据服务暂不可用，请稍后重试";
        }
        switch (e.getCode())
        {
            case INVALID_ARGUMENT:
                return "查询参数不合法: " + e.getMessage();
            case UNAUTHORIZED:
            case FORBIDDEN:
                return "数据服务鉴权失败";
            case NOT_FOUND:
                return "数据服务契约未就绪，请稍后重试";
            case RATE_LIMITED:
                return "查询过于频繁，请稍后重试";
            case CIRCUIT_OPEN:
            case TIMEOUT:
            case UNAVAILABLE:
            case UPSTREAM_ERROR:
            default:
                return "数据服务暂不可用(" + e.getCode().name() + ")，请稍后重试";
        }
    }
}
