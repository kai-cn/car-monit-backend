package com.ruoyi.web.controller.base;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeRecords01Service;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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

        TableDataInfo rspData = new TableDataInfo();
        List<OdsLwzxsfsjFeeRecords01> list = new ArrayList<>();
        long total = 0L;

        String vehicleplate = odsLwzxsfsjFeeRecords01.getVehicleplate();
        if(CommonUtil.isNotBlank(vehicleplate)) {
            TableDataInfo tableDataInfo =  odsLwzxsfsjFeeGantryFusion01.getOdsLwzxsfsjFeeRecords01Page(odsLwzxsfsjFeeRecords01);
            if (null != tableDataInfo.getRows() && tableDataInfo.getRows().size() > 0) {
                String trackJosn = JSON.toJSONString(tableDataInfo.getRows());
                list = JSON.parseArray(trackJosn, OdsLwzxsfsjFeeRecords01.class);
                total = tableDataInfo.getTotal();
            }
        }

        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(list);
        rspData.setTotal(total);
        return rspData;

    }


    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/export")
    public AjaxResult export(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01, HttpServletResponse response) {

        // 当前页面
        if (null == odsLwzxsfsjFeeRecords01.getPageNum()){
            odsLwzxsfsjFeeRecords01.setPageNum(1);
        }
        // 分页大小
        if (null == odsLwzxsfsjFeeRecords01.getPageSize()){
            odsLwzxsfsjFeeRecords01.setPageSize(10);
        }

        List<OdsLwzxsfsjFeeRecords01> list = new ArrayList<>();

        String vehicleplate = odsLwzxsfsjFeeRecords01.getVehicleplate();
        if(CommonUtil.isNotBlank(vehicleplate)) {
            list = odsLwzxsfsjFeeGantryFusion01.getOdsLwzxsfsjFeeRecords01ListToExport(odsLwzxsfsjFeeRecords01);
        }

        for (OdsLwzxsfsjFeeRecords01 feeRecords : list) {
            // 时间格式化
            if (null != feeRecords.getReceivetime()) {
                feeRecords.setReceivetimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, feeRecords.getReceivetime()));
                feeRecords.setLastgantrytimeStr(DateUtils.parseDateToStr(DateUtils.YYYY_MM_DD_HH_MM_SS, feeRecords.getLastgantrytime()));
            }
        }
        Map<String, Object> map = new HashMap<>();
        map.put("entitylist", list);
        try {
            String url = "templates/export/feeRecords.xlsx";
            TemplateExportParams params = new TemplateExportParams(url);
            Workbook workbook = ExcelExportUtil.exportExcel(params, map);
            response.setContentType("application/octet-stream;charset=UTF-8");
            response.setHeader("Content-Disposition", "attachment");
            OutputStream outs = response.getOutputStream();
            workbook.write(outs);
            outs.flush();
            outs.close();
        } catch (Exception e) {
            e.printStackTrace();
        }


        return null;
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
