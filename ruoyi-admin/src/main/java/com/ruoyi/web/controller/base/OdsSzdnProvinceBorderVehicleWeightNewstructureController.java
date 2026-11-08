package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure;
import com.ruoyi.base.service.IOdsSzdnProvinceBorderVehicleWeightNewstructureService;
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
 * 省界称重Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/vehicleweight")
public class OdsSzdnProvinceBorderVehicleWeightNewstructureController extends BaseController {

    @Autowired
    private IOdsSzdnProvinceBorderVehicleWeightNewstructureService odsSzdnProvinceBorderVehicleWeightNewstructureService;

    @Autowired
    private TrafficApiClient trafficApiClient;

    /**
     * 查询省界称重列表（统一走 api，不在请求线程直查分表）
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnProvinceBorderVehicleWeightNewstructure odsSzdnProvinceBorderVehicleWeightNewstructure) {
        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<OdsSzdnProvinceBorderVehicleWeightNewstructure> result =
                    trafficApiClient.vehicleWeightPage(odsSzdnProvinceBorderVehicleWeightNewstructure,
                            pageNum, pageSize, OdsSzdnProvinceBorderVehicleWeightNewstructure.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[省界称重] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }


    /**
     * 获取省界称重详细信息
     */
    @GetMapping(value = "/{dataSource}")
    public AjaxResult getInfo(@PathVariable("dataSource") String dataSource) {
        return AjaxResult.success(odsSzdnProvinceBorderVehicleWeightNewstructureService.selectOdsSzdnProvinceBorderVehicleWeightNewstructureById(dataSource));
    }



}
