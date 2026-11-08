package com.ruoyi.web.controller.manager.bigscreen;

import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.IncomeStatisticParam;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.bigscreen.BigScreenDictService;
import com.ruoyi.manager.service.bigscreen.BigScreenExceptRecordService;
import com.ruoyi.manager.service.bigscreen.BigScreenLocationService;
import com.ruoyi.manager.service.bigscreen.BigScreenRealtimeService;
import com.ruoyi.manager.service.bigscreen.BigScreenStatsService;
import io.swagger.annotations.ApiOperation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 大屏接口。
 *
 * <p>阶段一改造：统计类指标走预聚合/API + 两级缓存；实时列表走 api；字典/小结果缓存；
 * 异常流水消除 N+1。响应头的 ETag/304、X-Cache、X-Data-Age、X-Degrade 由
 * BigScreenResponseFilter 统一输出。</p>
 *
 * @author car-monit-backend-java-v3
 */
@ApiOperation("大屏接口")
@RestController
@RequestMapping("/manager/bigScreen")
@CrossOrigin(origins = "*")
public class BigScreenController extends BaseController
{
    private static final Logger log = LoggerFactory.getLogger(BigScreenController.class);

    @Autowired
    private BigScreenStatsService bigScreenStatsService;

    @Autowired
    private BigScreenRealtimeService bigScreenRealtimeService;

    @Autowired
    private BigScreenDictService bigScreenDictService;

    @Autowired
    private BigScreenLocationService bigScreenLocationService;

    @Autowired
    private BigScreenExceptRecordService bigScreenExceptRecordService;

    @Autowired
    private ICarExceptRecordService carExceptRecordService;

    /**
     * 重点关注车辆统计
     */
    @GetMapping(value = "/carStatistics")
    public AjaxResult getCarStatistics(IncomeStatisticParam param)
    {
        try
        {
            return AjaxResult.success(bigScreenStatsService.carStatistics(param));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    /**
     * 地图；车辆地图描点
     */
    @GetMapping(value = "/carLocation")
    public AjaxResult getCarLocation(CarLocationParam param)
    {
        normalizeParam(param);
        try
        {
            return AjaxResult.success(bigScreenLocationService.carLocation(param));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    /**
     * 路段列表
     */
    @GetMapping(value = "/sectionList")
    public AjaxResult getSectionList()
    {
        return AjaxResult.success(bigScreenDictService.sectionList());
    }

    /**
     * 收费站门架服务区列表
     */
    @GetMapping(value = "/tollGantryFwqList")
    public AjaxResult getTollList(@RequestParam(name = "sectionCode", required = false) String sectionCode,
                                  @RequestParam String type)
    {
        return AjaxResult.success(bigScreenDictService.tollGantryFwqList(sectionCode, type));
    }

    /**
     * 重点车辆库统计
     */
    @GetMapping(value = "/carVoList")
    public AjaxResult carVoList()
    {
        return AjaxResult.success(bigScreenRealtimeService.carVoList());
    }

    /**
     * 追缴统计
     */
    @GetMapping(value = "/carAudit")
    public AjaxResult getCarAudit(IncomeStatisticParam param)
    {
        try
        {
            return AjaxResult.success(bigScreenStatsService.carAudit(param));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    /**
     * 车辆预警
     */
    @GetMapping(value = "/carWarning")
    public AjaxResult getCarWarning(CarLocationParam param)
    {
        normalizeParam(param);
        try
        {
            return AjaxResult.success(bigScreenRealtimeService.carWarning(param));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    /**
     * 异常数据
     */
    @GetMapping(value = "/exceptionCar")
    public AjaxResult getExceptionCar()
    {
        return AjaxResult.success(bigScreenRealtimeService.exceptionCar());
    }

    /**
     * 重点车辆通行前10（按时间范围，默认最近 7 天）
     */
    @ApiOperation("重点车辆通行前10")
    @GetMapping(value = "/topTen")
    public AjaxResult topTen(@RequestParam(name = "startTime", required = false) String startTime,
                             @RequestParam(name = "endTime", required = false) String endTime)
    {
        try
        {
            return AjaxResult.success(bigScreenStatsService.topTen(startTime, endTime));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    @ApiOperation("机构列表")
    @GetMapping(value = "/orgList")
    public AjaxResult getOrgList()
    {
        return AjaxResult.success(bigScreenDictService.orgList());
    }

    /**
     * 堵漏增收统计
     */
    @ApiOperation("堵漏增收统计")
    @GetMapping(value = "/incomeStatistic")
    public AjaxResult incomeStatistic(IncomeStatisticParam param)
    {
        try
        {
            return AjaxResult.success(bigScreenStatsService.incomeStatistic(param));
        }
        catch (ApiClientException e)
        {
            return apiError(e);
        }
    }

    /**
     * 异常流水分页（批量补全 orgId / 补缴状态，消除 N+1）
     */
    @GetMapping("/exceptRecordList")
    public TableDataInfo list(CarExceptRecord carExceptRecord)
    {
        startPage();
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        TableDataInfo dataTable = getDataTable(list);
        List<CarExceptRecord> rows = (List<CarExceptRecord>) dataTable.getRows();
        bigScreenExceptRecordService.enrich(rows);
        return dataTable;
    }

    /**
     * 复用原有参数归一化逻辑：路段“全部”、type/code → 具体维度编码。
     */
    private void normalizeParam(CarLocationParam param)
    {
        String type = param.getType();
        String sectionCode = CommonUtil.isNull(param.getSectionCode());
        if (sectionCode.indexOf(Constants.section_all) > -1)
        {
            param.setSectionCode("");
        }
        String code = CommonUtil.isNull(param.getCode());
        if (CommonUtil.isNotBlank(type))
        {
            // 1收费站、2门架、3服务区
            if ("1".equals(type))
            {
                if (CommonUtil.isNotBlank(code))
                {
                    param.setTollCode(code);
                }
                else
                {
                    param.setTollCode(Constants.STATION_CAPTURE);
                }
            }
            else if ("2".equals(type))
            {
                if (CommonUtil.isNotBlank(code))
                {
                    param.setGantryCode(code);
                }
                else
                {
                    param.setGantryCode(Constants.GANTRY_CAPTURE);
                }
            }
            else if ("3".equals(type))
            {
                if (CommonUtil.isNotBlank(code))
                {
                    param.setFwqbm(code);
                }
                else
                {
                    param.setFwqbm(Constants.SERVICE_AREA_CAPTURE);
                }
            }
        }
    }

    private AjaxResult apiError(ApiClientException e)
    {
        log.warn("[大屏] api 调用失败 endpoint={} code={} msg={}", e.getEndpoint(), e.getCode(), e.getMessage());
        int code = 500;
        if (e.getCode() == com.ruoyi.integration.api.ApiErrorCode.INVALID_ARGUMENT)
        {
            code = 400;
        }
        else if (e.getCode() == com.ruoyi.integration.api.ApiErrorCode.CIRCUIT_OPEN
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.UNAVAILABLE
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.TIMEOUT
                || e.getCode() == com.ruoyi.integration.api.ApiErrorCode.UPSTREAM_ERROR)
        {
            code = 503;
        }
        String message = e.getCode().name() + ": 数据服务暂不可用，请稍后重试";
        if (code == 400)
        {
            message = "查询条件非法: " + e.getMessage();
        }
        return AjaxResult.error(code, message);
    }
}
