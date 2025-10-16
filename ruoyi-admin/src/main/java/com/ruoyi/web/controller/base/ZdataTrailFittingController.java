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
import com.ruoyi.common.core.page.TableDataInfo;

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

    /**
     * 查询车辆出入口拟合轨迹列表
     */
    @PreAuthorize("@ss.hasPermi('base:fitting:list')")
    @GetMapping("/list")
    public TableDataInfo list(ZdataTrailFitting zdataTrailFitting) {
        startPage();
        // zdataTrailFitting.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<ZdataTrailFitting> list = zdataTrailFittingService.selectZdataTrailFittingList(zdataTrailFitting);
        return getDataTable(list);
    }



    /**
     * 获取车辆出入口拟合轨迹详细信息
     */
    @GetMapping(value = "/{cid}")
    public AjaxResult getInfo(@PathVariable("cid") String cid) {
        return AjaxResult.success(zdataTrailFittingService.selectZdataTrailFittingById(cid));
    }


}
