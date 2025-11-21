package com.ruoyi.manager.service.impl;


import cn.hutool.json.JSONArray;
import cn.hutool.json.JSONUtil;
import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.IRoadPathService;
import com.ruoyi.base.service.IZdataTrailTracksService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.base.util.GpsUtil;
import com.ruoyi.base.util.LonLatPathsUtils;
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
import java.math.RoundingMode;
import java.text.SimpleDateFormat;
import java.util.*;
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

    @Autowired
    private IZdataTrailTracksService trailTracksService;

    @Resource
    private LonLatPathsUtils lonLatPathsUtils;
    @Autowired
    private IRoadPathService roadPathService;

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
            // 跟新车俩-----------------------  车的状态修改status 0
            car.setStatus("0");
            car.setTrackJosn(null);

            if (null != trailInfo){
                ZdataTrailTracks tracksBo = trailInfo.getTracks(); // 轨迹对象
                String pointUuid = CommonUtil.isNull(tracksBo.getUuid()); // 当前轨迹点：车辆+时间  carNo +"@@"+ formattedDate
                List<TrailBo> josnList = trailInfo.getTrailList(); // 轨迹李四
                if (null != josnList && josnList.size() > 0) {
                    List<TrailBo> stationList = new ArrayList<TrailBo>(); // 收费站
                    TrailBo firstStation = new TrailBo(); // 第一个收费站或者门架-------------

                    boolean trailExits = false;  // 轨迹点是否存在
                    // 在线增加判断是否有出的话 true=进入，false=驶出 directionIn
                    int fristCountNum = 0;
                    String captureTimeLast = "";  // 最后抓拍时间
                    boolean isExitFlag = true; // 是否离开
                    for (TrailBo trailBo : josnList) {
                        if (null != trailBo.getLon() && null != trailBo.getLat()) {
                            trailExits = true;
                        }

                        String captureTime = CommonUtil.isNull(trailBo.getCaptureTime());
                        if (CommonUtil.isNotBlank(captureTime)){
                            captureTimeLast = captureTime;
                        }
                        String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
                        switch (stateType) {
                            case Constants.BORDER_WEIGHING_CAPTURE:
                                // 省界称重
                                if (fristCountNum ==0){
                                    firstStation = trailBo;
                                    fristCountNum++;
                                }
                                break;
                            case Constants.GANTRY_CAPTURE:
                                // 门架抓拍
                                break;
                            case Constants.PROV_CAPTURE:
                                // 省界抓拍
                                if (fristCountNum ==0){
                                    firstStation = trailBo;
                                    fristCountNum++;
                                }
                                break;
                            case Constants.SERVICE_AREA_CAPTURE:
                                // 服务区抓拍
                                break;
                            case Constants.STATION_CAPTURE:
                                // 收费站抓拍
                                if (fristCountNum ==0){
                                    firstStation = trailBo;
                                    fristCountNum++;
                                }
                                stationList.add(trailBo);
                                break;
                        }
                    }

                    //  收费站---------------
                   /* Boolean inFlag = false;
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
                    }*/

                    //  判断在线最后一个节点时间
                    try {
                        SimpleDateFormat format2 = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                        long threeMinutesInMillis = 60 * 60 * 1000; // 60分钟转换为毫秒
                        if (CommonUtil.isNotBlank(captureTimeLast)){
                            Date captureTimeDate1 = format2.parse(captureTimeLast);
                            Date curDate = new Date();
                            long diff = Math.abs(curDate.getTime() - captureTimeDate1.getTime());
                            if (diff < threeMinutesInMillis) {
                                isExitFlag = false;
                            }
                        }

                    } catch (Exception e) {

                        log.info("日期解析失败------------" + e.toString());
                    }


                    if (isExitFlag && isZxFlag){
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

                            TrailBo lastMjBo = null;

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

                              /*  if (stateType.equals(Constants.BORDER_WEIGHING_CAPTURE)
                                        || stateType.equals(Constants.GANTRY_CAPTURE)
                                        || stateType.equals(Constants.PROV_CAPTURE)
                                        || stateType.equals(Constants.SERVICE_AREA_CAPTURE)
                                        || stateType.equals(Constants.STATION_CAPTURE)
                                ){

                                }*/
                                if (null != trailBo.getLon() && null != trailBo.getLat() && CommonUtil.isNotBlank(trailBo.getDevCode())) {
                                    lastBo = trailBo;
                                }


                               /* if (stateType.equals(Constants.GANTRY_CAPTURE)){
                                }*/

                                if (null != trailBo.getLon() && null != trailBo.getLat() && CommonUtil.isNotBlank(trailBo.getDevCode())) {
                                    lastMjBo = trailBo;
                                }

                            }

                            // 车辆实时位置
                            if (null != lastBo){
                                car.setStatus("1");
                                if (null != lastBo.getLon()) {
                                    car.setLastPassLongitude(CommonUtil.isNull(lastBo.getLon()));
                                }

                                if (null != lastBo.getLat()) {
                                    car.setLastPassLatitude(CommonUtil.isNull(lastBo.getLat()));
                                }
                                car.setTrackJosn(JSON.toJSON(trailInfo) + "");
                                car.setGantryCode(CommonUtil.deleteEnd(devCodes));
                            }

                            // 最后一个经过门架
                            if (null != lastMjBo) {
                                // 预警信息
                                CarWarningInfo carWarningInfo = new CarWarningInfo();
                                carWarningInfo.setCarId(vo.getId());
                                carWarningInfo.setCarNo(vo.getCarNo());
                                carWarningInfo.setCarType(vo.getCarType());
                                carWarningInfo.setCarVehicle(vo.getCarVehicle());
                                carWarningInfo.setCarNum(vo.getCarNum());

                                carWarningInfo.setTrackId(pointUuid);
                                carWarningInfo.setTrackJosn(JSON.toJSON(lastMjBo) + "");
                                carWarningInfo.setTrackNames(CommonUtil.deleteEnd(devCodes));

                                // 入站
                                carWarningInfo.setInStationId(CommonUtil.isNull(firstStation.getDevCode()));
                                carWarningInfo.setInStation(CommonUtil.isNull(firstStation.getDevName()));
                                if (CommonUtil.isNotBlank(firstStation.getCaptureTime())){
                                    carWarningInfo.setInTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,firstStation.getCaptureTime()));
                                }

                                // 抓拍设备
                                if (CommonUtil.isNotBlank(lastMjBo.getDevCode())){

                                    carWarningInfo.setGantryStationId(lastMjBo.getDevCode());
                                    carWarningInfo.setGantrytStation(lastMjBo.getDevName());
                                    if (CommonUtil.isNotBlank(lastMjBo.getCaptureTime())){
                                        carWarningInfo.setGantryTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,lastMjBo.getCaptureTime()));
                                    }
                                    carWarningInfo.setFileIds(CommonUtil.isNull(lastMjBo.getImagesArry()));

                                    // 预计下一个通行时间nextPassTime  预计下一个通行地址 nextPassAddress

                                    carWarningInfo.setDelFlag("0");
                                    carWarningInfo.setCreateBy(userId); // 创建人
                                    carWarningInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                                    carWarningInfo.setUpdateBy(userId); // 更新人
                                    carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
                                    carWarningInfo.setRoadCode(lastMjBo.getRoadCode()); // 路线
                                    carWarningInfo.setSectionCode(lastMjBo.getSectionCode());


                                    if (CommonUtil.isNotBlank(pointUuid)){
                                        delCarWarningInfoList.add(pointUuid);
                                    }

                                    SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
                                    String formattedDate = sdf.format(new Date());
                                    carWarningInfo.setBackCol1(formattedDate);
                                    if (pointUuid.indexOf("@@") > -1){
                                        String[] pointUuidStr = pointUuid.split("@@");
                                        if (pointUuidStr.length > 1){
                                            carWarningInfo.setBackCol1(pointUuidStr[1]);
                                        }
                                    }

                                    addCarWarningInfoList.add(carWarningInfo);
                                }
                            }
                        }
                    }
                }
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
                    nextBoList = nextBoList.stream().sorted(Comparator.comparing(TrailBo::getCountNum).reversed()
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


    /**
     * 轨迹同步：历史轨迹
     *
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncHistoryTrack() {
        // 查询所有的车俩
        List<CarInfo> carList = carInfoService.getRedisCarList();
        this.saveTrailTracksHistory(carList);
        return AjaxResult.success();
    }

    /**
     * 轨迹同步：历史轨迹
     *
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncHistoryTrackNoCar() {
        // 查询所有的车俩
        CarInfo carInfo = new CarInfo();
        carInfo.setFlag("noTrack");
        List<CarInfo> carList = carInfoService.selectCarInfoList(carInfo);
        this.saveTrailTracksHistory(carList);
        return AjaxResult.success();
    }

    private void saveTrailTracksHistory(List<CarInfo> carList){
        List<String> carNoList = new ArrayList<>();
        // 找到下一个位置
        List<ZdataTrailTracks> addlist = new ArrayList<>();
        for (CarInfo vo : carList) {
            String carNo = CommonUtil.isNull(vo.getCarNo());
            String key = Constants.car_history_trail + carNo;
            List<TrailInfo> trailInfoList = redisCache.getCacheObject(key);
            if (null != trailInfoList && trailInfoList.size() > 0) {
                for (TrailInfo trailInfo : trailInfoList) {
                    ZdataTrailTracks tracksBo = trailInfo.getTracks();
                    List<TrailBo> trailList = trailInfo.getTrailList(); // trailPoints
                    tracksBo.setPlateKey(carNo);
                    tracksBo.setPointCount(0L);
                    if (null !=trailList){
                        tracksBo.setTrackJosn(JSON.toJSONString(trailList));
                        tracksBo.setPointCount(Long.parseLong(trailList.size()+""));
                    }
                    carNoList.add(carNo);
                    addlist.add(tracksBo);
                }
            }
        }
        if (carNoList.size() > 0){
            trailTracksService.removeRealData(carNoList);
        }
        if (addlist.size()>0){
            trailTracksService.saveBatch(addlist);
        }
    }


    /**
     * 根据桩号转换轨迹经纬度
     * @param josnList
     * @return
     */
    @Override
    public List<Geometry> getCarGeometry(ZdataTrailTracks tracksBo,List<TrailBo> josnList) {

        if (null == tracksBo){
            tracksBo = new ZdataTrailTracks();
        }

        List<Geometry> raodTrailList = new ArrayList<>();
        // 去掉重复的桩号
        LinkedHashMap<String,List<TrailBo>> map = new LinkedHashMap<>(2);

        for (TrailBo trailBo : josnList) {
            String roadCode =  CommonUtil.isNull(trailBo.getRoadCode()); // 路线编号
            String pileno = CommonUtil.isNull(trailBo.getPileno()); // 桩号
            if (CommonUtil.isNotBlank(roadCode) && CommonUtil.isNotBlank(pileno)){
                String changPileno = pileno.replace("+", ".").replace("ZK", "").replace("YK", "").replace("K", "");
                // log.info("原始桩号{}变化后桩号{}",pileno, changPileno);
                trailBo.setPilenoDec(new BigDecimal(changPileno));
                List<TrailBo> roadCodeList = new ArrayList<>();
                if (map.containsKey(roadCode)){
                    roadCodeList = map.get(roadCode);
                }
                roadCodeList.add(trailBo);
                map.put(roadCode,roadCodeList);
            }
        }

        Map<String, List<Geometry>> roadMap = geometryService.getRedisList();

        // 循环Map
        for (Map.Entry<String, List<TrailBo>> entry : map.entrySet()) {
            String roadCode = entry.getKey();  // 路线
            List<TrailBo> trailBoList = entry.getValue(); // 轨迹点

            int reserver = 0;
            if(null !=trailBoList && trailBoList.size() >0){
                BigDecimal pilenoDec1 = trailBoList.get(0).getPilenoDec();
                BigDecimal pilenoDec2 = trailBoList.get(trailBoList.size() - 1).getPilenoDec();
                if(pilenoDec1.compareTo(pilenoDec2) > 0)
                {
                    reserver = 1;
                }

                // 按照桩号排序----------
                trailBoList =  trailBoList.stream().sorted(Comparator.comparing(TrailBo::getPilenoDec))
                        .collect(Collectors.toList());

                Geometry geometryQuery = new Geometry();

                //--------------起点
                BigDecimal bigDecimalFirst = trailBoList.get(0).getPilenoDec();
                int sq = bigDecimalFirst.setScale(4, RoundingMode.HALF_UP).intValue(); // 舍入到最接近的整数
                int sz = 0;
                if (trailBoList.size() > 1){
                    // ------------终点
                    BigDecimal bigDecimalEnd = trailBoList.get(trailBoList.size() -1).getPilenoDec();
                    sz = bigDecimalEnd.setScale(4, RoundingMode.HALF_UP).intValue() + 1; // 舍入到最接近的整数
                }else {
                    sz = sq;
                }

                // log.info("路线{}起点桩号{}终点桩号{}",geometryQuery.getLxbh(), geometryQuery.getQdzh(),geometryQuery.getZdzh());

                // https://blog.csdn.net/wangwuyilove/article/details/42875475
                // ”用qd表示，“终点”用zd表示，输起用“sq”表示，“输终”用sz表示。
                // 首先第一种情况他的sql我们经常写，qd<=sq && zd >= sz
                // 第二种情况那其实就是数据库记录的起点数值在输入数值的中间，也就是 qd > sq && qd < sz
                // 第三种情况和第二种类似，就是 zd > sq && zd < sz
                // 第四种情况就是输入的数值包含了数据库记录的区间数值，也就是 qd >= sq && zd <= sz

                List<Geometry> addlist = new ArrayList<>(); // 重缓存种查询到符合的值


                List<Geometry> filtlist = roadMap.get(roadCode);
                if (null != filtlist && filtlist.size() > 0) {
                    // 如果有数据
                    for (Geometry filtbo : filtlist) {
                        int qd = 0;
                        int zd = 0;
                        if (null != filtbo.getQdzh()) {
                            qd = filtbo.getQdzh();
                        }

                        if (null != filtbo.getZdzh()) {
                            zd = filtbo.getZdzh();
                        }

                        int countNum = 0;
                        if (qd <= sq && zd >= sz) {
                            countNum++;
                        }

                        if (qd > sq && qd < sz) {
                            countNum++;
                        }

                        if (zd > sq && zd < sz) {
                            countNum++;
                        }

                        if (qd >= sq && zd <= sz) {
                            countNum++;
                        }

                        if (countNum > 0){
                            addlist.add(filtbo);
                        }
                    }
                }



                if (null !=addlist && addlist.size() > 0){
                    // 把路线所有的轨迹点拼接出来
                    Geometry rtnGeometry = new Geometry();
                    rtnGeometry.setLxbh(roadCode);
                    JSONArray pathsJSONArray = new JSONArray();
                    for (Geometry queryGeometry : addlist) {
                        String paths =  queryGeometry.getPaths();
                        if (CommonUtil.isNotBlank(paths)){
                            JSONArray objects = JSONUtil.parseArray(paths);
                            pathsJSONArray.addAll(objects);
                        }
                    }
                    if(reserver == 1)
                    {
                        Collections.reverse(pathsJSONArray);
                    }
                    rtnGeometry.setPaths(pathsJSONArray.toString());
                    raodTrailList.add(rtnGeometry);
                }
            }
        }
        return raodTrailList;
    }

    /**
     * 根据桩号转换轨迹经纬度
     * @param josnList
     * @return
     */
    @Override
    public TrailDevCountBO getTrailDevBO(ZdataTrailTracks tracks,List<TrailBo> josnList){

        if (null == tracks){
            tracks = new ZdataTrailTracks();
        }

        TrailDevCountBO trailDevCountBO = new TrailDevCountBO();
        Integer exceptNum = 0;
        List<TrailDevBO> TrailDevList = new ArrayList<>();
        String  exceptMsg = "";

        Map<String,List<TrailBo>> map = new HashMap<>();
        List<TrailBo> rtnList = new ArrayList<>();

        for (TrailBo trailBo : josnList) {
            String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
            String devName = CommonUtil.isNull(trailBo.getDevName());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
            if (stateType.equals(Constants.GANTRY_CAPTURE) || stateType.equals(Constants.FeeRecord)) {
                // 门架抓拍  门架流水
                if (CommonUtil.isNotBlank(devName)) {
                    List<TrailBo> templist = new ArrayList<>();
                    if (map.containsKey(devName)) {
                        templist = map.get(devName); // 重复的对象合并
                    }else{
                        rtnList.add(trailBo); // 去掉重复的
                    }
                    templist.add(trailBo);
                    map.put(devName, templist);
                } else {
                    rtnList.add(trailBo);
                }
            }else{
                rtnList.add(trailBo);
            }
        }

        for (TrailBo trailBo : rtnList) {
            TrailDevBO trailDevBO = new TrailDevBO();
            String stateType = CommonUtil.isNull(trailBo.getStateType());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
            String devName = CommonUtil.isNull(trailBo.getDevName());  // 流水来源类型标识:可作为维度字段，用于回溯数据来源、确定查找目标表
            trailDevBO.setStatus("0");  // 默认为正常
            List<TrailBo> trailList = new ArrayList<>();

            if (stateType.equals(Constants.GANTRY_CAPTURE) || stateType.equals(Constants.FeeRecord)) {
                if(map.containsKey(devName)){
                    trailList = map.get(devName);
                    // 判断异常数量
                    int conutGantryCapture = 0;
                    int conutFeeRecord = 0;
                    for (TrailBo rtnTrailBo : trailList) {
                        String stateTypeDif = CommonUtil.isNull(rtnTrailBo.getStateType());
                        if (stateTypeDif.equals(Constants.GANTRY_CAPTURE)) {
                            // 门架抓拍
                            conutGantryCapture++;
                        } else if (stateTypeDif.equals(Constants.FeeRecord)) {
                            // 卡口流水
                            conutFeeRecord++;
                        }
                    }
                    if (conutGantryCapture > 0 && conutFeeRecord == 0) {
                        trailDevBO.setStatus("1");  // 异常数据
                        exceptNum++;
                    }
                }else{
                    trailList.add(trailBo);
                }
            }else{
                trailList.add(trailBo);
            }
            trailDevBO.setDevName(devName);
            trailDevBO.setTrailList(trailList);
            TrailDevList.add(trailDevBO);
        }
        trailDevCountBO.setExceptNum(exceptNum);
        trailDevCountBO.setTrailDevList(TrailDevList);
        trailDevCountBO.setTrailList(josnList);

        String tips = "";
        if (null == tracks.getStartLonDec() || null == tracks.getStratLatDec()) {
            tips = "起始位置";
        }

        if (null == tracks.getEndLonDec() || null == tracks.getEndLatDec()) {
            if (tips.equals("")) {
                tips = "终点位置";
            } else {
                tips = tips + "和终点位置";
            }
        }


        if (CommonUtil.isNotBlank(tips) ){
            exceptMsg = "由于无法获取轨迹"+tips+"，系统路线规划采用已有的轨迹点进行轨迹绘制，可能会导致部分路线丢失。";
        }


        trailDevCountBO.setExceptMsg(exceptMsg);

        return trailDevCountBO;
    }

    /**
     * 根据桩号转换轨迹经纬度：先通过腾讯API转换
     * @param josnList
     * @return
     */
    @Override
    public List<Geometry> getCarGeometryByPlan(ZdataTrailTracks tracksBo, List<TrailBo> josnList) {
        if (null == tracksBo){
            tracksBo = new ZdataTrailTracks();
        }

        if (null == tracksBo.getStartLonDec() || null == tracksBo.getStratLatDec() ||
                null == tracksBo.getEndLonDec() || null == tracksBo.getEndLatDec())
        {
            log.info("起始和终点位置不存在-----------");
            return this.getCarGeometry(tracksBo,josnList);
        }
        else {

            String key = Constants.car_lxgh + CommonUtil.isNull(tracksBo.getPlateKey()) + CommonUtil.isNull(tracksBo.getStartLonDec())
                    + CommonUtil.isNull(tracksBo.getStratLatDec())  + CommonUtil.isNull(tracksBo.getEndLonDec()) + CommonUtil.isNull(tracksBo.getEndLatDec())
                    +josnList.size();

            String lxbh = "";
            StringBuilder wayPoints = new StringBuilder();
            for (TrailBo trailBo : josnList) {
                if (null != trailBo.getLon() && null != trailBo.getLat()) {
                    double lon = trailBo.getLon().doubleValue();
                    double lat = trailBo.getLat().doubleValue();
                    String roadCode = trailBo.getRoadCode();
                    if("".equals(lxbh) && !"".equals(roadCode))
                    {
                        lxbh = roadCode;
                    }

                    double[] doubles = GpsUtil.gps84_To_Gcj02(lat, lon);
                    if(wayPoints.length() > 0)
                    {
                        wayPoints.append(";");
                    }
                    wayPoints.append(doubles[0]).append(",").append(doubles[1]);
                }
            }
            String paths = "";

            Object obj = redisCache.getCacheObject(key);
            if (null != obj) {
                paths = CommonUtil.isNull(obj);
            }else{
                paths = lonLatPathsUtils.calcLonAndLatPaths(tracksBo.getStartLonDec().toPlainString(), tracksBo.getStratLatDec().toPlainString(),
                        tracksBo.getEndLonDec().toPlainString(), tracksBo.getEndLatDec().toPlainString(), "", wayPoints.toString());
                if(null != paths){
                    redisCache.setCacheObject(key,paths);
                }
            }



            Geometry rtnGeometry = new Geometry();
            if(null == paths)
            {
                log.info("调用腾讯地图API找不到位置不存在-----------");
                return this.getCarGeometry(tracksBo,josnList);
            }
            rtnGeometry.setLxbh(lxbh);
            rtnGeometry.setPaths(paths);
            List<Geometry> rtn = new ArrayList<>();
            rtn.add(rtnGeometry);
            return rtn;
        }
    }

    /**
     * 根据桩号转换轨迹经纬度：先通过本身的API
     * @param josnList
     * @return
     */
    @Override
    public List<Geometry> getCarGeometryByPlanNew(ZdataTrailTracks tracksBo, List<TrailBo> josnList) {
        if (null == tracksBo){
            tracksBo = new ZdataTrailTracks();
        }

        List<String> nodeIds = new ArrayList<>();

        if (CommonUtil.isNotBlank(tracksBo.getEntollstationid()) && CommonUtil.isNotBlank(tracksBo.getExtollstationid()))
        {
            nodeIds.add(tracksBo.getEntollstationid());  // 起点

            String key = Constants.car_lxgh + CommonUtil.isNull(tracksBo.getPlateKey()) + CommonUtil.isNull(tracksBo.getEntollstationid())
                    + CommonUtil.isNull(tracksBo.getExtollstationid()) + josnList.size();

            String lxbh = "";
            for (TrailBo trailBo : josnList) {
                String roadCode = trailBo.getRoadCode();
                if("".equals(lxbh) && !"".equals(roadCode))
                {
                    lxbh = roadCode;
                }
                if (CommonUtil.isNotBlank(trailBo.getDevCode())) {
                    nodeIds.add(trailBo.getDevCode());  // 中间的轨迹点
                }
            }
            nodeIds.add(tracksBo.getExtollstationid()); // 终点

            String paths = "";

            Object obj = redisCache.getCacheObject(key);
            if (null != obj) {
                paths = CommonUtil.isNull(obj);
            } else {
                paths = roadPathService.getShortestRoadPath(nodeIds);
                if(null != paths) {
                    log.info("调用本地API获取path-----------");
                    redisCache.setCacheObject(key,paths);
                }
            }


            Geometry rtnGeometry = new Geometry();
            if(null == paths)
            {
                log.info("调用本地API找不到位置不存在-----------");
                return this.getCarGeometryByPlan(tracksBo,josnList);
            }
            rtnGeometry.setLxbh(lxbh);
            rtnGeometry.setPaths(paths);
            List<Geometry> rtn = new ArrayList<>();
            rtn.add(rtnGeometry);
            return rtn;
        }
        else {
            log.info("起始和终点位置不存在-----------");
            return this.getCarGeometryByPlan(tracksBo,josnList);
        }
    }

}
