package com.ruoyi.web.controller.base;

import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.base.domain.OdsCxztFwqclls;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;

/**
 * 服务区车辆流水Controller
 *
 * @author ruoyi
 * @date 2025-10-20
 */
@RestController
@RequestMapping("/manager/fwqclls")
public class OdsCxztFwqcllsController extends BaseController {

    @Autowired
    private TrafficApiClient trafficApiClient;

    /**
     * 查询服务区车辆流水列表（统一走 api，不在请求线程直查分表）
     */
    @PreAuthorize("@ss.hasPermi('manager:fwqclls:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsCxztFwqclls odsCxztFwqclls) {
        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<OdsCxztFwqclls> result =
                    trafficApiClient.serviceAreaFlowPage(odsCxztFwqclls,
                            pageNum, pageSize, OdsCxztFwqclls.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[服务区流水] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }

    /**
     * 获取服务区车辆流水详细信息（api 按主键查询；api 不可用返回明确错误）
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        try {
            return AjaxResult.success(trafficApiClient.flowDetail("/manager/fwqclls",
                    String.valueOf(bigId), OdsCxztFwqclls.class));
        } catch (ApiClientException e) {
            logger.warn("[服务区流水] 详情 api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return AjaxResult.error(FlowApiSupport.statusFor(e), FlowApiSupport.messageFor(e));
        }
    }


}
