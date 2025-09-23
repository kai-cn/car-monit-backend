package com.ruoyi.manager.service.impl;


import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarTrackInfo;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.CarVO;
import com.ruoyi.manager.domain.vo.TrailBo;
import com.ruoyi.manager.mapper.CarTrackInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import com.ruoyi.manager.service.ICarWarningInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 车辆行驶轨迹Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
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
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult sync() {
        // 查询所有的车俩
        List<CarInfo> carList = carInfoService.getRedisCarList();

        Map<String,CarInfo> carMap = new HashMap<>();
        List<CarVO> carVOList = new ArrayList<>();
        for (CarInfo rtn : carList) {
            CarVO tempVO = new CarVO();
            tempVO.setCarId(rtn.getId());
            tempVO.setCarNo(rtn.getCarNo());
            carVOList.add(tempVO);
            carMap.put(rtn.getCarNo(),rtn);
        }
        CarParaVO carParaVO = new CarParaVO();
        carParaVO.setCarlist(carVOList);

        List<CarInfo> updatalist = new ArrayList<CarInfo>();

        // 调用接口
        Map<String, List<TrailBo>> mapCar = httpSysUtilApiService.syncTrack(carParaVO);

        // 新增的预警
        List<CarWarningInfo> addCarWarningInfoList = new ArrayList<>();
        // 删除的预警
        List<String> delCarWarningInfoList = new ArrayList<>();

        Long userId = 1L;

        for (Map.Entry<String, List<TrailBo>> entry : mapCar.entrySet()) {
            String carNo = entry.getKey();
            if (carMap.containsKey(carNo)){
                CarInfo vo = carMap.get(carNo);
                CarInfo car = new CarInfo();
                car.setId(vo.getId());
                List<TrailBo> josnList = entry.getValue();
                if (null != josnList && josnList.size() > 0) {
                    // 车的状态修改更新为 status 1  经纬度 last_pass_longitude  last_pass_latitude  josn字符串要更新 track_id track_josn
                    // 同事要跟新车俩预警  car_warning_info
                    car.setStatus("1");
                    // 进度和维度
                    TrailBo lastBo = josnList.get(josnList.size() - 1);
                    if (null !=lastBo.getLon()){
                        car.setLastPassLongitude(CommonUtil.isNull(lastBo.getLon()));
                    }

                    if (null !=lastBo.getLat()){
                        car.setLastPassLatitude(CommonUtil.isNull(lastBo.getLat()));
                    }
                    car.setTrackJosn(JSON.toJSON(josnList)+"");

                    for (TrailBo trailBo : josnList) {

                        String pointUuid = CommonUtil.isNull(trailBo.getPointUuid());

                        CarWarningInfo carWarningInfo = new CarWarningInfo();
                        carWarningInfo.setCarId(vo.getId());
                        carWarningInfo.setCarNo(vo.getCarNo());
                        carWarningInfo.setCarType(vo.getCarType());
                        carWarningInfo.setCarVehicle(vo.getCarVehicle());
                        carWarningInfo.setCarNum(vo.getCarNum());
                        // 入站
                        carWarningInfo.setInStationId(trailBo.getFirtStationCode());
                        carWarningInfo.setInStation(trailBo.getFirtStationName());
                        if (CommonUtil.isNotBlank(trailBo.getFirtStationTime())){
                            carWarningInfo.setInTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getFirtStationTime()));
                        }

                        // 抓拍设备
                        carWarningInfo.setGantryStationId(trailBo.getDevCode());
                        carWarningInfo.setInStation(trailBo.getDevName());
                        if (CommonUtil.isNotBlank(trailBo.getCaptureTime())){
                            carWarningInfo.setGantryTime(DateUtils.dateTime(DateUtils.YYYY_MM_DD_HH_MM_SS,trailBo.getCaptureTime()));
                        }
                        carWarningInfo.setFileIds(trailBo.getImagesArry());
                        carWarningInfo.setBackCol1(pointUuid);

                        // 预计下一个通行时间nextPassTime  预计下一个通行地址 nextPassAddress

                        carWarningInfo.setDelFlag("0");
                        carWarningInfo.setCreateBy(userId); // 创建人
                        carWarningInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                        carWarningInfo.setUpdateBy(userId); // 更新人
                        carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间


                        addCarWarningInfoList.add(carWarningInfo);

                        if (CommonUtil.isNotBlank(pointUuid)){
                            delCarWarningInfoList.add(pointUuid);
                        }



                    }



                }else{
                    // 跟新车俩-----------------------  车的状态修改status 0
                    car.setStatus("0");
                    car.setTrackJosn(null);
                }
                updatalist.add(car);
            }
        }

        // 修改
        if (updatalist.size() > 0) {
            carInfoService.updateBatchById(updatalist);
        }

        // 更新缓存
        carInfoService.updateRedisCarList();

        return AjaxResult.success();
    }



}
