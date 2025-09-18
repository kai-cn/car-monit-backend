package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsSzdnTollStationIp;
import com.ruoyi.base.service.IOdsSzdnTollStationIpService;
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
 * 收费站ipController
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/tollStationIp")
public class OdsSzdnTollStationIpController extends BaseController {

    @Autowired
    private IOdsSzdnTollStationIpService odsSzdnTollStationIpService;

    /**
     * 查询收费站ip列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsSzdnTollStationIp odsSzdnTollStationIp) {
        startPage();
        // odsSzdnTollStationIp.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsSzdnTollStationIp> list = odsSzdnTollStationIpService.selectOdsSzdnTollStationIpList(odsSzdnTollStationIp);
        return getDataTable(list);
    }


    /**
     * 获取收费站ip详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id) {
        return AjaxResult.success(odsSzdnTollStationIpService.selectOdsSzdnTollStationIpById(id));
    }


}
