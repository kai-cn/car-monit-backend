package com.ruoyi.manager.service.impl;

import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.*;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.*;
import com.ruoyi.manager.mapper.CarInfoMapper;
import com.ruoyi.manager.mapper.CarSuspiciousMapper;
import com.ruoyi.manager.service.*;
import com.ruoyi.system.service.ISysDictDataService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 可疑车辆Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarSuspiciousServiceImpl extends ServiceImpl<CarSuspiciousMapper, CarSuspicious> implements ICarSuspiciousService {

    @Autowired
    private CarSuspiciousMapper carSuspiciousMapper;

    @Autowired
    private CarInfoMapper carInfoMapper;

    @Autowired
    private ICarSuspiciousCheckService carSuspiciousCheckService;

    @Autowired
    private ICarExceptRecordService carExceptRecordService;

    @Autowired
    private RedisCache redisCache;

    @Resource
    private HttpSysUtilApiService httpSysUtilApiService;

    @Autowired
    private ICarWhiteInfoService carWhiteInfoService;

    @Autowired
    private ISysDictDataService sysDictDataService;

    @Autowired
    private IGeometryService geometryService;

    @Autowired
    private ICarInfoService carInfoService;

    @Autowired
    private ICarTrackInfoService carTrackInfoService;


    /**
     * 查询可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 可疑车辆
     */
    @Override
    public CarSuspicious selectCarSuspiciousById(String id) {

        CarSuspicious carSuspicious = carSuspiciousMapper.selectCarSuspiciousById(id);

        if(null != carSuspicious){
            CarSuspiciousCheck querybo = new CarSuspiciousCheck();
            querybo.setCarId(id);
            List<CarSuspiciousCheck> checkList =   carSuspiciousCheckService.selectCarSuspiciousCheckList(querybo);
            carSuspicious.setCheckList(checkList);


            //---------------查询实时轨迹
            TrailInfo trailInfo = new TrailInfo();

            List<TrailBo> carTrailList = new ArrayList<>();
            List<Geometry> raodTrailList = new ArrayList<>();
            String trackJosn = carSuspicious.getTrackJosn();
            if (CommonUtil.isNotBlank(trackJosn)) {
                trailInfo = JSON.parseObject(trackJosn, TrailInfo.class);
                // 转换查询
                trailInfo = httpSysUtilApiService.changeTrailInfo(trailInfo);
                // 轨迹值还原
                ZdataTrailTracks tracks = trailInfo.getTracks();
                carTrailList = trailInfo.getTrailList();
                if (null != carTrailList && carTrailList.size() > 0){
                    raodTrailList = carTrackInfoService.getCarGeometry(tracks,carTrailList);
                }

            }

            trailInfo.setTrailUuid(carSuspicious.getCarNo());
            trailInfo.setTrailList(carTrailList);
            trailInfo.setRaodTrailList(raodTrailList);
            trailInfo.setTrailDevCountBO(carTrackInfoService.getTrailDevBO(carTrailList));


            List<TrailInfo> trailList = new ArrayList<>();
            trailList.add(trailInfo);
            carSuspicious.setTrailList(trailList);


        }

        return carSuspicious;
    }

    /**
     * 查询可疑车辆列表
     *
     * @param carSuspicious 可疑车辆
     * @return 可疑车辆
     */
    @Override
    public List<CarSuspicious> selectCarSuspiciousList(CarSuspicious carSuspicious) {
        return carSuspiciousMapper.selectCarSuspiciousList(carSuspicious);
    }


    /**
     * 新增或者修改可疑车辆
     *
     * @param carSuspicious 可疑车辆
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarSuspicious(CarSuspicious carSuspicious)
    {
        carSuspicious.setCarNo(CommonUtil.isNull(carSuspicious.getCarNo()));

        Long userId = 1L;
        if (CommonUtil.isNotBlank(carSuspicious.getId()))
        {
            carSuspicious.setUpdateBy(userId); // 更新人
            carSuspicious.setUpdateTime(DateUtils.getTimestampNew()); // 更新时间
            // 修改
            carSuspiciousMapper.updateById(carSuspicious);
        }
        else
        {
            carSuspicious.setCreateBy(userId); // 创建人
            carSuspicious.setCreateTime(DateUtils.getTimestampNew()); // 创建时间
            carSuspicious.setUpdateBy(userId); // 更新人
            carSuspicious.setUpdateTime(DateUtils.getTimestampNew()); // 更新时间
            carSuspicious.setIsExcept("1"); // 默认是可疑车俩
            carSuspicious.setStatus("0"); // 是否可以核实标识
            // 新增 主键
            carSuspiciousMapper.insert(carSuspicious);
        }

        return AjaxResult.success("操作成功！",carSuspicious.getId());
    }


    /**
     * 批量删除可疑车辆
     *
     * @param ids 需要删除的可疑车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarSuspiciousByIds(String[] ids)
    {
        int count = carSuspiciousMapper.deleteCarSuspiciousByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除可疑车辆信息
     *
     * @param id 可疑车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSuspiciousById(String id)
    {
        int count = carSuspiciousMapper.deleteCarSuspiciousById(id);
        return AjaxResult.success(count);
    }

    /**
     * 大屏查询前10 可疑车俩
     *
     * @return 结果
     */
    @Override
    public List<CarSuspicious> selectCarSuspiciousListLimit10() {
        return carSuspiciousMapper.selectCarSuspiciousListLimit10();
    }

    /**
     * 车俩核实
     *
     * @param carSuspicious 可疑车辆
     * @return 结果
     */
    @Override
    public AjaxResult cherkCarSuspicious(CarSuspicious carSuspicious) {

        String carId = CommonUtil.isNull(carSuspicious.getId());
        if(CommonUtil.isBlank(carId)){
            return  AjaxResult.error("可疑车俩不存在！");
        }

        // 查询可疑车俩
        CarSuspicious rtnVo = carSuspiciousMapper.selectCarSuspiciousById(carId);
        if (null != rtnVo && CommonUtil.isNotBlank(rtnVo.getId())) {
        } else {
            return AjaxResult.error("可疑车俩不存在！");
        }

        if (CommonUtil.isNull(rtnVo.getStatus()).equals("1")){
            return AjaxResult.error("可疑车俩异常流水已追缴！");
        }



        // 车辆信息：根据车牌号查询
        String carNo = CommonUtil.isNull(carSuspicious.getCarNo()); // 车牌号

        List<CarSuspiciousCheck> checkList = carSuspicious.getCheckList();
        if("1".equals(CommonUtil.isNull(carSuspicious.getIsExcept()))){
            if (null != checkList && checkList.size() > 0) {
            } else {
                return AjaxResult.error("车辆逃费类型列表不能为空！");
            }
        }

        // 删除人工核验详情
        carSuspiciousCheckService.deleteCarSuspiciousCheckBySuspiciousId(carId);

        // 删除异常车辆信息
        carExceptRecordService.deleteCarExceptRecordByCarId(carId);

        // 逃费类型
        String escapedType = "";
        BigDecimal escapedAmount = BigDecimal.ZERO;
        for (CarSuspiciousCheck check : checkList) {
            String addCheckType = CommonUtil.isNull(check.getEscapedType());
            if (escapedType.indexOf(addCheckType) > -1) {
            } else {
                escapedType += addCheckType + ",";
            }
            if (null != check.getDifAmount()){
                escapedAmount = escapedAmount.add(check.getDifAmount());
            }
        }
        escapedType = CommonUtil.deleteEnd(escapedType);

        // 确认逃费
        if("1".equals(CommonUtil.isNull(carSuspicious.getIsExcept()))){


            // 查询车俩
            CarInfo querybo = new CarInfo();
            querybo.setCarNo(carNo);
            List<CarInfo> carInfoList =  carInfoMapper.selectCarInfoList(querybo);

            // 有值
            if (null != carInfoList && carInfoList.size() > 0) {
                // CarInfo addCarInfo = carInfoList.get(0);
            }else{
                CarInfo addCarInfo = new CarInfo();
                Long userId = SecurityUtils.getUserId();
                addCarInfo.setId(StringUtils.getUUID()); // 主键
                addCarInfo.setDelFlag("0");
                addCarInfo.setEpsId(SecurityUtils.getEpsId());
                addCarInfo.setCreateBy(userId); // 创建人
                addCarInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                addCarInfo.setUpdateBy(userId); // 更新人
                addCarInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间

                addCarInfo.setCarNo(carNo);
                addCarInfo.setCarType(carSuspicious.getCarType());
                addCarInfo.setCarNum(carSuspicious.getCarNum());
                addCarInfo.setCarVehicle(carSuspicious.getCarVehicle());
                addCarInfo.setPlateColor(carSuspicious.getPlateColor());
                addCarInfo.setEscapedType(carSuspicious.getEscapedType());
                addCarInfo.setEscapedAmount(escapedAmount);

                carInfoMapper.insert(addCarInfo);
            }


            List<CarExceptRecord> exceptRecordList = new ArrayList<CarExceptRecord>();

            // 人工核实详情
            for (CarSuspiciousCheck check : checkList) {
                check.setCarId(carId);
                check.setCarNo(carNo);
                check.setSuspicousFlag(carSuspicious.getIsExcept());

                // --------------异常流水
                CarExceptRecord carExceptRecord = new CarExceptRecord();
                carExceptRecord.setCarId(carId);
                carExceptRecord.setCarNo(carNo);
                carExceptRecord.setCarType(carSuspicious.getCarType());
                carExceptRecord.setCarVehicle(carSuspicious.getCarVehicle());
                carExceptRecord.setCarNum(carSuspicious.getCarNum());

                carExceptRecord.setPassType(rtnVo.getPassType());
                carExceptRecord.setInStationId(rtnVo.getInStationId());
                carExceptRecord.setInStation(rtnVo.getInStation());
                carExceptRecord.setInTime(rtnVo.getInTime());
                carExceptRecord.setOutStationId(rtnVo.getGantryStationId());
                carExceptRecord.setOutStation(rtnVo.getGantrytStation());
                carExceptRecord.setOutTime(rtnVo.getGantryTime());
                carExceptRecord.setStatus("0");

                carExceptRecord.setTotalAmount(check.getTotalAmount());
                carExceptRecord.setChargeAmount(check.getChargeAmount());
                carExceptRecord.setDifAmount(check.getDifAmount());
                carExceptRecord.setEscapedType(check.getEscapedType());
                exceptRecordList.add(carExceptRecord);

            }

            if (null != checkList && checkList.size() > 0) {
                carSuspiciousCheckService.saveBatch(checkList); // 插入核实
                carExceptRecordService.saveBatch(exceptRecordList); // 插入异常车辆流水
            }

        }


        // 修改状态已核实
        CarSuspicious updatebo = new CarSuspicious();
        updatebo.setId(carId);
        updatebo.setCheckStatus("1");
        updatebo.setIsExcept(carSuspicious.getIsExcept());
        updatebo.setExceptRemark(carSuspicious.getExceptRemark());
        updatebo.setExceptFileIds(carSuspicious.getExceptFileIds());
        updatebo.setPassType(carSuspicious.getPassType());

        updatebo.setPlateColor(carSuspicious.getPlateColor());
        updatebo.setCarNo(carNo);
        updatebo.setCarType(carSuspicious.getCarType());
        updatebo.setCarVehicle(carSuspicious.getCarVehicle());
        updatebo.setCarNum(carSuspicious.getCarNum());
        updatebo.setEscapedType(carSuspicious.getEscapedType());
        updatebo.setRemark(carSuspicious.getRemark());

        // 车辆相关信息
        if("0".equals(CommonUtil.isNull(carSuspicious.getIsExcept()))){
            updatebo.setExceptFileIds("");
        }
        carSuspiciousMapper.updateById(updatebo);

        // 跟新重点车俩库
        carInfoService.updateRedisCarList();

        return AjaxResult.success("操作成功！",carSuspicious.getId());
    }

    /**
     * 可疑车俩
     *
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncSuspiciousCar() {
        Long userId = 1L;
        CarParaVO carParaVO = new CarParaVO();

        //-------------------白名单的不生成相关数据------------
        Map<String,CarWhiteInfo> carWhiteInfoMap = new HashMap<>();
        List<CarWhiteInfo> carWhiteInfoList = carWhiteInfoService.getRedisCarWhiteList();
        for (CarWhiteInfo carWhiteInfo:carWhiteInfoList){
            carWhiteInfoMap.put(CommonUtil.isNull(carWhiteInfo.getCarNo()),carWhiteInfo);
        }

        // 调用接口 (从redis拿)
        // Map<String, List<TrailBo>> mapCar = httpSysUtilApiService.syncSuspiciousCar(carParaVO);

        // 从redis拿
        List<TrailInfo> trailInfoList = new ArrayList<>();
        Date now = new Date();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd");
        String formattedDate = sdf.format(now);

        Collection<String> keys = redisCache.keys(Constants.car_uspicious + formattedDate + "*");
        if (null != keys && keys.size() > 0){
            for (String key : keys) {
                TrailInfo trailInfo = redisCache.getCacheObject(key);
                trailInfoList.add(trailInfo);
            }
        }

        // 查询所有的车俩
        Map<String,CarInfo> carInfoMap = new HashMap<>();
        List<CarInfo> carList = carInfoService.getRedisCarList();
        for (CarInfo vo : carList) {
            carInfoMap.put(CommonUtil.isNull(vo.getCarNo()),vo);
        }

        // 轨迹新增或者修改
        List<CarSuspicious>  carSuspiciousListAdd = new ArrayList<>();
        List<CarSuspicious>  carSuspiciousListUpdate = new ArrayList<>();

        // 车牌颜色
        Map<String,String> plateColorMap = sysDictDataService.selectDictDataLaleMap("plate_color");

        // 车型
        Map<String,String> carTypeMap = sysDictDataService.selectDictDataMap("car_type_old");

        // 车种
       //  Map<String,String> carVehicleMap = sysDictDataService.selectDictDataLaleMap("car_vehicle");

        //车牌对应的车种
        // Map<String,String> plateChangeMap = sysDictDataService.selectDictDataLaleMap("plate_change");

        for (TrailInfo trailInfo:trailInfoList) {

            ZdataTrailTracks tracksBo = trailInfo.getTracks();
            String carNo = CommonUtil.isNull(tracksBo.getPlateKey()); // 车牌号
            String trailUUid = CommonUtil.isNull(tracksBo.getUuid()); // 轨迹单
            if (CommonUtil.isNotBlank(carNo) && CommonUtil.isNotBlank(trailUUid)) {
                if (!carWhiteInfoMap.containsKey(carNo)){
                    List<TrailBo> josnList = trailInfo.getTrailList();

                    if (null != josnList && josnList.size() > 0) {

                        String devCodes = "";  // 设备所有的集合
                        // 生成可疑车辆
                        CarSuspicious carSuspicious = new CarSuspicious();

                        CarSuspicious queryBo = new CarSuspicious();
                        queryBo.setCarNo(carNo);
                        queryBo.setTrackId(trailUUid);
                        List<CarSuspicious> queryList = carSuspiciousMapper.selectCarSuspiciousList(queryBo);

                        String checkStatus = "0";
                        if (null != queryList && queryList.size() > 0) {
                            carSuspicious.setId(queryList.get(0).getId());
                            checkStatus = CommonUtil.isNull(queryList.get(0).getCheckStatus());
                        }

                        carSuspicious.setTrackId(trailUUid);
                        carSuspicious.setTrackJosn(JSON.toJSON(trailInfo)+"");

                        if (checkStatus.equals("1")){
                            // 是否核实
                        }else{
                            carSuspicious.setCarNo(carNo);
                            carSuspicious.setPlateColor(CommonUtil.isNull(plateColorMap.get(tracksBo.getPlateColor()))); // 来源于收费站抓拍对象 platecolor 中文

                            // ------------------标记需要转换
                            if (carInfoMap.containsKey(carNo)){
                                CarInfo carInfo = carInfoMap.get(carNo);
                                carSuspicious.setPlateColor(CommonUtil.isNull(carInfo.getPlateColor()));
                                carSuspicious.setCarType(CommonUtil.isNull(carInfo.getCarType()));
                                carSuspicious.setCarVehicle(CommonUtil.isNull(carInfo.getCarVehicle()));

                            }else{
                                // 车型
                                if (CommonUtil.isNotBlank(tracksBo.getEnvehicletype())){

                                    String carType = "";
                                    String carVehicle = "";
                                    String carTypeName = CommonUtil.isNull(carTypeMap.get(tracksBo.getEnvehicletype()));
                                    if (carTypeName.equals("六型货车")){
                                        carType = "10"; // 货六
                                        carVehicle = "2";
                                    } else if (carTypeName.equals("五型货车")){
                                        carType = "9"; // 货五
                                        carVehicle = "2";
                                    } else if (carTypeName.equals("四型货车")){
                                        carType = "8"; // 货五
                                        carVehicle = "2";
                                    } else if (carTypeName.equals("三型货车")){
                                        carType = "7"; // 货五
                                        carVehicle = "2";
                                    }else if (carTypeName.equals("二型货车")){
                                        carType = "6"; // 货五
                                        carVehicle = "2";
                                    } else if (carTypeName.equals("小货车")){
                                        carType = "5"; // 货五
                                        carVehicle = "2";
                                    } else if (carTypeName.equals("客车")){
                                        carType = "1"; // 货一
                                        carVehicle = "1";
                                    } else if (carTypeName.equals("一型客车")){
                                        carType = "1"; //
                                        carVehicle = "1";
                                    }else if (carTypeName.equals("二型客车")){
                                        carType = "2"; //
                                        carVehicle = "1";
                                    } else if (carTypeName.equals("三型客车")){
                                        carType = "3"; //
                                        carVehicle = "1";
                                    }else if (carTypeName.equals("四型客车")){
                                        carType = "4"; //
                                        carVehicle = "1";
                                    }

                                    carSuspicious.setCarType(carType); // 对应的是car_type_old 来源于 zdata_trail_fitting envehicletype
                                    carSuspicious.setCarVehicle(carVehicle);
                                }
                            }


                            // 入口车轴数
                            if (null != tracksBo.getEnaxlecount()) {
                                carSuspicious.setCarNum(Long.parseLong(tracksBo.getEnaxlecount() + "")); // 轴数
                            } else {
                                carSuspicious.setCarNum(tracksBo.getCarNum()); // 轴数
                            }
                            carSuspicious.setPassType(tracksBo.getPassType()); // 通行标识



                            //--------------设置默认值
                            if (CommonUtil.isBlank(carSuspicious.getPlateColor())){
                                carSuspicious.setPlateColor("0");
                            }

                            if (CommonUtil.isBlank(carSuspicious.getCarType())){
                                carSuspicious.setCarType("99");
                            }

                            if (CommonUtil.isBlank(carSuspicious.getCarVehicle())){
                                carSuspicious.setCarVehicle("99");
                            }

                            // -------------需要转换----------------


                            List<TrailBo> gantryList = new ArrayList<TrailBo>(); // 门架
                            List<TrailBo> stationList = new ArrayList<TrailBo>(); // 收费站

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
                                switch (stateType) {
                                    case Constants.BORDER_WEIGHING_CAPTURE:
                                        // 省界称重
                                        break;
                                    case Constants.GANTRY_CAPTURE:
                                        // 门架抓拍
                                        gantryList.add(trailBo);
                                        break;
                                    case Constants.PROV_CAPTURE:
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
                            for (int i = 0; i < stationList.size(); i++) {
                                TrailBo trailBo = stationList.get(i);
                                if (i == 0) {
                                    // 第一个收费站
                                    carSuspicious.setInStationId(trailBo.getDevCode());
                                    carSuspicious.setInStation(trailBo.getDevName());
                                    if (CommonUtil.isNotBlank(trailBo.getCaptureTime())){
                                        carSuspicious.setInTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getCaptureTime()));
                                    }
                                } else {
                                    // 最后一个收费站
                                    if (i == stationList.size() - 1) {
                                        carSuspicious.setOutStationId(trailBo.getDevCode());
                                        carSuspicious.setOutStation(trailBo.getDevName());
                                        if (CommonUtil.isNotBlank(trailBo.getCaptureTime())){
                                            carSuspicious.setOutTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getCaptureTime()));
                                        }
                                    }
                                }
                            }

                            // 入口收费站编号
                            if (CommonUtil.isNotBlank(tracksBo.getEntollstationid())){
                                // 第一个收费站
                                carSuspicious.setInStationId(tracksBo.getEntollstationid());
                                carSuspicious.setInStation(tracksBo.getEntollstationname());
                                if (null != tracksBo.getEnterTime()){
                                    carSuspicious.setInTime(tracksBo.getEnterTime());
                                }
                            }

                            // 出口收费站
                            if (CommonUtil.isNotBlank(tracksBo.getExtollstationid())){
                                // 最后一个收费站
                                carSuspicious.setOutStationId(tracksBo.getExtollstationid());
                                carSuspicious.setOutStation(tracksBo.getExtollstationname());
                                if (null != tracksBo.getExitTime()){
                                    carSuspicious.setOutTime(tracksBo.getExitTime());
                                }
                            }


                            //  门架 ---------------
                            for (int i = 0; i < gantryList.size(); i++) {
                                TrailBo trailBo = gantryList.get(i);
                                if (i == 0) {
                                    // 第一个门架
                                    carSuspicious.setGantryStationId(trailBo.getDevCode());
                                    carSuspicious.setGantrytStation(trailBo.getDevName());
                                    if (CommonUtil.isNotBlank(trailBo.getCaptureTime())){
                                        carSuspicious.setGantryTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getCaptureTime()));
                                    }
                                } else {
                                    // 最后一个门架
                                    if (i == gantryList.size() - 1) {
                                        carSuspicious.setOutGantryStationId(trailBo.getDevCode());
                                        carSuspicious.setOutGantrytStation(trailBo.getDevName());
                                        if (CommonUtil.isNotBlank(trailBo.getCaptureTime())){
                                            carSuspicious.setOutGantryTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getCaptureTime()));
                                        }
                                    }
                                }
                            }

                            carSuspicious.setCreateBy(userId); // 创建人
                            carSuspicious.setCreateTime(DateUtils.getTimestampNew()); // 创建时间
                            carSuspicious.setUpdateBy(userId); // 更新人
                            carSuspicious.setUpdateTime(DateUtils.getTimestampNew()); // 更新时间
                            carSuspicious.setIsExcept("1"); // 默认是可疑车俩
                            carSuspicious.setStatus("0"); // 是否可以核实标识

                            carSuspicious.setTrackNames(CommonUtil.deleteEnd(devCodes));
                            if (CommonUtil.isBlank(carSuspicious.getId())){
                                // 新增-----------
                                carSuspicious.setEscapedType(tracksBo.getEscapedType()); //屏蔽
                                carSuspicious.setRemark(tracksBo.getEscapedTypeRemark());
                                carSuspiciousListAdd.add(carSuspicious);
                            }else{
                                // 没有核实
                                carSuspicious.setRemark(tracksBo.getEscapedTypeRemark());
                                carSuspiciousListUpdate.add(carSuspicious);
                            }
                        }
                    }
                }
            }
        }

        if (null !=carSuspiciousListAdd && carSuspiciousListAdd.size() > 0){
            this.saveBatch(carSuspiciousListAdd);
        }


        if (null !=carSuspiciousListUpdate && carSuspiciousListUpdate.size() > 0){
            this.updateBatchById(carSuspiciousListUpdate);
        }

        if (null != keys && keys.size() > 0){
            // 删除redis
            redisCache.deleteObject(keys);
        }

        return AjaxResult.success();
    }
}
