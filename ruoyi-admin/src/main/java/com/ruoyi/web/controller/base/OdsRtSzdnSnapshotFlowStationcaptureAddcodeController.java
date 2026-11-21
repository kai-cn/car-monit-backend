package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowStationcaptureAddcode;
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
 * 收费站抓拍Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/stationcapture")
public class OdsRtSzdnSnapshotFlowStationcaptureAddcodeController extends BaseController {

    @Autowired
    private TrafficApiClient trafficApiClient;

    /**
     * 查询收费站抓拍列表（统一走 api，不在请求线程直查分表）
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowStationcaptureAddcode odsRtSzdnSnapshotFlowStationcaptureAddcode) {
        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<OdsRtSzdnSnapshotFlowStationcaptureAddcode> result =
                    trafficApiClient.stationcapturePage(odsRtSzdnSnapshotFlowStationcaptureAddcode,
                            pageNum, pageSize, OdsRtSzdnSnapshotFlowStationcaptureAddcode.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[收费站抓拍] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }


    /**
     * 获取收费站抓拍详细信息（api 按主键查询；api 不可用返回明确错误）
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        try {
            return AjaxResult.success(trafficApiClient.flowDetail("/base/stationcapture",
                    String.valueOf(bigId), OdsRtSzdnSnapshotFlowStationcaptureAddcode.class));
        } catch (ApiClientException e) {
            logger.warn("[收费站抓拍] 详情 api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return AjaxResult.error(FlowApiSupport.statusFor(e), FlowApiSupport.messageFor(e));
        }
    }


}
