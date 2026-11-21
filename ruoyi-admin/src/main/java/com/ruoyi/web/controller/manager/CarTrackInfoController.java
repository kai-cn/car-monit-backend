package com.ruoyi.web.controller.manager;

import com.alibaba.fastjson2.JSON;
import com.github.pagehelper.PageInfo;
import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.integration.api.ApiClientException;
import com.ruoyi.integration.api.ApiPageResult;
import com.ruoyi.integration.api.TrafficApiClient;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.service.ICarQueryLogService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import com.ruoyi.manager.service.bigscreen.FeatureSwitchService;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.ArrayList;
import java.util.List;

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
    private RedisCache redisCache;

    @Autowired
    private IZdataTrailTracksService zdataTrailTracksService;

    @Autowired
    private ICarQueryLogService carQueryLogService;

    @Autowired
    private TrafficApiClient trafficApiClient;

    @Autowired
    private FeatureSwitchService featureSwitchService;

    @Value("${bigscreen.trail.mode:api}")
    private String trailMode;



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

        zdataTrailTracks.setCarNo(CommonUtil.isNull(zdataTrailTracks.getCarNo()));
        if (CommonUtil.isBlank(zdataTrailTracks.getCarNo())) {
            zdataTrailTracks.setCarNo("-1");
        }

        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();

        // 在线列表统一走 api；不再回写本地 zdata_trail_tracks（本地物化已移除）
        if (apiFirst()) {
            try {
                CarParaVO carParaVO = new CarParaVO();
                carParaVO.setCarNo(zdataTrailTracks.getCarNo());
                carParaVO.setApplyTime1(zdataTrailTracks.getApplyTime1());
                carParaVO.setApplyTime2(zdataTrailTracks.getApplyTime2());
                ApiPageResult<TrailInfo> apiPage = trafficApiClient.trailPage(carParaVO,
                        pageNum, pageSize);
                cacheHistoryTrail(zdataTrailTracks.getCarNo(), apiPage.getRows());
                return pageResult(apiPage.getRows(), apiPage.getTotal());
            } catch (ApiClientException e) {
                logger.warn("[轨迹在线] api 查询失败，回退本地只读 code={} msg={}",
                        e.getCode(), e.getMessage());
            }
        }

        // 兜底：本地旧表只读（不再写回、不再物化）
        startPage();
        List<ZdataTrailTracks> carlist = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);
        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(buildTrailInfos(carlist));
        rspData.setTotal(new PageInfo(carlist).getTotal());
        return rspData;
    }

    /**
     * 轨迹在线查询是否 api 优先：运行期开关 + 配置模式（local 强制本地）。
     */
    private boolean apiFirst() {
        return featureSwitchService.isEnabled(FeatureSwitchService.TRAIL_API)
                && !"local".equalsIgnoreCase(trailMode == null ? "" : trailMode.trim());
    }

    /**
     * 旧本地表行 → TrailInfo（只读兜底路径）。
     */
    private List<TrailInfo> buildTrailInfos(List<ZdataTrailTracks> carlist) {
        List<TrailInfo> rtnList = new ArrayList<>();
        if (null == carlist || carlist.isEmpty()) {
            return rtnList;
        }
        for (ZdataTrailTracks tracksBo : carlist) {
            String keyValue = tracksBo.getTrackJosn();
            if (CommonUtil.isBlank(keyValue)) {
                continue;
            }
            List<TrailBo> josnList = JSON.parseArray(keyValue, TrailBo.class);
            tracksBo.setTrailPoints("");
            tracksBo.setTrackJosn("");
            rtnList.add(newTrailInfo(tracksBo, josnList));
        }
        return rtnList;
    }

    private TrailInfo newTrailInfo(ZdataTrailTracks tracksBo, List<TrailBo> josnList) {
        String carNo = CommonUtil.isNull(tracksBo.getPlateKey());
        TrailInfo trailInfo = new TrailInfo();
        trailInfo.setTracks(tracksBo);
        trailInfo.setTrailList(josnList);
        trailInfo.setTrailUuid(carNo);
        trailInfo.setRaodTrailList(new ArrayList<Geometry>());
        TrailDevCountBO trailDevCountBO = new TrailDevCountBO();
        trailDevCountBO.setExceptNum(0);
        trailDevCountBO.setTrailDevList(new ArrayList<TrailDevBO>());
        trailInfo.setTrailDevCountBO(trailDevCountBO);
        return trailInfo;
    }

    /**
     * 轨迹“当前页”缓存写入 backend 私有键，禁止写 {@code car_history_trail}：
     * 该键由 api 侧 TrackTask 作为“全量历史”只读消费，写入分页数据会被当成旧全量合并。
     * 预警详情优先读 api 全量键，缺失时再回退本页缓存。
     */
    private void cacheHistoryTrail(String carNo, List<TrailInfo> trailList) {
        if (CommonUtil.isBlank(carNo) || null == trailList || trailList.isEmpty()) {
            return;
        }
        try {
            redisCache.setCacheObject(Constants.car_history_trail_page + carNo, trailList);
        } catch (RuntimeException e) {
            logger.warn("[轨迹在线] 写 Redis 轨迹页缓存失败 carNo={} reason={}", carNo, e.getMessage());
        }
    }

    private TableDataInfo pageResult(List<TrailInfo> rows, long total) {
        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(rows == null ? new ArrayList<TrailInfo>() : rows);
        rspData.setTotal(total);
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


        PageDomain page = TableSupport.buildPageRequest();
        int pageNum = page.getPageNum() == null ? 1 : page.getPageNum();
        int pageSize = page.getPageSize() == null ? 10 : page.getPageSize();

        // 有车牌时走 api；时间-only 查询 api 契约要求 carNo，继续走本地旧表（只读）
        if (apiFirst() && CommonUtil.isNotBlank(zdataTrailTracks.getCarNo())) {
            try {
                CarParaVO carParaVO = new CarParaVO();
                carParaVO.setCarNo(zdataTrailTracks.getCarNo());
                carParaVO.setApplyTime1(zdataTrailTracks.getApplyTime1());
                carParaVO.setApplyTime2(zdataTrailTracks.getApplyTime2());
                ApiPageResult<TrailInfo> apiPage = trafficApiClient.trailPage(carParaVO,
                        pageNum, pageSize);
                cacheHistoryTrail(zdataTrailTracks.getCarNo(), apiPage.getRows());
                return pageResult(apiPage.getRows(), apiPage.getTotal());
            } catch (ApiClientException e) {
                logger.warn("[轨迹按时间] api 查询失败，回退本地只读 code={} msg={}",
                        e.getCode(), e.getMessage());
            }
        }

        startPage();
        List<ZdataTrailTracks> carlist = zdataTrailTracksService.carTrackQuery(zdataTrailTracks);
        TableDataInfo rspData = new TableDataInfo();
        rspData.setCode(HttpStatus.SUCCESS);
        rspData.setMsg("查询成功");
        rspData.setRows(buildTrailInfos(carlist));
        rspData.setTotal(new PageInfo(carlist).getTotal());
        return rspData;
    }

    /**
     * 修改车辆行驶轨迹
     */
    @Log(title = "车辆行驶轨迹", businessType = BusinessType.UPDATE)
    @PutMapping("/changeTrailInfo")
    public AjaxResult changeTrailInfo(@RequestBody TrailInfo trailInfo) {
        
        // 查询日志
        carQueryLogService.queryLog(JSON.toJSONString(trailInfo), "1", "1");
        if (null != trailInfo) {
            ZdataTrailTracks tracks = trailInfo.getTracks();
            List<TrailBo> josnList = trailInfo.getTrailList();
            if (null != tracks && null != josnList && josnList.size() > 0) {
                // 转换查询
               //  TrailInfo rtn = httpSysUtilApiService.changeTrailInfo(trailInfo);

                // 获取抓拍对象
                trailInfo.setTrailList(josnList);
                josnList = trailInfo.getTrailList(); // 新的数据--------------
                List<Geometry> raodTrailList = new ArrayList<>();
                if (null != josnList && josnList.size() > 0) {
                    raodTrailList = carTrackInfoService.getCarGeometryByPlanNew(tracks, josnList);
                }
                trailInfo.setRaodTrailList(raodTrailList);
                trailInfo.setTrailDevCountBO(carTrackInfoService.getTrailDevBO(tracks,josnList));
            }
        }
        return AjaxResult.success(trailInfo);
    }


    @GetMapping(value = "/carSnapShot")
    public AjaxResult carSnapShot(TrailBo trailBo) {
        if(null != trailBo) {
            String stateType = CommonUtil.isNull(trailBo.getStateType());
            String pointUuid = trailBo.getPointUuid();
            if(StringUtils.isNoneBlank(stateType, pointUuid)) {
                TrailBo bo = httpSysUtilApiService.getByTrailBo(trailBo);
                return AjaxResult.success(bo);
            }
        }
        return AjaxResult.success();
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
