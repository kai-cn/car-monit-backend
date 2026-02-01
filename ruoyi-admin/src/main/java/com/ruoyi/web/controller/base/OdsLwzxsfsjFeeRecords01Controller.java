package com.ruoyi.web.controller.base;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeRecords01Service;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.service.ICarQueryLogService;
import com.ruoyi.system.service.ISysDictDataService;
import org.apache.poi.ss.usermodel.Workbook;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletResponse;
import java.io.OutputStream;
import java.math.BigDecimal;
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
    @Resource
    private RedisCache redisCache;
    @Autowired
    private ISysDictDataService sysDictDataService;

    @Autowired
    private ICarQueryLogService carQueryLogService;

    /**
     * 查询基础-收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01) {
        // 插入查询日志
        carQueryLogService.queryLog(JSON.toJSONString(odsLwzxsfsjFeeRecords01), "3", "1");
        // 当前页面
        if (null == odsLwzxsfsjFeeRecords01.getPageNum()){
            odsLwzxsfsjFeeRecords01.setPageNum(1);
        }
        // 分页大小
        if (null == odsLwzxsfsjFeeRecords01.getPageSize()){
            odsLwzxsfsjFeeRecords01.setPageSize(10);
        }

        //  路段
        String sectionCodeStr = CommonUtil.deleteEnd(odsLwzxsfsjFeeRecords01.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr)){
            if (sectionCodeStr.indexOf(Constants.section_all) > -1) {
                odsLwzxsfsjFeeRecords01.setSectionCodeStr("");
            }
        }

        TableDataInfo rspData = new TableDataInfo();
        List<OdsLwzxsfsjFeeRecords01> list = new ArrayList<>();
        long total = 0L;

        // 时间段必填
        if(CommonUtil.isNotBlank(odsLwzxsfsjFeeRecords01.getInApplyTime1()) && CommonUtil.isNotBlank(odsLwzxsfsjFeeRecords01.getInApplyTime2())){
            TableDataInfo tableDataInfo =  odsLwzxsfsjFeeGantryFusion01.getOdsLwzxsfsjFeeRecords01Page(odsLwzxsfsjFeeRecords01);
            if (null != tableDataInfo.getRows() && tableDataInfo.getRows().size() > 0) {
                String trackJosn = JSON.toJSONString(tableDataInfo.getRows());
                list = JSON.parseArray(trackJosn, OdsLwzxsfsjFeeRecords01.class);
                if (null != list && list.size() > 0) {
                    List<OdsSzdnSection> sectionList = redisCache.getCacheList(Constants.SECTION_LIST);
                    Map<String, OdsSzdnSection> sectionMap = new HashMap<>();
                    if (null !=sectionList && sectionList.size() > 0){
                        for (OdsSzdnSection section:sectionList){
                            sectionMap.put(CommonUtil.isNull(section.getSectionCode()),section);
                        }
                    }

                    // 车牌颜色
                    Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");

                    // 车型
                    Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type_old");

                    // 车种
                    Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle_old");


                    for (OdsLwzxsfsjFeeRecords01 feeRecords : list) {
                        if (CommonUtil.isNotBlank(feeRecords.getPlateColor())) {
                            String plateColorVaule = CommonUtil.isNull(plateColorMap.get(feeRecords.getPlateColor()));
                            if (CommonUtil.isNotBlank(plateColorVaule)) {
                                feeRecords.setVehicleplate(CommonUtil.isNull(feeRecords.getVehicleplate()) + "_" + plateColorVaule);
                            }
                        }

                        if (CommonUtil.isNotBlank(feeRecords.getFeevehicletype())) {
                            feeRecords.setFeevehicletype(CommonUtil.isNull(carTypeMap.get(CommonUtil.isNull(feeRecords.getFeevehicletype()))));
                        }

                        if (CommonUtil.isNotBlank(feeRecords.getVehicleclass())) {
                            feeRecords.setVehicleclass(CommonUtil.isNull(carVehicleMap.get(CommonUtil.isNull(feeRecords.getVehicleclass()))));
                        }



                        BigDecimal fee = feeRecords.getFee();
                        if (null != fee && fee.compareTo(BigDecimal.ZERO) > 0) {
                            feeRecords.setChargeStatus("成功");
                        }else {
                            feeRecords.setChargeStatus("失败");
                        }
                        feeRecords.setFee(null);

                        String sectionCode = CommonUtil.isNull(feeRecords.getSectionCodeStr());
                        if(CommonUtil.isNotBlank(sectionCode)){
                            if (sectionMap.containsKey(sectionCode)){
                                OdsSzdnSection sectionBo = sectionMap.get(sectionCode);
                                feeRecords.setSectionName(sectionBo.getSectionName());
                                feeRecords.setRoadname(sectionBo.getRoadName());
                            }
                        }
                    }
                }

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
        // 插入查询日志
        carQueryLogService.queryLog(JSON.toJSONString(odsLwzxsfsjFeeRecords01), "3", "2");
        // 当前页面
        if (null == odsLwzxsfsjFeeRecords01.getPageNum()){
            odsLwzxsfsjFeeRecords01.setPageNum(1);
        }
        // 分页大小
        if (null == odsLwzxsfsjFeeRecords01.getPageSize()){
            odsLwzxsfsjFeeRecords01.setPageSize(10);
        }

        //  路段
        String sectionCodeStr = CommonUtil.deleteEnd(odsLwzxsfsjFeeRecords01.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr)){
            if (sectionCodeStr.indexOf(Constants.section_all) > -1) {
                odsLwzxsfsjFeeRecords01.setSectionCodeStr("");
            }
        }

        List<OdsLwzxsfsjFeeRecords01> list = new ArrayList<>();

        // 时间段必填
        if(CommonUtil.isNotBlank(odsLwzxsfsjFeeRecords01.getInApplyTime1()) && CommonUtil.isNotBlank(odsLwzxsfsjFeeRecords01.getInApplyTime2())){
            list = odsLwzxsfsjFeeGantryFusion01.getOdsLwzxsfsjFeeRecords01ListToExport(odsLwzxsfsjFeeRecords01);
        }

        if (null != list && list.size() > 0) {

            // 车牌颜色
            Map<String,String> plateColorMap = sysDictDataService.selectDictDataMap("plate_color");

            // 车型
            Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type_old");

            // 车种
            Map<String,String> carVehicleMap = sysDictDataService.selectDictDataMap("car_vehicle_old");


            // 通行状态
            Map<String,String> passstateMap = sysDictDataService.selectDictDataMap("passstate");

            List<OdsSzdnSection> sectionList = redisCache.getCacheList(Constants.SECTION_LIST);
            Map<String, OdsSzdnSection> sectionMap = new HashMap<>();
            if (null !=sectionList && sectionList.size() > 0){
                for (OdsSzdnSection section:sectionList){
                    sectionMap.put(CommonUtil.isNull(section.getSectionCode()),section);
                }
            }
            for (OdsLwzxsfsjFeeRecords01 feeRecords : list) {

                if (CommonUtil.isNotBlank(feeRecords.getPlateColor())) {
                    String plateColorVaule = CommonUtil.isNull(plateColorMap.get(feeRecords.getPlateColor()));
                    if (CommonUtil.isNotBlank(plateColorVaule)) {
                        feeRecords.setVehicleplate(CommonUtil.isNull(feeRecords.getVehicleplate()) + "_" + plateColorVaule);
                    }
                }

                if (CommonUtil.isNotBlank(feeRecords.getFeevehicletype())) {
                    feeRecords.setFeevehicletype(CommonUtil.isNull(carTypeMap.get(CommonUtil.isNull(feeRecords.getFeevehicletype()))));
                }

                if (CommonUtil.isNotBlank(feeRecords.getVehicleclass())) {
                    feeRecords.setVehicleclass(CommonUtil.isNull(carVehicleMap.get(CommonUtil.isNull(feeRecords.getVehicleclass()))));
                }

                BigDecimal fee = feeRecords.getFee();
                if (null != fee && fee.compareTo(BigDecimal.ZERO) > 0) {
                    feeRecords.setChargeStatus("成功");
                }else {
                    feeRecords.setChargeStatus("失败");
                }
                feeRecords.setFee(null);

                String sectionCode = CommonUtil.isNull(feeRecords.getSectionCodeStr());
                if(CommonUtil.isNotBlank(sectionCode)){
                    if (sectionMap.containsKey(sectionCode)){
                        OdsSzdnSection sectionBo = sectionMap.get(sectionCode);
                        feeRecords.setSectionName(sectionBo.getSectionName());
                        feeRecords.setRoadname(sectionBo.getRoadName());
                    }
                }
                feeRecords.setPassstate(CommonUtil.isNull(passstateMap.get(feeRecords.getPassstate())));
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
