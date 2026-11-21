package com.ruoyi.web.controller.base;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsLwzxsfsjFeeRecords01;
import com.ruoyi.base.service.forest.HttpOdsLwzxsfsjFeeRecords01Service;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;
import com.ruoyi.integration.api.TrafficQueryContract;
import com.ruoyi.manager.domain.vo.bigscreen.SectionVO;
import com.ruoyi.manager.service.ICarQueryLogService;
import com.ruoyi.manager.service.bigscreen.BigScreenDictService;
import org.apache.poi.ss.usermodel.Workbook;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
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
 * 基础-收费流水Controller。
 *
 * <p>阶段一：列表/导出统一走 api；字典与路段映射走两级缓存，避免轮询时重复查库。</p>
 *
 * @author ruoyi
 */
@RestController
@RequestMapping("/base/feerecords")
public class OdsLwzxsfsjFeeRecords01Controller extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(OdsLwzxsfsjFeeRecords01Controller.class);

    @Resource
    private HttpOdsLwzxsfsjFeeRecords01Service odsLwzxsfsjFeeGantryFusion01;

    @Autowired
    private ICarQueryLogService carQueryLogService;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private BigScreenDictService bigScreenDictService;

    /**
     * 查询基础-收费流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01)
    {
        carQueryLogService.queryLog(JSON.toJSONString(odsLwzxsfsjFeeRecords01), "3", "1");
        if (null == odsLwzxsfsjFeeRecords01.getPageNum())
        {
            odsLwzxsfsjFeeRecords01.setPageNum(1);
        }
        if (null == odsLwzxsfsjFeeRecords01.getPageSize())
        {
            odsLwzxsfsjFeeRecords01.setPageSize(10);
        }

        String sectionCodeStr = CommonUtil.deleteEnd(odsLwzxsfsjFeeRecords01.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr))
        {
            if (sectionCodeStr.indexOf(Constants.section_all) > -1)
            {
                odsLwzxsfsjFeeRecords01.setSectionCodeStr("");
            }
        }

        TableDataInfo rspData = new TableDataInfo();
        List<OdsLwzxsfsjFeeRecords01> list = new ArrayList<OdsLwzxsfsjFeeRecords01>();
        long total = 0L;
        try
        {
            String[] range = TrafficQueryContract.normalizeDateTimeRange(
                    odsLwzxsfsjFeeRecords01.getInApplyTime1(),
                    odsLwzxsfsjFeeRecords01.getInApplyTime2());
            odsLwzxsfsjFeeRecords01.setInApplyTime1(range[0]);
            odsLwzxsfsjFeeRecords01.setInApplyTime2(range[1]);

            ApiPageResult<OdsLwzxsfsjFeeRecords01> page = trafficApiClient.feePage(odsLwzxsfsjFeeRecords01);
            list = page.getRows();
            total = page.getTotal();
            enrich(list, false);
            rspData.setCode(HttpStatus.SUCCESS);
            rspData.setMsg("查询成功");
        }
        catch (ApiClientException e)
        {
            log.warn("[收费流水] 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            rspData.setCode(statusFor(e));
            rspData.setMsg(errorMessage(e));
        }
        rspData.setRows(list);
        rspData.setTotal(total);
        return rspData;
    }

    @PreAuthorize("@ss.hasPermi('base:feerecords:list')")
    @GetMapping("/export")
    public AjaxResult export(OdsLwzxsfsjFeeRecords01 odsLwzxsfsjFeeRecords01, HttpServletResponse response)
    {
        carQueryLogService.queryLog(JSON.toJSONString(odsLwzxsfsjFeeRecords01), "3", "2");

        String sectionCodeStr = CommonUtil.deleteEnd(odsLwzxsfsjFeeRecords01.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr))
        {
            if (sectionCodeStr.indexOf(Constants.section_all) > -1)
            {
                odsLwzxsfsjFeeRecords01.setSectionCodeStr("");
            }
        }

        List<OdsLwzxsfsjFeeRecords01> list;
        try
        {
            String[] range = TrafficQueryContract.normalizeDateTimeRange(
                    odsLwzxsfsjFeeRecords01.getInApplyTime1(),
                    odsLwzxsfsjFeeRecords01.getInApplyTime2());
            odsLwzxsfsjFeeRecords01.setInApplyTime1(range[0]);
            odsLwzxsfsjFeeRecords01.setInApplyTime2(range[1]);
            list = trafficApiClient.feeExport(odsLwzxsfsjFeeRecords01);
        }
        catch (ApiClientException e)
        {
            log.warn("[收费流水] 导出失败 code={} msg={}", e.getCode(), e.getMessage());
            return AjaxResult.error("数据服务暂不可用(" + e.getCode().name() + ")，请稍后重试");
        }

        enrich(list, true);

        Map<String, Object> map = new HashMap<String, Object>();
        map.put("entitylist", list);
        try
        {
            String url = "templates/export/feeRecords.xlsx";
            TemplateExportParams params = new TemplateExportParams(url);
            Workbook workbook = ExcelExportUtil.exportExcel(params, map);
            response.setContentType("application/octet-stream;charset=UTF-8");
            response.setHeader("Content-Disposition", "attachment");
            OutputStream outs = response.getOutputStream();
            workbook.write(outs);
            outs.flush();
            outs.close();
        }
        catch (Exception e)
        {
            log.error("[收费流水] 生成 Excel 失败", e);
            return AjaxResult.error("导出文件生成失败");
        }
        return null;
    }

    /**
     * 获取基础-收费流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId)
    {
        return AjaxResult.success(odsLwzxsfsjFeeGantryFusion01.selectOdsLwzxsfsjFeeRecords01ById(bigId));
    }

    private int statusFor(ApiClientException e)
    {
        if (e.getCode() == com.ruoyi.integration.api.ApiErrorCode.INVALID_ARGUMENT)
        {
            return HttpStatus.BAD_REQUEST;
        }
        if (e.getCode() == com.ruoyi.integration.api.ApiErrorCode.UNAVAILABLE
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.CIRCUIT_OPEN
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.TIMEOUT
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.UPSTREAM_ERROR)
        {
            return 503;
        }
        return HttpStatus.ERROR;
    }

    private String errorMessage(ApiClientException e)
    {
        if (e.getCode() == com.ruoyi.integration.api.ApiErrorCode.INVALID_ARGUMENT)
        {
            return "查询条件非法: " + e.getMessage();
        }
        return "数据服务暂不可用(" + e.getCode().name() + ")，请稍后重试";
    }

    /**
     * 名称/状态回填：字典与路段映射均走缓存。
     *
     * @param withPassState 导出时额外回填通行状态
     */
    private void enrich(List<OdsLwzxsfsjFeeRecords01> list, boolean withPassState)
    {
        if (list == null || list.isEmpty())
        {
            return;
        }
        Map<String, SectionVO> sectionMap = bigScreenDictService.sectionMap();
        Map<String, String> plateColorMap = bigScreenDictService.dictMap("plate_color");
        Map<String, String> carTypeMap = bigScreenDictService.dictMap("car_type_old");
        Map<String, String> carVehicleMap = bigScreenDictService.dictMap("car_vehicle_old");
        Map<String, String> passstateMap = withPassState
                ? bigScreenDictService.dictMap("passstate") : new HashMap<String, String>();

        for (OdsLwzxsfsjFeeRecords01 feeRecords : list)
        {
            if (CommonUtil.isNotBlank(feeRecords.getPlateColor()))
            {
                String plateColorValue = CommonUtil.isNull(plateColorMap.get(feeRecords.getPlateColor()));
                if (CommonUtil.isNotBlank(plateColorValue))
                {
                    feeRecords.setVehicleplate(CommonUtil.isNull(feeRecords.getVehicleplate()) + "_" + plateColorValue);
                }
            }
            if (CommonUtil.isNotBlank(feeRecords.getFeevehicletype()))
            {
                feeRecords.setFeevehicletype(CommonUtil.isNull(
                        carTypeMap.get(CommonUtil.isNull(feeRecords.getFeevehicletype()))));
            }
            if (CommonUtil.isNotBlank(feeRecords.getVehicleclass()))
            {
                feeRecords.setVehicleclass(CommonUtil.isNull(
                        carVehicleMap.get(CommonUtil.isNull(feeRecords.getVehicleclass()))));
            }

            BigDecimal fee = feeRecords.getFee();
            if (null != fee && fee.compareTo(BigDecimal.ZERO) > 0)
            {
                feeRecords.setChargeStatus("成功");
            }
            else
            {
                feeRecords.setChargeStatus("失败");
            }
            feeRecords.setFee(null);

            String sectionCodeValue = CommonUtil.isNull(feeRecords.getSectionCodeStr());
            if (CommonUtil.isNotBlank(sectionCodeValue))
            {
                SectionVO sectionBo = sectionMap.get(sectionCodeValue);
                if (sectionBo != null)
                {
                    feeRecords.setSectionName(sectionBo.getSectionName());
                    feeRecords.setRoadname(sectionBo.getRoadName());
                }
            }
            if (withPassState)
            {
                feeRecords.setPassstate(CommonUtil.isNull(passstateMap.get(feeRecords.getPassstate())));
            }
        }
    }
}
