package com.ruoyi.web.controller.base;

import java.util.Arrays;
import java.util.List;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.base.domain.ZdataTrailFitting;
import com.ruoyi.base.service.IZdataTrailFittingService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;

/**
 * 车辆出入口拟合轨迹Controller
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@RestController
@RequestMapping("/base/fitting")
public class ZdataTrailFittingController extends BaseController {

    @Autowired
    private IZdataTrailFittingService zdataTrailFittingService;

    @Autowired
    private TrafficApiClient trafficApiClient;

    /**
     * 查询车辆出入口拟合轨迹列表（统一走 api，不在请求线程直查分表）
     */
    @GetMapping("/list")
    public TableDataInfo list(ZdataTrailFitting zdataTrailFitting) {
        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();
        try {
            ApiPageResult<ZdataTrailFitting> result =
                    trafficApiClient.trailFittingPage(zdataTrailFitting,
                            pageNum, pageSize, ZdataTrailFitting.class);
            return FlowApiSupport.page(result);
        } catch (ApiClientException e) {
            logger.warn("[拟合轨迹] api 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            return FlowApiSupport.error(e);
        }
    }



    /**
     * 获取车辆出入口拟合轨迹详细信息
     */
    @GetMapping(value = "/{cid}")
    public AjaxResult getInfo(@PathVariable("cid") String cid) {
        return AjaxResult.success(zdataTrailFittingService.selectZdataTrailFittingById(cid));
    }


}
