package com.ruoyi.web.controller.base;

import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeRecords01Service;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.exception.ServiceException;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;

/**
 * 基础-收费流水Controller
 *
 * @author ruoyi
 * @date 2025-08-29
 */
@RestController
@RequestMapping("/base/feerecords")
public class OdsLwzxsfsjFeeRecords01Controller extends BaseController {

    @Resource
    private HttpOdsLwzxsfsjFeeRecords01Service odsLwzxsfsjFeeGantryFusion01;

    /**
     * 查询基础-收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01) {
        // 当前页面
        if (null == odsLwzxsfsjFeeRecords01.getPageNum()){
            odsLwzxsfsjFeeRecords01.setPageNum(1);
        }
        // 分页大小
        if (null == odsLwzxsfsjFeeRecords01.getPageSize()){
            odsLwzxsfsjFeeRecords01.setPageSize(10);
        }

        return odsLwzxsfsjFeeGantryFusion01.getOdsLwzxsfsjFeeRecords01Page(odsLwzxsfsjFeeRecords01);
    }

    /**
     * 导出基础-收费流水列表
     */
//    @PreAuthorize("@ss.hasPermi('base:feerecords:export')")
//    @Log(title = "基础-收费流水", businessType = BusinessType.EXPORT)
//    @GetMapping("/export")
//    public AjaxResult export(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01) {
//        List<OdsLwzxsfsjFeeRecords01> list = odsLwzxsfsjFeeRecords01Service.selectOdsLwzxsfsjFeeRecords01List(odsLwzxsfsjFeeRecords01);
//        ExcelUtil<OdsLwzxsfsjFeeRecords01> util = new ExcelUtil<OdsLwzxsfsjFeeRecords01>(OdsLwzxsfsjFeeRecords01.class);
//        return util.exportExcel(list, "基础-收费流水数据");
//    }

    /**
     * 获取基础-收费流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId) {
        return AjaxResult.success(odsLwzxsfsjFeeGantryFusion01.selectOdsLwzxsfsjFeeRecords01ById(bigId));
    }
}
