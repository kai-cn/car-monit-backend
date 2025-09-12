package com.ruoyi.web.controller.manager;

import java.util.Arrays;
import java.util.List;

import com.ruoyi.common.utils.CommonUtil;
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
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.service.ICarTrackInfoService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 车辆行驶轨迹Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/cartrackinfo")
public class CarTrackInfoController extends BaseController {

    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    /**
     * 查询车辆行驶轨迹列表
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarTrackInfo carTrackInfo) {
        startPage();
        // carTrackInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        return getDataTable(list);
    }

    /**
     * 通根据车牌号查询
     *
     * @param carTrackInfo
     * @return
     */
    @GetMapping("/listByCarId")
    public AjaxResult listByCarId(CarTrackInfo carTrackInfo) {
        if (CommonUtil.isBlank(carTrackInfo.getCarNo())) {
            carTrackInfo.setCarNo("-1");
        }
        List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        return AjaxResult.success(list);
    }


    /**
     * 导出车辆行驶轨迹列表
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:export')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarTrackInfo carTrackInfo) {
        List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        ExcelUtil<CarTrackInfo> util = new ExcelUtil<CarTrackInfo>(CarTrackInfo.class);
        return util.exportExcel(list, "车辆行驶轨迹数据");
    }

    /**
     * 获取车辆行驶轨迹详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carTrackInfoService.selectCarTrackInfoById(id));
    }

    /**
     * 新增车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:add')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarTrackInfo carTrackInfo) {
        return carTrackInfoService.saveCarTrackInfo(carTrackInfo);
    }

    /**
     * 修改车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:edit')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarTrackInfo carTrackInfo) {
        return carTrackInfoService.saveCarTrackInfo(carTrackInfo);
    }

    /**
     * 删除车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:remove')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carTrackInfoService.deleteCarTrackInfoByIds(ids);
    }

}
