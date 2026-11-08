package com.ruoyi.web.controller.base;

import cn.afterturn.easypoi.excel.ExcelExportUtil;
import cn.afterturn.easypoi.excel.entity.TemplateExportParams;
import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.service.forest.HttpOdsRtSzdnSnapshotFlowAddcodeService;
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
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 门架抓拍流水Controller。
 *
 * <p>阶段一：列表与导出统一走 api（backend 不再查询本地 MySQL 分表）；拆表/路由由 api 负责。</p>
 *
 * @author ruoyi
 */
@RestController
@RequestMapping("/base/snapshotflow")
public class OdsRtSzdnSnapshotFlowAddcodeController extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(OdsRtSzdnSnapshotFlowAddcodeController.class);

    @Resource
    private HttpOdsRtSzdnSnapshotFlowAddcodeService httpOdsRtSzdnSnapshotFlowAddcodeService;

    @Autowired
    private ICarQueryLogService carQueryLogService;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private BigScreenDictService bigScreenDictService;

    /**
     * 查询门架抓拍流水列表
     */
    @PreAuthorize("@ss.hasPermi('base:snapshotflow:list')")
    @GetMapping("/list")
    public TableDataInfo list(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode)
    {
        carQueryLogService.queryLog(JSON.toJSONString(odsRtSzdnSnapshotFlowAddcode), "2", "1");
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageNum())
        {
            odsRtSzdnSnapshotFlowAddcode.setPageNum(1);
        }
        if (null == odsRtSzdnSnapshotFlowAddcode.getPageSize())
        {
            odsRtSzdnSnapshotFlowAddcode.setPageSize(10);
        }
        normalizeSection(odsRtSzdnSnapshotFlowAddcode);

        TableDataInfo rspData = new TableDataInfo();
        List<OdsRtSzdnSnapshotFlowAddcode> list = new ArrayList<OdsRtSzdnSnapshotFlowAddcode>();
        long total = 0L;
        try
        {
            String[] range = TrafficQueryContract.normalizeDateTimeRange(
                    odsRtSzdnSnapshotFlowAddcode.getApplyTime1(),
                    odsRtSzdnSnapshotFlowAddcode.getApplyTime2());
            odsRtSzdnSnapshotFlowAddcode.setApplyTime1(range[0]);
            odsRtSzdnSnapshotFlowAddcode.setApplyTime2(range[1]);
            ApiPageResult<OdsRtSzdnSnapshotFlowAddcode> page = trafficApiClient.snapshotPage(
                    odsRtSzdnSnapshotFlowAddcode);
            list = page.getRows();
            total = page.getTotal();
            rspData.setCode(HttpStatus.SUCCESS);
            rspData.setMsg("查询成功");
        }
        catch (ApiClientException e)
        {
            log.warn("[门架流水] 查询失败 code={} msg={}", e.getCode(), e.getMessage());
            rspData.setCode(statusFor(e));
            rspData.setMsg(errorMessage(e));
        }
        rspData.setRows(list);
        rspData.setTotal(total);
        return rspData;
    }

    /**
     * 导出门架抓拍流水（调用 api 导出接口，不在请求线程内直查业务库）
     */
    @PreAuthorize("@ss.hasPermi('base:snapshotflow:list')")
    @GetMapping("/export")
    public AjaxResult export(OdsRtSzdnSnapshotFlowAddcode odsRtSzdnSnapshotFlowAddcode, HttpServletResponse response)
    {
        carQueryLogService.queryLog(JSON.toJSONString(odsRtSzdnSnapshotFlowAddcode), "2", "2");
        normalizeSection(odsRtSzdnSnapshotFlowAddcode);
        List<OdsRtSzdnSnapshotFlowAddcode> list;
        try
        {
            String[] range = TrafficQueryContract.normalizeDateTimeRange(
                    odsRtSzdnSnapshotFlowAddcode.getApplyTime1(),
                    odsRtSzdnSnapshotFlowAddcode.getApplyTime2());
            odsRtSzdnSnapshotFlowAddcode.setApplyTime1(range[0]);
            odsRtSzdnSnapshotFlowAddcode.setApplyTime2(range[1]);
            list = trafficApiClient.snapshotExport(odsRtSzdnSnapshotFlowAddcode);
        }
        catch (ApiClientException e)
        {
            log.warn("[门架流水] 导出失败 code={} msg={}", e.getCode(), e.getMessage());
            return AjaxResult.error("数据服务暂不可用(" + e.getCode().name() + ")，请稍后重试");
        }

        Map<String, String> directionMap = bigScreenDictService.dictMap("direction");
        for (OdsRtSzdnSnapshotFlowAddcode dp : list)
        {
            if (dp.getDirection() != null)
            {
                dp.setDirectionStr(directionMap.get(dp.getDirection().toString()));
            }
        }

        Map<String, Object> map = new HashMap<String, Object>();
        map.put("entitylist", list);
        try
        {
            String url = "templates/export/snapshotFlow.xlsx";
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
            log.error("[门架流水] 生成 Excel 失败", e);
            return AjaxResult.error("导出文件生成失败");
        }
        return null;
    }

    /**
     * 路段“全部”归一化：去掉末尾逗号，命中 section_all 时置空（由 api 按无路段条件处理）。
     */
    private void normalizeSection(OdsRtSzdnSnapshotFlowAddcode query)
    {
        String sectionCodeStr = CommonUtil.deleteEnd(query.getSectionCodeStr());
        if (CommonUtil.isNotBlank(sectionCodeStr))
        {
            if (sectionCodeStr.indexOf(Constants.section_all) > -1)
            {
                query.setSectionCodeStr("");
            }
        }
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
     * 获取门架抓拍流水详细信息
     */
    @GetMapping(value = "/{bigId}")
    public AjaxResult getInfo(@PathVariable("bigId") String bigId)
    {
        return AjaxResult.success(httpOdsRtSzdnSnapshotFlowAddcodeService.selectOdsRtSzdnSnapshotFlowAddcodeById(bigId));
    }

    /**
     * 查询GaussDB中最早的snapshottime（用于全量同步任务确定起始时间）
     */
    @GetMapping("/earliest-time")
    public AjaxResult getEarliestSnapshottime()
    {
        Date earliestTime = httpOdsRtSzdnSnapshotFlowAddcodeService.getEarliestSnapshottime();
        if (earliestTime != null)
        {
            return AjaxResult.success(earliestTime);
        }
        return AjaxResult.success("暂无数据");
    }
}
