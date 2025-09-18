package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsSzdnGantryIp;
import com.ruoyi.base.service.IOdsSzdnGantryIpService;
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
 * 省界设备ipController
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/gantryIp")
public class OdsSzdnGantryIpController extends BaseController {

    @Autowired
    private IOdsSzdnGantryIpService odsSzdnGantryIpService;

    /**
     * 查询省界设备ip列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnGantryIp odsSzdnGantryIp) {
        startPage();
        // odsSzdnGantryIp.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnGantryIp> list = odsSzdnGantryIpService.selectOdsSzdnGantryIpList(odsSzdnGantryIp);
        return getDataTable(list);
    }


    /**
     * 获取省界设备ip详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(odsSzdnGantryIpService.selectOdsSzdnGantryIpById(id));
    }


}
