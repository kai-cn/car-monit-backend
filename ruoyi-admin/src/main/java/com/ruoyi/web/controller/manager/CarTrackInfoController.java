package com.ruoyi.web.controller.manager;

import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 车辆行驶轨迹Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@RestController
@RequestMapping("/manager/cartrackinfo")
public class CarTrackInfoController extends BaseController {

    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    @Resource
    private HttpSysUtilApiService httpSysUtilApiService;

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private IGeometryService geometryService;


    @Autowired
    private IZdataTrailTracksService zdataTrailTracksService;

    /**
     * 查询车辆行驶轨迹列表
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:list')")
    @GetMapping("/list")
    public TableDataInfo list(CarTrackInfo carTrackInfo) {
        startPage();
        // carTrackInfo.setTenantId(SecurityUtils.getTenantId()); // 查询我自己单位的租户
        List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        return getDataTable(list);
    }

    /**
     * 车俩历史轨迹 ：根据车牌号查询
     *
     * @param zdataTrailTracks
     * @return
     */
    @GetMapping("/listByCarId")
    public TableDataInfo listByCarId(ZdataTrailTracks zdataTrailTracks) {
        startPage();
        if (CommonUtil.isBlank(zdataTrailTracks.getCarNo())) {
            zdataTrailTracks.setCarNo("-1");
        }
        List<TrailInfo> trailList = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);
        for (TrailInfo rtn:trailList){
            List<TrailBo> josnList = rtn.getTrailList();
            List<Geometry> raodTrailList = new ArrayList<>();
            if (null !=josnList && josnList.size() > 0){
                List<String> roadCodeList = josnList.stream().map(TrailBo::getRoadCode).distinct().collect(Collectors.toList());
                raodTrailList = geometryService.getListByCode(roadCodeList);
            }
            rtn.setRaodTrailList(raodTrailList);
        }

        return getDataTable(trailList);
    }


    /**
     * 车俩历史轨迹 ：根据时间查询
     *
     * @param zdataTrailTracks
     * @return
     */
    @GetMapping("/listByCarByTime")
    public TableDataInfo listByCarByTime(ZdataTrailTracks zdataTrailTracks) {
        startPage();
        List<TrailInfo> trailList = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);
        for (TrailInfo rtn:trailList){
            List<TrailBo> josnList = rtn.getTrailList();
            List<Geometry> raodTrailList = new ArrayList<>();
            if (null !=josnList && josnList.size() > 0){
                List<String> roadCodeList = josnList.stream().map(TrailBo::getRoadCode).distinct().collect(Collectors.toList());
                raodTrailList = geometryService.getListByCode(roadCodeList);
            }
            rtn.setRaodTrailList(raodTrailList);
        }
        return getDataTable(trailList);
    }


    /**
     * 导出车辆行驶轨迹列表
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:export')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.EXPORT)
    @GetMapping("/export")
    public AjaxResult export(CarTrackInfo carTrackInfo) {
        List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        ExcelUtil<CarTrackInfo> util = new ExcelUtil<CarTrackInfo>(CarTrackInfo.class);
        return util.exportExcel(list, "车辆行驶轨迹数据");
    }

    /**
     * 获取车辆行驶轨迹详细信息
     */
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") String id) {
        return AjaxResult.success(carTrackInfoService.selectCarTrackInfoById(id));
    }

    /**
     * 新增车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:add')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CarTrackInfo carTrackInfo) {
        return carTrackInfoService.saveCarTrackInfo(carTrackInfo);
    }

    /**
     * 修改车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:edit')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CarTrackInfo carTrackInfo) {
        return carTrackInfoService.saveCarTrackInfo(carTrackInfo);
    }

    /**
     * 删除车辆行驶轨迹
     */
    @PreAuthorize("@ss.hasPermi('manager:cartrackinfo:remove')")
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.DELETE)
    @DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable String[] ids) {
        return carTrackInfoService.deleteCarTrackInfoByIds(ids);
    }

}
