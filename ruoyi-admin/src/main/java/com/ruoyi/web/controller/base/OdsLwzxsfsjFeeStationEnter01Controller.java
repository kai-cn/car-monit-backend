package com.ruoyi.web.controller.base;

import com.ruoyi.base.domain.OdsLwzxsfsjFeeStationEnter01;
import com.ruoyi.base.service.IOdsLwzxsfsjFeeStationEnter01Service;
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
 * 收费站入口数据Controller
 *
 * @author ruoyi
 * @date 2025-09-18
 */
@RestController
@RequestMapping("/base/feeStationEnter")
public class OdsLwzxsfsjFeeStationEnter01Controller extends BaseController {

    @Autowired
    private IOdsLwzxsfsjFeeStationEnter01Service odsLwzxsfsjFeeStationEnter01Service;

    /**
     * 查询收费站入口数据列表
     */
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeStationEnter01 odsLwzxsfsjFeeStationEnter01) {
        startPage();
        // odsLwzxsfsjFeeStationEnter01.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<OdsLwzxsfsjFeeStationEnter01> list = odsLwzxsfsjFeeStationEnter01Service.selectOdsLwzxsfsjFeeStationEnter01List(odsLwzxsfsjFeeStationEnter01);
        return getDataTable(list);
    }


    /**
     * 获取收费站入口数据详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") Long bigId) {
        return AjaxResult.success(odsLwzxsfsjFeeStationEnter01Service.selectOdsLwzxsfsjFeeStationEnter01ById(bigId));
    }



}
