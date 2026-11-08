package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationEnter01;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 收费站入口数据Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/feeStationEnter")
public class OdsLwzxsfsjFeeStationEnter01Controller extends BaseController {

    @Autowired
    private TrafficApiClient trafficApiClient;

    /**
     * 查询收费站入口数据列表（统一走 api，不在请求线程直查分表）
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeStationEnter01 odsLwzxsfsjFeeStationEnter01) {
        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<OdsLwzxsfsjFeeStationEnter01> result =
                    trafficApiClient.feeStationEnterPage(odsLwzxsfsjFeeStationEnter01,
                            pageNum, pageSize, OdsLwzxsfsjFeeStationEnter01.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[收费站入口] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }


    /**
     * 获取收费站入口数据详细信息（api 按主键查询；api 不可用返回明确错误）
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        try {
            return AjaxResult.success(trafficApiClient.flowDetail("/base/feeStationEnter",
                    String.valueOf(bigId), OdsLwzxsfsjFeeStationEnter01.class));
        } catch (ApiClientException e) {
            logger.warn("[收费站入口] 详情 api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return AjaxResult.error(FlowApiSupport.statusFor(e), FlowApiSupport.messageFor(e));
        }
    }



}
