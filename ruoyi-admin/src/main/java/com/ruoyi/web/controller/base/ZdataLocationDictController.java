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
import com.ruoyi.base.domain.ZdataLocationDict;
import com.ruoyi.base.service.IZdataLocationDictService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 车辆位置Controller
 *
 * @author ruoyi
 * @date 2025-10-15
 */
@RestController
@RequestMapping("/base/location")
public class ZdataLocationDictController extends BaseController {

    @Autowired
    private IZdataLocationDictService zdataLocationDictService;

    /**
     * 查询车辆位置列表
     */
    @PreAuthorize("@ss.hasPermi('base:location:list')")
    @GetMapping("/list")
    public TableDataInfo list(ZdataLocationDict zdataLocationDict) {
        startPage();
        // zdataLocationDict.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<ZdataLocationDict> list = zdataLocationDictService.selectZdataLocationDictList(zdataLocationDict);
        return getDataTable(list);
    }


    /**
     * 获取车辆位置详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(zdataLocationDictService.selectZdataLocationDictById(id));
    }


}
