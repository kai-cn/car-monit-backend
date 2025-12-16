package com.ruoyi.web.controller.manager.bigscreen;

import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.*;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.*;
import com.ruoyi.manager.domain.vo.bigscreen.*;
import com.ruoyi.manager.service.*;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;



@ApiOperation("大屏接口")
@RestController
@RequestMapping("/manager/bigScreen")
@CrossOrigin(origins = "*")
public class BigScreenController extends BaseController {

    @Autowired
    private ICarConfimFreeService carConfimFreeService;
    @Autowired
    private ICarAduitFreeService carAduitFreeService;
    @Autowired
    private ICarInfoService carInfoService;
    @Autowired
    private IOdsSzdnSectionService odsSzdnSectionService;
    @Autowired
    private IOdsSzdnTollService tollService;
    @Autowired
    private ICarWarningInfoService carWarningInfoService;
    @Autowired
    private IOdsSzdnGantryService gantryService;
    @Autowired
    private IDwdLcztFwqjcxxService fwqjcxxService;
    @Autowired
    private IOdsRtSzdnSnapshotFlowAddcodeService snapshotFlowAddcodeService;
    @Autowired
    private ICarSuspiciousService carSuspiciousService;
    @Autowired
    private IOdsYhglVBaseOrgService baseOrgService;
    @Autowired
    private ICarExceptRecordService carExceptRecordService;


    /**
     *  重点关注车辆统计
     */
    @GetMapping(value = "/carStatistics")
    public AjaxResult getCarStatistics(IncomeStatisticParam param) {
        List<CarStatisticsVO> carStatisticsVO = carConfimFreeService.getCarStatistics(param);
        return AjaxResult.success(carStatisticsVO);
    }

    /**
     * 地图 ；车俩地图描点
     */
    @GetMapping(value = "/carLocation")
    public AjaxResult getCarLocation(CarLocationParam param) {
        String type = param.getType();
        if(StringUtils.isNotBlank(type)) {
            switch (type) {
                case "1":
                    param.setTollCode(param.getCode());
                    break;
                case "2":
                    param.setGantryCode(param.getCode());
                    break;
                case "3":
                    param.setFwqbm(param.getCode());
                    break;
            }
        }
        List<CarLocationVO> carLocationVOList = carInfoService.carLocation(param);
        return AjaxResult.success(carLocationVOList);
    }

    /**
     * 路段列表
     * @return
     */
    @GetMapping(value = "/sectionList")
    public AjaxResult getSectionList() {
        List<SectionVO> collect = odsSzdnSectionService.selectOdsSzdnSectionListNew(new OdsSzdnSection())
                .stream().map(item -> {
                    SectionVO sectionVO = new SectionVO();
                    sectionVO.setSectionCode(item.getSectionCode());
                    sectionVO.setSectionName(item.getSectionName());
                    return sectionVO;
                }).collect(Collectors.toList());

        // 需要增加全部
        List<SectionVO> collectNew = new ArrayList<>();
        SectionVO sectionAll = new SectionVO();
        sectionAll.setSectionCode("all");
        sectionAll.setSectionName("全部");
        collectNew.add(sectionAll);

        for (SectionVO rtn:collect){
            collectNew.add(rtn);
        }


        return AjaxResult.success(collectNew);
    }

