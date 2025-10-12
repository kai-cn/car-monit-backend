package com.ruoyi.manager.service.impl;


import cn.hutool.core.util.StrUtil;
import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONUtil;
import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.domain.ZdataTrailTracks;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.mapper.CarTrackInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import com.ruoyi.manager.service.ICarWarningInfoService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

/**
 * 车辆行驶轨迹Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Slf4j
@Service
public class CarTrackInfoServiceImpl extends ServiceImpl<CarTrackInfoMapper, CarTrackInfo> implements ICarTrackInfoService {


    @Autowired
    private CarTrackInfoMapper carTrackInfoMapper;

    @Autowired
    private ICarInfoService carInfoService;

    @Resource
    private HttpSysUtilApiService httpSysUtilApiService;

    @Autowired
    private ICarWarningInfoService carWarningInfoService;

    @Autowired
    private IGeometryService geometryService;

    @Value("${isLocalhost}")
    private String isLocalhost;

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询车辆行驶轨迹
     *
     * @param id 车辆行驶轨迹ID
     * @return 车辆行驶轨迹
     */
    @Override
    public CarTrackInfo selectCarTrackInfoById(String id) {
        return carTrackInfoMapper.selectCarTrackInfoById(id);
    }

    /**
     * 查询车辆行驶轨迹列表
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 车辆行驶轨迹
     */
    @Override
    public List<CarTrackInfo> selectCarTrackInfoList(CarTrackInfo carTrackInfo) {
        List<CarTrackInfo> list = carTrackInfoMapper.selectCarTrackInfoList(carTrackInfo);
        if (null != list && list.size() > 0) {
            for (CarTrackInfo rtn : list) {

                if (CommonUtil.isNotBlank(rtn.getLongitude())){
                    rtn.setLongitudeDec(new BigDecimal(rtn.getLongitude()));
                }

                if (CommonUtil.isNotBlank(rtn.getLatitude())){
                    rtn.setLatitudeDec(new BigDecimal(rtn.getLatitude()));
                }
            }
        }
        return list;
    }


    /**
     * 新增或者修改车辆行驶轨迹
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarTrackInfo(CarTrackInfo carTrackInfo)
    {
        if (CommonUtil.isNotBlank(carTrackInfo.getId()))
        {
            // 修改
            carTrackInfoMapper.updateById(carTrackInfo);
        }
        else
        {
            // 新增 主键
            carTrackInfoMapper.insert(carTrackInfo);
        }
        return AjaxResult.success("操作成功！",carTrackInfo.getId());
    }

    /**
     * 批量删除车辆行驶轨迹
     *
     * @param ids 需要删除的车辆行驶轨迹ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarTrackInfoByIds(String[] ids)
    {
        int count = carTrackInfoMapper.deleteCarTrackInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆行驶轨迹信息
     *
     * @param id 车辆行驶轨迹ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarTrackInfoById(String id)
    {
        int count = carTrackInfoMapper.deleteCarTrackInfoById(id);
        return AjaxResult.success(count);
    }


    /**
     * 轨迹同步
     *
     * @return 结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncCurrentTrack() {
        // 查询所有的车俩
        List<CarInfo> carList = carInfoService.getRedisCarList();

        List<CarInfo> updatalist = new ArrayList<CarInfo>();

        // 新增的预警
        List<CarWarningInfo> addCarWarningInfoList = new ArrayList<>();
        // 删除的预警
        List<String> delCarWarningInfoList = new ArrayList<>();

        Long userId = 1L;

        // System.out.println("获取的配置信息：--本地配置："+isLocalhost);
        Boolean isZxFlag = true; // 是否执行
        if (CommonUtil.isNull(isLocalhost).equals("local")){
            isZxFlag = false;  // 本地不执行
        }

        for (CarInfo vo : carList) {
            String carNo = CommonUtil.isNull(vo.getCarNo());
            String key = Constants.car_curent_trail + carNo;
            TrailInfo trailInfo = redisCache.getCacheObject(key);

            CarInfo car = new CarInfo();
            car.setId(vo.getId());

            if (null != trailInfo){
                ZdataTrailTracks tracksBo = trailInfo.getTracks(); // 轨迹对象
                String pointUuid = CommonUtil.isNull(tracksBo.getUuid()); // 当前轨迹点
                List<TrailBo> josnList = trailInfo.getTrailList(); // 轨迹李四
                if (null != josnList && josnList.size() > 0) {
                    List<TrailBo> stationList = new ArrayList<TrailBo>(); // 收费站
                    boolean trailExits = false;  // 轨迹点是否存在
                    // 在线增加判断是否有出的话 true=进入，false=驶出 directionIn
                    for (TrailBo trailBo : josnList) {
                        if (null != trailBo.getLon() && null != trailBo.getLat()) {
                            trailExits = true;
                        }
                        String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
                        switch (stateType) {
                            case Constants.BORDER_WEIGHING_CAPTURE:
                                // 省界称重
                                break;
                            case Constants.GANTRY_CAPTURE:
                                // 门架抓拍
                                break;
                            case Constants.PROV_CAPTURE:
                                // 省界抓拍
                                break;
                            case Constants.SERVICE_AREA_CAPTURE:
                                // 服务区抓拍
                                break;
                            case Constants.STATION_CAPTURE:
                                // 收费站抓拍
                                stationList.add(trailBo);
                                break;
                        }
                    }

                    //  收费站---------------
                    Boolean inFlag = false;
                    Boolean outFlag = false;
                    for (int i = 0; i < stationList.size(); i++) {
                        TrailBo trailBo = stationList.get(i);
                        Boolean directionIn = trailBo.getDirectionIn();
                        if (null != directionIn && directionIn){
                            inFlag = true;
                        }
                        // 最后一个收费站
                        if (i == stationList.size() - 1) {
                            if (null != directionIn && !directionIn){
                                // 是使出
                                outFlag = true;
                            }

                        }
                    }

                    if (inFlag && outFlag && isZxFlag){
                        // 跟新车俩-----------------------  车的状态修改status 0
                        car.setStatus("0");
                        car.setTrackJosn(null);
                    }else{
                        if (trailExits){
                            // 车的状态修改更新为 status 1  经纬度 last_pass_longitude  last_pass_latitude  josn字符串要更新 track_id track_josn
                            // 车的门架 路段 等数据--------------
                            // 同事要跟新车俩预警  car_warning_info
                            // 进度和维度
                            TrailBo lastBo = null;

                            String devCodes = "";  // 设备所有的集合
                            for (TrailBo trailBo : josnList) {

                                String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
                                // 抓拍设备
                                if (CommonUtil.isNotBlank(trailBo.getDevCode())) {
                                    devCodes += stateType + ":" + trailBo.getDevCode() + ",";
                                }
                                // 路线
                                if (CommonUtil.isNotBlank(trailBo.getRoadCode())) {
                                    String roadKey = "roadCode:" + trailBo.getRoadCode();
                                    if (devCodes.indexOf(roadKey) > -1) {
                                    } else {
                                        devCodes += roadKey + ",";
                                    }
                                }
                                // 路段
                                if (CommonUtil.isNotBlank(trailBo.getSectionCode())) {
                                    String sectionKey = "sectionCode:" + trailBo.getSectionCode();
                                    if (devCodes.indexOf(sectionKey) > -1) {
                                    } else {
                                        devCodes += sectionKey + ",";
                                    }
                                }

                                if (stateType.equals(Constants.BORDER_WEIGHING_CAPTURE)
                                        || stateType.equals(Constants.GANTRY_CAPTURE)
                                        || stateType.equals(Constants.PROV_CAPTURE)
                                        || stateType.equals(Constants.SERVICE_AREA_CAPTURE)
                                        || stateType.equals(Constants.STATION_CAPTURE)
                                ){
                                    if (null != trailBo.getLon() && null != trailBo.getLat() && CommonUtil.isNotBlank(trailBo.getDevCode())) {
                                        lastBo = trailBo;
                                    }
                                }
                            }

                            if (null != lastBo){
                                car.setStatus("1");
                                if (null != lastBo.getLon()) {
                                    car.setLastPassLongitude(CommonUtil.isNull(lastBo.getLon()));
                                }

                                if (null != lastBo.getLat()) {
                                    car.setLastPassLatitude(CommonUtil.isNull(lastBo.getLat()));
                                }
                                car.setTrackJosn(JSON.toJSON(josnList) + "");
                                car.setGantryCode(CommonUtil.deleteEnd(devCodes));

                                // 预警信息
                                CarWarningInfo carWarningInfo = new CarWarningInfo();
                                carWarningInfo.setCarId(vo.getId());
                                carWarningInfo.setCarNo(vo.getCarNo());
                                carWarningInfo.setCarType(vo.getCarType());
                                carWarningInfo.setCarVehicle(vo.getCarVehicle());
                                carWarningInfo.setCarNum(vo.getCarNum());

                                carWarningInfo.setTrackId(pointUuid);
                                carWarningInfo.setTrackJosn(JSON.toJSON(josnList) + "");
                                carWarningInfo.setTrackNames(CommonUtil.deleteEnd(devCodes));

                                // 入站
                                carWarningInfo.setInStationId(tracksBo.getFirtStationCode());
                                carWarningInfo.setInStation(tracksBo.getFirtStationName());
                                if (CommonUtil.isNotBlank(tracksBo.getFirtStationTime())){
                                    carWarningInfo.setInTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,tracksBo.getFirtStationTime()));
                                }


                                // 抓拍设备
                                if (CommonUtil.isNotBlank(lastBo.getDevCode())){

                                    carWarningInfo.setGantryStationId(lastBo.getDevCode());
                                    carWarningInfo.setGantrytStation(lastBo.getDevName());
                                    if (CommonUtil.isNotBlank(lastBo.getCaptureTime())){
                                        carWarningInfo.setGantryTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,lastBo.getCaptureTime()));
                                    }
                                    carWarningInfo.setFileIds(CommonUtil.isNull(lastBo.getImagesArry()));

                                    // 预计下一个通行时间nextPassTime  预计下一个通行地址 nextPassAddress

                                    carWarningInfo.setDelFlag("0");
                                    carWarningInfo.setCreateBy(userId); // 创建人
                                    carWarningInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                                    carWarningInfo.setUpdateBy(userId); // 更新人
                                    carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
                                    carWarningInfo.setRoadCode(lastBo.getRoadCode()); // 路线

                                    if (CommonUtil.isNotBlank(pointUuid)){
                                        delCarWarningInfoList.add(pointUuid);
                                    }
                                    addCarWarningInfoList.add(carWarningInfo);
                                }
                            }else{
                                // 跟新车俩-----------------------  车的状态修改status 0
                                car.setStatus("0");
                                car.setTrackJosn(null);
                            }
                        }else{
                            // 跟新车俩-----------------------  车的状态修改status 0
                            car.setStatus("0");
                            car.setTrackJosn(null);
                        }
                    }
                }else{
                    // 跟新车俩-----------------------  车的状态修改status 0
                    car.setStatus("0");
                    car.setTrackJosn(null);
                }
            }else{
                // 跟新车俩-----------------------  车的状态修改status 0
                car.setStatus("0");
                car.setTrackJosn(null);
            }
            updatalist.add(car);
        }

        // 修改
        if (updatalist.size() > 0) {
            carInfoService.updateBatchById(updatalist);
            // 更新缓存
            carInfoService.updateRedisCarList();
        }

        // 生成车俩预警信息
        if (delCarWarningInfoList.size() > 0) {
            carWarningInfoService.deleteCarWarningInfoByUUid(delCarWarningInfoList);
        }

        if (addCarWarningInfoList.size() > 0) {
            // 预计下一个通行时间nextPassTime  预计下一个通行地址 nextPassAddress
            for (int zz = 0; zz < addCarWarningInfoList.size(); zz++) {
                CarWarningInfo addbo = addCarWarningInfoList.get(zz);

                String carNo = CommonUtil.isNull(addbo.getCarNo());
                String nextKey = Constants.car_history_trail + carNo;
                // 当前进入门架的时间-----------------------
                String gantryStationId = CommonUtil.isNull(addbo.getGantryStationId());
                Date gantryTime = addbo.getGantryTime();

                List<TrailInfo> trailInfoList = redisCache.getCacheObject(nextKey);
                List<TrailBo> nextBoList = new ArrayList<>();
                if (null != trailInfoList && trailInfoList.size() > 0) {
                    // 找到下一个位置
                    for (TrailInfo trailInfo : trailInfoList) {
                        // ZdataTrailTracks tracksBo = trailInfo.getTracks();
                        List<TrailBo> trailList = trailInfo.getTrailList();
                        // 循环轨迹
                        if (null != trailList && trailList.size() > 0) {
                            for (int yy = 0; yy < trailList.size(); yy++) {
                                TrailBo trailBo = trailList.get(yy);
                                String curDevCode = CommonUtil.isNull(trailBo.getDevCode());
                                String curCaptureTime = trailBo.getCaptureTime();
                                if (gantryStationId.equals(curDevCode)) {
                                    // 判断有下一个:不是最后一个
                                    if (yy != trailList.size() - 1) {
                                        TrailBo nextTrailBo = trailList.get(yy + 1);
                                        nextTrailBo.setPreCaptureTime(curCaptureTime);
                                        nextBoList.add(nextTrailBo);
                                    }
                                }
                            }
                        }
                    }
                }
                if (nextBoList.size() > 0) {
                    // 找到最后一条记录
                    Map<String, Integer> countMap = new HashMap<>();
                    for (TrailBo nextbo : nextBoList) {
                        String curDevCode = CommonUtil.isNull(nextbo.getDevCode());
                        if (countMap.containsKey(curDevCode)) {
                            countMap.put(curDevCode, countMap.get(curDevCode) + 1);
                        } else {
                            countMap.put(curDevCode, 1);
                        }
                    }

                    for (TrailBo nextbo : nextBoList) {
                        String curDevCode = CommonUtil.isNull(nextbo.getDevCode());
                        if (countMap.containsKey(curDevCode)) {
                            nextbo.setCountNum(countMap.get(curDevCode));
                        } else {
                            nextbo.setCountNum(0);
                        }
                    }

                    // 按照先countNum排序 然后按照抓拍时间
                    nextBoList = nextBoList.stream().sorted(
                            Comparator.comparing(TrailBo::getCountNum).reversed().thenComparing(TrailBo::getCaptureTime).reversed()
                    ).collect(Collectors.toList());

                    TrailBo lastTrailBo = nextBoList.get(0);

                    addbo.setNextPassAddress(lastTrailBo.getDevName());

                    String curCaptureTime = lastTrailBo.getCaptureTime();
                    String preCaptureTime = lastTrailBo.getPreCaptureTime();

                    if (null != gantryTime && CommonUtil.isNotBlank(curCaptureTime) && CommonUtil.isNotBlank(preCaptureTime)) {
                        Date date1 = DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS, curCaptureTime);
                        Date date2 = DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS, preCaptureTime);
                        long difTime = gantryTime.getTime() + date1.getTime() - date2.getTime();
                        Date dateLast = new Date(difTime);
                        /* SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");*/
                        addbo.setNextPassTime(dateLast);
                    }
                }

            }
            carWarningInfoService.saveBatch(addCarWarningInfoList);
        }

        // 更新缓存。。。。。。。。。。。。
        carWarningInfoService.updateRedisWarningList();

        return AjaxResult.success();
    }

    @Override
    public List<Geometry> getCarGeometry(List<TrailBo> josnList) {
        List<Geometry> raodTrailList = new ArrayList<>();
        LinkedHashMap<String, List<TrailBo>> collect =
                josnList.stream().filter(o -> StrUtil.isNotEmpty(o.getPileno()))
                        .peek(o -> {
                            String pileno = o.getPileno();
                            pileno = pileno.replace("+", ".").replace("ZK", "").replace("YK", "").replace("K", "");
                            log.info("原始桩号{}变化后桩号{}", o.getPileno(), pileno);
                            o.setPileno(pileno);
                        })
                        .collect(Collectors.groupingBy(TrailBo::getRoadCode, LinkedHashMap::new, Collectors.toList()));
        AtomicInteger index = new AtomicInteger(0);
        collect.forEach((k, v) -> {
            LambdaQueryWrapper<Geometry> l = new LambdaQueryWrapper<>();
            Optional<Integer> min = v.stream().map(o -> new BigDecimal(o.getPileno()).intValue()).min(Integer::compare);
            Optional<Integer> max = v.stream().map(o -> new BigDecimal(o.getPileno()).intValue()).max(Integer::compare);
            if(min.isPresent()) {
                log.info("路线{}起始桩号{}终点桩号{}", k, min.get(), max.get());
                l.eq(Geometry::getLxbh, k).eq(Geometry::getLxfx, "1");
                if(min.get().equals(max.get()))
                {
                    l.eq(Geometry::getQdzh, min.get());
                }
                else {
                    l.lt(Geometry::getQdzh, max.get()).ge(Geometry::getQdzh, min.get());
                }

                List<Geometry> list = geometryService.list(l);
                Geometry geometry = new Geometry();
                JSONArray paths = new JSONArray();
                geometry.setLxbh(k);
                geometry.setQdzh(min.get());
                geometry.setZdzh(max.get()+1);
                List<TrailBo> station = v.stream().filter(o -> "StationCapture".equals(o.getStateType())).filter(o -> null != o.getLon() && null != o.getLat()).collect(Collectors.toList());
                // 起点收费站
                JSONArray stationPaths = new JSONArray();
                // 终点收费站
                JSONArray stationPaths2 = new JSONArray();
                if(!station.isEmpty()) {
                    TrailBo trailBo = station.get(0);
                    stationPaths.add(trailBo.getLon());
                    stationPaths.add(trailBo.getLat());
                    if(station.size() > 1)
                    {
                        trailBo = station.get(station.size() - 1);
                        stationPaths2.add(trailBo.getLon());
                        stationPaths2.add(trailBo.getLat());
                    }
                }
                int i = index.getAndIncrement();
                if(0 == i && !stationPaths.isEmpty())
                {
                    paths.add(stationPaths);
                }

                list.forEach(o -> {
                    JSONArray objects = JSONUtil.parseArray(o.getPaths());
                    paths.addAll(objects);
                });
                /*
                 * 判断一条路线有多个收费站时候，该条路线最后一个收费站是终点收费站；
                 * 多条路线则终点收费站是改路线的第一个收费站
                 */
                if(i == 0 && station.size() > 1)
                {
                    paths.add(stationPaths2);
                }
                else if(0 != i && !stationPaths.isEmpty())
                {
                    paths.add(stationPaths);
                }
                geometry.setPaths(paths.toString());
                raodTrailList.add(geometry);

            }
        });
        return raodTrailList;
    }


}
