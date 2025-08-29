package com.ruoyi.web.controller.manager.bigscreen;

import com.ruoyi.base.domain.OdsSzdnSection;
import com.ruoyi.base.domain.OdsSzdnToll;
import com.ruoyi.base.service.IOdsSzdnSectionService;
import com.ruoyi.base.service.IOdsSzdnTollService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.vo.bigscreen.*;
import com.ruoyi.manager.service.ICarAduitFreeService;
import com.ruoyi.manager.service.ICarConfimFreeService;
import com.ruoyi.manager.service.ICarInfoService;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

import static com.ruoyi.common.utils.PageUtils.startPage;

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
    private IOdsSzdnTollService odsSzdnTollService;


    /**
     *
     */
    @ApiOperation("重点关注车辆统计")
    @GetMapping(value = "/carStatistics")
    public AjaxResult<CarStatisticsVO> getCarStatistics() {
        CarStatisticsVO carStatisticsVO = carConfimFreeService.getCarStatistics();
        return AjaxResult.success(carStatisticsVO);
    }

    /**
     * 地图
     */
    @ApiOperation("车辆地图")
    @GetMapping(value = "/carLocation")
    public AjaxResult<List<CarLocationVO>> getCarLocation(CarLocationParam param) {
        List<CarLocationVO> carLocationVOList = carInfoService.carLocation(param);
        return AjaxResult.success(carLocationVOList);
    }

    @ApiOperation("路段列表")
    @GetMapping(value = "/sectionList")
    public AjaxResult<List<SectionVO>> getSectionList() {
        List<SectionVO> collect = odsSzdnSectionService.lambdaQuery().select(OdsSzdnSection::getSectionCode, OdsSzdnSection::getSectionName).list()
                .stream().map(item -> {
                    SectionVO sectionVO = new SectionVO();
                    sectionVO.setSectionCode(item.getSectionCode());
                    sectionVO.setSectionName(item.getSectionName());
                    return sectionVO;
                }).collect(Collectors.toList());
        return AjaxResult.success(collect);
    }

    @ApiOperation("收费站列表")
    @GetMapping(value = "/tollList")
    public AjaxResult<List<TollVO>> getTollList() {
        List<TollVO> collect = odsSzdnTollService.lambdaQuery().select(OdsSzdnToll::getTollCode, OdsSzdnToll::getTollName).list()
                .stream().map(item -> {
            TollVO tollVO = new TollVO();
            tollVO.setTollCode(item.getTollCode());
            tollVO.setTollName(item.getTollName());
            return tollVO;
        }).collect(Collectors.toList());
        return AjaxResult.success(collect);
    }

    /**
     * 重点车辆库统计
     */
    @ApiOperation("重点车辆库统计")
    @GetMapping(value = "/carVoList")
    public AjaxResult<List<CarInfoVO>> carVoList() {
        startPage();
        List<CarInfoVO> carVoList = carInfoService.selectCarVoList();
        return AjaxResult.success(carVoList);
    }


    /**
     * 追缴统计
     */
    @ApiOperation("追缴统计")
    @GetMapping(value = "/carAudit")
    public AjaxResult<List<CarAuditVO>> getCarAudit() {
        List<CarAuditVO> carAuditVOList = carAduitFreeService.getCarAudit();
        Long count = carConfimFreeService.lambdaQuery().count();
        return AjaxResult.success(carAuditVOList);
    }
}