    /**
     * 收费站门架服务区列表
     * @param sectionCode
     * @param type
     * @return
     */
    @GetMapping(value = "/tollGantryFwqList")
    public AjaxResult getTollList(@RequestParam(name = "sectionCode", required = false) String sectionCode, @RequestParam String type) {
        if(CommonUtil.isBlank(sectionCode)) {
            return AjaxResult.success(new ArrayList<>());
        }
        sectionCode = CommonUtil.deleteEnd(sectionCode);

        String[] split = sectionCode.split(",");
        List<String> sectionCodeList = Arrays.stream(split).collect(Collectors.toList());
        if (sectionCode.indexOf("all") > -1){
            sectionCodeList = new ArrayList<>();
        }

        List<TollGantryFwqVO> collect = new ArrayList<>();
        if ("1".equals(type)) {
            OdsSzdnToll odsSzdnToll = new OdsSzdnToll();
            odsSzdnToll.setSectionCodeList(sectionCodeList);
            collect = tollService.selectOdsSzdnTollListNew(odsSzdnToll)
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("1");
                        vo.setCode(item.getTollCode());
                        vo.setName(item.getTollName());
                        return vo;
                    }).collect(Collectors.toList());
        } else if ("2".equals(type)) {
            OdsSzdnGantry odsSzdnGantry = new OdsSzdnGantry();
            odsSzdnGantry.setSectionCodeList(sectionCodeList);
            collect = gantryService.selectOdsSzdnGantryListNew(odsSzdnGantry)
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("2");
                        vo.setCode(item.getGantryCode());
                        vo.setName(item.getGantryName());
                        return vo;
                    }).collect(Collectors.toList());
        } else if ("3".equals(type)) {
            DwdLcztFwqjcxx dwdLcztFwqjcxx = new DwdLcztFwqjcxx();
            dwdLcztFwqjcxx.setSectionCodeList(sectionCodeList);
            collect = fwqjcxxService.selectDwdLcztFwqjcxxListNew(dwdLcztFwqjcxx)
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("3");
                        vo.setCode(item.getFwqbm());
                        vo.setName(item.getFwqmc());
                        return vo;
                    }).collect(Collectors.toList());
        }
        return AjaxResult.success(collect);
    }

    /**
     * 重点车辆库统计
     */
    @GetMapping(value = "/carVoList")
    public AjaxResult carVoList() {
        List<CarInfoVO> carVoList = carInfoService.selectCarVoList();
        return AjaxResult.success(carVoList);
    }


    /**
     * 追缴统计
     */
    @GetMapping(value = "/carAudit")
    public AjaxResult getCarAudit(IncomeStatisticParam param) {
        CarAuditVO vo = new CarAuditVO();

        CarStatisticsVO vo1 = carAduitFreeService.getCarAudit(param); // 逃费费用:异常流水
        if (null != vo1){
            vo.setTotalAmount(vo1.getEscapedAmount());
            vo.setTotalCount(vo1.getNumber());
        }


        CarStatisticsVO vo2 = carConfimFreeService.getCarConfirm(param); //确认追缴

        if (null != vo2){
            vo.setFinishedAmount(vo2.getEscapedAmount());
            vo.setFinishedCount(vo2.getNumber());
        }


        return AjaxResult.success(vo);
    }

    /**
     * 车辆预警
     */
    @GetMapping(value = "/carWarning")
    public AjaxResult getCarWarning(CarLocationParam param) {
        String type = param.getType();
        if(StringUtils.isNotBlank(type)) {
            switch (type) {
                case "1":
                    param.setTollCode(param.getCode());
                    break;
                case "2":
                    param.setGantryCode(param.getCode());
                    break;
                case "3":
                    param.setFwqbm(param.getCode());
                    break;
            }
        }
        List<CarWarningInfo> warningInfoList = carWarningInfoService.selectCarWarningInfoListLimit100(param);
        return AjaxResult.success(warningInfoList);
    }

    /**
     * 异常数据
     */
    @GetMapping(value = "/exceptionCar")
    public AjaxResult getExceptionCar() {
        List<CarSuspicious> carSuspicious = carSuspiciousService.selectCarSuspiciousListLimit10();
        return AjaxResult.success(carSuspicious);
    }

    /**
     * 重点车辆通行前10
     */
    @ApiOperation("重点车辆通行前10")
    @GetMapping(value = "/topTen")
    public AjaxResult topTen() {
        List<TopTenVO> topTenVO = snapshotFlowAddcodeService.getTopTen();
        return AjaxResult.success(topTenVO);
    }

    @ApiOperation("机构列表")
    @GetMapping(value = "/orgList")
    public AjaxResult getOrgList() {
        List<OrgVO> collect = baseOrgService.lambdaQuery().select(OdsYhglVBaseOrg::getOrgCode, OdsYhglVBaseOrg::getOrgName).list()
                .stream().map(item -> {
                    OrgVO orgVO = new OrgVO();
                    orgVO.setOrgCode(item.getOrgCode());
                    orgVO.setOrgName(item.getOrgName());
                    return orgVO;
                }).collect(Collectors.toList());
        return AjaxResult.success(collect);
    }

    /**
     * 堵漏增收统计
     */
    @ApiOperation("堵漏增收统计")
    @GetMapping(value = "/incomeStatistic")
    public AjaxResult incomeStatistic(IncomeStatisticParam param) {

        // 默认为所
        if (CommonUtil.isBlank(param.getQueryDateType())){
            param.setQueryDateType("suo");
        }
        List<incomeStatisticVO> voList =  carAduitFreeService.incomeStatistic(param);
        return AjaxResult.success(voList);
    }

    @GetMapping("/exceptRecordList")
    public TableDataInfo list(CarExceptRecord carExceptRecord) {
        startPage();
        List<CarExceptRecord> list = carExceptRecordService.selectCarExceptRecordList(carExceptRecord);
        TableDataInfo dataTable = getDataTable(list);
        List<CarExceptRecord> rows = (List<CarExceptRecord>) dataTable.getRows();
        for (CarExceptRecord row : rows) {
           String orgId = carConfimFreeService.selectOrgId(row.getCarId(), row.getId());
           row.setOrgId(orgId);
            Long count = carAduitFreeService.lambdaQuery().eq(CarAduitFree::getCarId, row.getCarId()).count();
            if (count != null && count > 0) {
                row.setSupplementaryStatus("1");
            }
        }
        return dataTable;
    }
}
