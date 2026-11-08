package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationExit01;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeStationExit01Service;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

/**
 * 收费站出口流水Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/feestationexit")
public class OdsLwzxsfsjFeeStationExit01Controller extends BaseController {

    @Resource
    private HttpOdsLwzxsfsjFeeStationExit01Service httpOdsLwzxsfsjFeeStationExit01Service;

    @Resource
    private TrafficApiClient trafficApiClient;

    /**
     * 查询收费站出口流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feestationexit:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01) {
        // 当前页面
        if (null == odsLwzxsfsjFeeStationExit01.getPageNum()){
            odsLwzxsfsjFeeStationExit01.setPageNum(1);
        }
        // 分页大小
        if (null == odsLwzxsfsjFeeStationExit01.getPageSize()){
            odsLwzxsfsjFeeStationExit01.setPageSize(10);
        }

        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<OdsLwzxsfsjFeeStationExit01> result =
                    trafficApiClient.feeStationExitPage(odsLwzxsfsjFeeStationExit01,
                            pageNum, pageSize, OdsLwzxsfsjFeeStationExit01.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[收费站出口] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }

    /**
     * 导出收费站出口流水列表
     */
//    @PreAuthorize("@ss.hasPermi('base:feestationexit:export')")
//    @Log(title = "收费站出口流水", businessType = BusinessType.EXPORT)
//    @GetMapping("/export")
//    public AjaxResult export(OdsLwzxsfsjFeeStationExit01 odsLwzxsfsjFeeStationExit01) {
//        List<OdsLwzxsfsjFeeStationExit01> list = odsLwzxsfsjFeeStationExit01Service.selectOdsLwzxsfsjFeeStationExit01List(odsLwzxsfsjFeeStationExit01);
//        ExcelUtil<OdsLwzxsfsjFeeStationExit01> util = new ExcelUtil<OdsLwzxsfsjFeeStationExit01>(OdsLwzxsfsjFeeStationExit01.class);
//        return util.exportExcel(list, "收费站出口流水数据");
//    }

    /**
     * 获取收费站出口流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(httpOdsLwzxsfsjFeeStationExit01Service.selectOdsLwzxsfsjFeeStationExit01ById(bigId));
    }
}
