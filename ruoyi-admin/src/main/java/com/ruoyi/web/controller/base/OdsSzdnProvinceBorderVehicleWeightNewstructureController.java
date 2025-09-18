package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsSzdnProvinceBorderVehicleWeightNewstructure;
import com.ruoyi.base.service.IOdsSzdnProvinceBorderVehicleWeightNewstructureService;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
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

    /**
     * 查询省界称重列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnProvinceBorderVehicleWeightNewstructure odsSzdnProvinceBorderVehicleWeightNewstructure) {
        startPage();
        // odsSzdnProvinceBorderVehicleWeightNewstructure.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnProvinceBorderVehicleWeightNewstructure> list = odsSzdnProvinceBorderVehicleWeightNewstructureService.selectOdsSzdnProvinceBorderVehicleWeightNewstructureList(odsSzdnProvinceBorderVehicleWeightNewstructure);
        return getDataTable(list);
    }


    /**
     * 获取省界称重详细信息
     */
    @GetMapping(value = "/{dataSource}")
    public AjaxResult getInfo(@PathVariable("dataSource") String dataSource) {
        return AjaxResult.success(odsSzdnProvinceBorderVehicleWeightNewstructureService.selectOdsSzdnProvinceBorderVehicleWeightNewstructureById(dataSource));
    }



}
