package com.ruoyi.web.controller.manager;

import com.alibaba.fastjson2.JSON;
import com.github.pagehelper.PageInfo;
import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 车辆行驶轨迹Controller
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Slf4j
@RestController
@RequestMapping("/manager/cartrackinfo")
public class CarTrackInfoController extends BaseController {

    @Autowired
    private ICarTrackInfoService carTrackInfoService;

    @Resource
    private HttpSysUtilApiService httpSysUtilApiService;




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
     * @param
     * @return
     */
    @GetMapping("/listByCarId")
    public TableDataInfo listByCarId(ZdataTrailTracks zdataTrailTracks) {

        // ----------------------- 查询自己表结构
        zdataTrailTracks.setCarNo(CommonUtil.isNull(zdataTrailTracks.getCarNo()));
        if (CommonUtil.isBlank(zdataTrailTracks.getCarNo())) {
            zdataTrailTracks.setCarNo("-1");
        }

        startPage();
        List<ZdataTrailTracks> carlist = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);

        // 如果查询数据为空
        long totalNum = new PageInfo(carlist).getTotal();

        List<TrailInfo> rtnList = new ArrayList<>();
        if (null != carlist && carlist.size() > 0) {
            for (ZdataTrailTracks tracksBo : carlist) {
                String keyValue = tracksBo.getTrackJosn(); // 行驶轨迹
                List<TrailBo> josnList = new ArrayList<TrailBo>();
                if (CommonUtil.isNotBlank(keyValue)) {
                    josnList = JSON.parseArray(keyValue, TrailBo.class);
                    tracksBo.setTrailPoints("");  // 行驶轨迹
                    tracksBo.setTrackJosn("");
                    String carNo = CommonUtil.isNull(tracksBo.getPlateKey());
                    TrailInfo trailInfo = new TrailInfo();
                    trailInfo.setTracks(tracksBo);
                    trailInfo.setTrailList(josnList);
                    trailInfo.setTrailUuid(carNo);

                    // 路线
                    List<Geometry> raodTrailList = new ArrayList<>();
                    trailInfo.setRaodTrailList(raodTrailList);

                    // 集合列表
                    TrailDevCountBO trailDevCountBO = new TrailDevCountBO();
                    Integer exceptNum = 0;
                    List<TrailDevBO> TrailDevList = new ArrayList<>();
                    trailDevCountBO.setExceptNum(exceptNum);
                    trailDevCountBO.setTrailDevList(TrailDevList);
                    trailInfo.setTrailDevCountBO(trailDevCountBO);


                    rtnList.add(trailInfo);
                }
            }
        }else{
            // ----------------------- 查询接口
            CarParaVO carParaVO = new CarParaVO();
            carParaVO.setCarNo(zdataTrailTracks.getCarNo()); // 车牌号
           /* carParaVO.setApplyTime1(zdataTrailTracks.getApplyTime1());
            carParaVO.setApplyTime2(zdataTrailTracks.getApplyTime2());*/
            carParaVO.setPageNum(1);
            carParaVO.setPageSize(20);

            TableDataInfo tableDataInfo = httpSysUtilApiService.carTrackQueryByCarNo(carParaVO);

            List<TrailInfo> trailList = new ArrayList<>();
            if (null != tableDataInfo.getRows() && tableDataInfo.getRows().size() > 0) {
                String trackJosn =JSON.toJSONString(tableDataInfo.getRows());
                trailList = JSON.parseArray(trackJosn, TrailInfo.class);
                trailList = trailList.stream().sorted(Comparator.comparing(TrailInfo::getEnterTime).reversed())
                        .collect(Collectors.toList());

                List<String> carNoList = new ArrayList<>();
                // 找到下一个位置
                List<ZdataTrailTracks> addlist = new ArrayList<>();
                carNoList.add(zdataTrailTracks.getCarNo());
                for (TrailInfo trailInfo : trailList) {

                    //  ------------------新增
                    ZdataTrailTracks tracksBo = trailInfo.getTracks();
                    String carNo = CommonUtil.isNull(tracksBo.getPlateKey());
                    List<TrailBo> josnList = trailInfo.getTrailList(); // trailPoints
                    tracksBo.setPlateKey(carNo);
                    tracksBo.setPointCount(0L);
                    if (null != josnList) {
                        tracksBo.setTrackJosn(JSON.toJSONString(josnList));
                        tracksBo.setPointCount(Long.parseLong(josnList.size() + ""));
                    }
                    addlist.add(tracksBo);


                    // 路线
                    List<Geometry> raodTrailList = new ArrayList<>();
                    trailInfo.setRaodTrailList(raodTrailList);

                    // 集合列表
                    TrailDevCountBO trailDevCountBO = new TrailDevCountBO();
                    Integer exceptNum = 0;
                    List<TrailDevBO> TrailDevList = new ArrayList<>();
                    trailDevCountBO.setExceptNum(exceptNum);
                    trailDevCountBO.setTrailDevList(TrailDevList);
                    trailInfo.setTrailDevCountBO(trailDevCountBO);

                    rtnList.add(trailInfo);

                }

                if (carNoList.size() > 0){
                    zdataTrailTracksService.removeRealData(carNoList);
                }
                if (addlist.size() > 0) {
                    zdataTrailTracksService.saveBatch(addlist);
                }


                totalNum = tableDataInfo.getTotal();
            }
        }

        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(rtnList);
        rspData.setTotal(totalNum);
        return rspData;


    }


    /**
     * 车俩历史轨迹 ：根据时间查询
     *
     * @param zdataTrailTracks carTrackInfo
     * @return
     */
    @GetMapping("/listByCarByTime")
    public TableDataInfo listByCarByTime(ZdataTrailTracks zdataTrailTracks) {

        // 当前页面
       /* if (null == carTrackInfo.getPageNum()){
            carTrackInfo.setPageNum(1);
        }
        // 分页大小
        if (null == carTrackInfo.getPageSize()){
            carTrackInfo.setPageSize(10);
        }

        // ----------------------- 查询接口
        CarParaVO carParaVO = new CarParaVO();
        carParaVO.setCarNo(carTrackInfo.getCarNo()); // 车牌号
        carParaVO.setApplyTime1(carTrackInfo.getApplyTime1());
        carParaVO.setApplyTime2(carTrackInfo.getApplyTime2());
        carParaVO.setPageNum(carTrackInfo.getPageNum());
        carParaVO.setPageSize(carTrackInfo.getPageSize());

        TableDataInfo tableDataInfo = httpSysUtilApiService.carTrackQueryByTime(carParaVO);

        List<TrailInfo> trailList = new ArrayList<>();
        if (null != tableDataInfo.getRows() && tableDataInfo.getRows().size() > 0) {
            String trackJosn =JSON.toJSONString(tableDataInfo.getRows());
            trailList = JSON.parseArray(trackJosn, TrailInfo.class);
            trailList = trailList.stream().sorted(Comparator.comparing(TrailInfo::getEnterTime).reversed())
                    .collect(Collectors.toList());
            for (TrailInfo rtn : trailList) {
                List<TrailBo> josnList = rtn.getTrailList();
                List<Geometry> raodTrailList = new ArrayList<>();
                if (null != josnList && josnList.size() > 0) {
                    raodTrailList = carTrackInfoService.getCarGeometry(josnList);
                }
                rtn.setRaodTrailList(raodTrailList);
            }
        }
        tableDataInfo.setRows(trailList);
        return tableDataInfo;*/


        // ----------------------- 查询自己表结构
        startPage();
        List<ZdataTrailTracks> carlist = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);
        List<TrailInfo> rtnList = new ArrayList<>();
        if (null != carlist && carlist.size() > 0) {
            for (ZdataTrailTracks tracksBo : carlist) {
                String keyValue = tracksBo.getTrackJosn(); // 行驶轨迹
                List<TrailBo> josnList = new ArrayList<TrailBo>();
                if (CommonUtil.isNotBlank(keyValue)) {
                    josnList = JSON.parseArray(keyValue, TrailBo.class);
                    tracksBo.setTrailPoints("");  // 行驶轨迹
                    tracksBo.setTrackJosn("");
                    String carNo = CommonUtil.isNull(tracksBo.getPlateKey());
                    TrailInfo trailInfo = new TrailInfo();
                    trailInfo.setTracks(tracksBo);
                    trailInfo.setTrailList(josnList);
                    trailInfo.setTrailUuid(carNo);

                    // 路线
                    List<Geometry> raodTrailList = new ArrayList<>();
                    trailInfo.setRaodTrailList(raodTrailList);

                    // 集合列表
                    TrailDevCountBO trailDevCountBO = new TrailDevCountBO();
                    Integer exceptNum = 0;
                    List<TrailDevBO> TrailDevList = new ArrayList<>();
                    trailDevCountBO.setExceptNum(exceptNum);
                    trailDevCountBO.setTrailDevList(TrailDevList);
                    trailInfo.setTrailDevCountBO(trailDevCountBO);

                    rtnList.add(trailInfo);
                }
            }
        }

        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(rtnList);
        rspData.setTotal(new PageInfo(carlist).getTotal());
        return rspData;
    }

    /**
     * 修改车辆行驶轨迹
     */
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.UPDATE)
    @PutMapping("/changeTrailInfo")
    public AjaxResult changeTrailInfo(@RequestBody TrailInfo trailInfo) {
        if (null != trailInfo) {
            ZdataTrailTracks tracks = trailInfo.getTracks();
            List<TrailBo> josnList = trailInfo.getTrailList();
            if (null != tracks && null != josnList && josnList.size() > 0) {
                // 转换查询
                TrailInfo rtn = httpSysUtilApiService.changeTrailInfo(trailInfo);

                // 获取抓拍对象
                trailInfo.setTrailList(rtn.getTrailList());
                josnList = trailInfo.getTrailList(); // 新的数据--------------
                List<Geometry> raodTrailList = new ArrayList<>();
                if (null != josnList && josnList.size() > 0) {
                    // raodTrailList = carTrackInfoService.getCarGeometry(tracks, josnList);
                    raodTrailList = carTrackInfoService.getCarGeometryByPlan(tracks, josnList);
                }
                trailInfo.setRaodTrailList(raodTrailList);
                trailInfo.setTrailDevCountBO(carTrackInfoService.getTrailDevBO(josnList));
            }
        }
        return AjaxResult.success(trailInfo);
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
