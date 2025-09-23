package com.ruoyi.web.controller.manager;

import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.CarVO;
import com.ruoyi.manager.domain.vo.TrailBo;
import com.ruoyi.manager.domain.vo.TrailInfo;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

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
     * @param carTrackInfo
     * @return
     */
    @GetMapping("/listByCarId")
    public AjaxResult listByCarId(CarTrackInfo carTrackInfo) {
        if (CommonUtil.isBlank(carTrackInfo.getCarNo())) {
            carTrackInfo.setCarNo("-1");
        }
        // ----------查询自己的表
          /* List<CarTrackInfo> list = carTrackInfoService.selectCarTrackInfoList(carTrackInfo);
        return AjaxResult.success(list);*/

        // ---------- 查询接口
        CarParaVO carParaVO = new CarParaVO();
        carParaVO.setCarNo(carTrackInfo.getCarNo()); // 车牌号
        carParaVO.setApplyTime1(carTrackInfo.getApplyTime1());
        carParaVO.setApplyTime2(carTrackInfo.getApplyTime2());
        Map<String, List<TrailBo>> caMap =  httpSysUtilApiService.carTrackQueryByCarNo(carParaVO);

        List<TrailInfo> trailList = new ArrayList<>();
        for (Map.Entry<String, List<TrailBo>> entry : caMap.entrySet()) {
            String carNo = entry.getKey();
            List<TrailBo> josnList = entry.getValue();

            TrailInfo trailInfo = new TrailInfo();
            trailInfo.setTrailUuid(carNo);
            trailInfo.setTrailList(josnList);

            trailList.add(trailInfo);
        }

        return AjaxResult.success(trailList);

    }


    /**
     * 车俩历史轨迹 ：根据时间查询
     *
     * @param carTrackInfo
     * @return
     */
    @GetMapping("/listByCarByTime")
    public AjaxResult listByCarByTime(CarTrackInfo carTrackInfo) {

        // 查询所有的车俩
        List<CarInfo> carList = carInfoService.getRedisCarList();
        List<CarVO> carVOList = new ArrayList<>();
        for (CarInfo rtn : carList) {
            CarVO tempVO = new CarVO();
            tempVO.setCarId(rtn.getId());
            tempVO.setCarNo(rtn.getCarNo());
            carVOList.add(tempVO);
        }
        // ---------- 查询接口
        CarParaVO carParaVO = new CarParaVO();
        carParaVO.setCarlist(carVOList);

        carParaVO.setApplyTime1(carTrackInfo.getApplyTime1());
        carParaVO.setApplyTime2(carTrackInfo.getApplyTime2());
        Map<String, List<TrailBo>> caMap =  httpSysUtilApiService.carTrackQueryByTime(carParaVO);


        List<TrailInfo> trailList = new ArrayList<>();
        for (Map.Entry<String, List<TrailBo>> entry : caMap.entrySet()) {
            String carNo = entry.getKey();
            List<TrailBo> josnList = entry.getValue();

            TrailInfo trailInfo = new TrailInfo();
            trailInfo.setTrailUuid(carNo);
            trailInfo.setTrailList(josnList);

            trailList.add(trailInfo);
        }

        return AjaxResult.success(trailList);

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
