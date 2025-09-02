package com.ruoyi.web.controller.manager.bigscreen;

import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.*;
import com.ruoyi.common.core.domain.AjaxResultNew;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.CarAduitFree;
import com.ruoyi.manager.domain.CarConfimFree;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.vo.bigscreen.*;
import com.ruoyi.manager.service.*;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;


@ApiOperation("大屏接口")
@RestController
@RequestMapping("/manager/bigScreen")
@CrossOrigin(origins = "*")
public class BigScreenController {

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


    /**
     *
     */
    @ApiOperation("重点关注车辆统计")
    @GetMapping(value = "/carStatistics")
    public AjaxResultNew<List<CarStatisticsVO>> getCarStatistics() {
        List<CarStatisticsVO> carStatisticsVO = carConfimFreeService.getCarStatistics();
        return AjaxResultNew.success(carStatisticsVO);
    }

    /**
     * 地图
     */
    @ApiOperation("车辆地图")
    @GetMapping(value = "/carLocation")
    public AjaxResultNew getCarLocation(CarLocationParam param) {
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
        return AjaxResultNew.success(carLocationVOList);
    }

    @ApiOperation("路段列表")
    @GetMapping(value = "/sectionList")
    public AjaxResultNew<List<SectionVO>> getSectionList() {
        List<SectionVO> collect = odsSzdnSectionService.lambdaQuery().select(OdsSzdnSection::getSectionCode, OdsSzdnSection::getSectionName).list()
                .stream().map(item -> {
                    SectionVO sectionVO = new SectionVO();
                    sectionVO.setSectionCode(item.getSectionCode());
                    sectionVO.setSectionName(item.getSectionName());
                    return sectionVO;
                }).collect(Collectors.toList());
        return AjaxResultNew.success(collect);
    }

    @ApiOperation("收费站门架服务区列表")
    @GetMapping(value = "/tollGantryFwqList")
    public AjaxResultNew<List<TollGantryFwqVO>> getTollList(@RequestParam String type) {
        List<TollGantryFwqVO> collect = new ArrayList<>();
        if ("1".equals(type)) {
            collect = tollService.lambdaQuery().select(OdsSzdnToll::getTollCode, OdsSzdnToll::getTollName).list()
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("1");
                        vo.setCode(item.getTollCode());
                        vo.setName(item.getTollName());
                        return vo;
                    }).collect(Collectors.toList());
        } else if ("2".equals(type)) {
            collect = gantryService.lambdaQuery().select(OdsSzdnGantry::getGantryCode, OdsSzdnGantry::getGantryName).list()
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("2");
                        vo.setCode(item.getGantryCode());
                        vo.setName(item.getGantryName());
                        return vo;
                    }).collect(Collectors.toList());
        } else if ("3".equals(type)) {
            collect = fwqjcxxService.lambdaQuery().select(DwdLcztFwqjcxx::getFwqbm, DwdLcztFwqjcxx::getFwqmc).list()
                    .stream().map(item -> {
                        TollGantryFwqVO vo = new TollGantryFwqVO();
                        vo.setType("3");
                        vo.setCode(item.getFwqbm());
                        vo.setName(item.getFwqmc());
                        return vo;
                    }).collect(Collectors.toList());
        }
        return AjaxResultNew.success(collect);
    }

    /**
     * 重点车辆库统计
     */
    @ApiOperation("重点车辆库统计")
    @GetMapping(value = "/carVoList")
    public AjaxResultNew<List<CarInfoVO>> carVoList() {
        List<CarInfoVO> carVoList = carInfoService.selectCarVoList();
        return AjaxResultNew.success(carVoList);
    }


    /**
     * 追缴统计
     */
    @ApiOperation("追缴统计")
    @GetMapping(value = "/carAudit")
    public AjaxResultNew<CarAuditVO> getCarAudit() {
        CarAuditVO vo = new CarAuditVO();
        BigDecimal totalAmount = carAduitFreeService.getCarAudit();
        BigDecimal finishedAmount = carConfimFreeService.getCarConfirm();
        if (totalAmount != null) {
            vo.setTotalAmount(totalAmount);
        }
        if (finishedAmount != null) {
            vo.setFinishedAmount(finishedAmount);
        }
        Long confirmCount = carConfimFreeService.lambdaQuery().eq(CarConfimFree::getDelFlag, "0").count();
        Long auditCount = carAduitFreeService.lambdaQuery().eq(CarAduitFree::getDelFlag, "0").count();
        if (confirmCount != null && confirmCount > 0) {
            vo.setTotalCount(Math.toIntExact(confirmCount));
        }
        if (auditCount != null && auditCount > 0) {
            vo.setFinishedCount(Math.toIntExact(auditCount));
        }
        return AjaxResultNew.success(vo);
    }

    /**
     * 车辆预警
     */
    @ApiOperation("车辆预警")
    @GetMapping(value = "/carWarning")
    public AjaxResultNew<List<CarWarningInfo>> getCarWarning() {
        List<CarWarningInfo> warningInfoList = carWarningInfoService.selectCarWarningInfoList(new CarWarningInfo());
        return AjaxResultNew.success(warningInfoList);
    }

    /**
     * 异常数据
     */
    @ApiOperation("异常数据")
    @GetMapping(value = "/exceptionCar")
    public AjaxResultNew<List<CarSuspicious>> getExceptionCar() {
        List<CarSuspicious> carSuspicious = carSuspiciousService.selectCarSuspiciousList(new CarSuspicious());
        return AjaxResultNew.success(carSuspicious);
    }

    /**
     * 重点车辆通行前10
     */
    @ApiOperation("重点车辆通行前10")
    @GetMapping(value = "/topTen")
    public AjaxResultNew<List<TopTenVO>> topTen() {
        List<TopTenVO> topTenVO = snapshotFlowAddcodeService.getTopTen();
        return AjaxResultNew.success(topTenVO);
    }

    @ApiOperation("机构列表")
    @GetMapping(value = "/orgList")
    public AjaxResultNew<List<OrgVO>> getOrgList() {
        List<OrgVO> collect = baseOrgService.lambdaQuery().select(OdsYhglVBaseOrg::getOrgCode, OdsYhglVBaseOrg::getOrgName).list()
                .stream().map(item -> {
                    OrgVO orgVO = new OrgVO();
                    orgVO.setOrgCode(item.getOrgCode());
                    orgVO.setOrgName(item.getOrgName());
                    return orgVO;
                }).collect(Collectors.toList());
        return AjaxResultNew.success(collect);
    }

    /**
     * 堵漏增收统计
     */
    @ApiOperation("堵漏增收统计")
    @GetMapping(value = "/incomeStatistic")
    public AjaxResultNew<List<incomeStatisticVO>> incomeStatistic(IncomeStatisticParam param) {
        if(StringUtils.isNotBlank(param.getYear()) && StringUtils.isNotBlank(param.getMonth())){
            String start = param.getYear() + "-" + param.getMonth() + "-01";
            param.setStartDate(start);
        }
        List<incomeStatisticVO> voList =  carAduitFreeService.incomeStatistic(param);
        /*if(StringUtils.isNotBlank(param.getQueryDateType())) {
            String queryDateType = param.getQueryDateType();
            if("1".equals(queryDateType)) {
                //1年
            } else if("2".equals(queryDateType)) {
                //2月
            }
        }*/
        return AjaxResultNew.success(voList);
    }
}
