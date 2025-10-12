package com.ruoyi.manager.service.impl;

import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.domain.CarVO;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.domain.TrailBo;
import com.ruoyi.base.domain.TrailInfo;
import com.ruoyi.base.service.IGeometryService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO;
import com.ruoyi.manager.mapper.CarInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarTrackInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 车辆信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarInfoServiceImpl extends ServiceImpl<CarInfoMapper, CarInfo> implements ICarInfoService {


    @Autowired
    private RedisCache redisCache;


    @Autowired
    private CarInfoMapper carInfoMapper;

    @Autowired
    private IGeometryService geometryService;

    @Autowired
    private ICarTrackInfoService carTrackInfoService;


    /**
     * 查询车辆信息
     *
     * @param id 车辆信息ID
     * @return 车辆信息
     */
    @Override
    public CarInfo selectCarInfoById(String id) {
        CarInfo car = carInfoMapper.selectCarInfoById(id);
        if (null != car) {
            //---------------查询实时轨迹
            List<TrailBo> carTrailList = new ArrayList<>();
            List<Geometry> raodTrailList = new ArrayList<>();
            if (CommonUtil.isNull(car.getStatus()).equals("1")) {
                String trackJosn = car.getTrackJosn();
                if (CommonUtil.isNotBlank(trackJosn)) {
                    carTrailList = JSON.parseArray(trackJosn, TrailBo.class);
                    raodTrailList = carTrackInfoService.getCarGeometry(carTrailList);;
                }
            }
            TrailInfo trailInfo = new TrailInfo();
            trailInfo.setTrailUuid(car.getCarNo());
            trailInfo.setTrailList(carTrailList);
            trailInfo.setRaodTrailList(raodTrailList);

            List<TrailInfo> trailList = new ArrayList<>();
            trailList.add(trailInfo);
            car.setTrailList(trailList);

        }
        return car;
    }

    /**
     * 查询车辆信息列表
     *
     * @param carInfo 车辆信息
     * @return 车辆信息
     */
    @Override
    public List<CarInfo> selectCarInfoList(CarInfo carInfo) {
        return carInfoMapper.selectCarInfoList(carInfo);
    }


    /**
     * 新增或者修改车辆信息
     *
     * @param carInfo 车辆信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarInfo(CarInfo carInfo)
    {
        Long userId = SecurityUtils.getUserId();
        carInfo.setCarNo(CommonUtil.isNull(carInfo.getCarNo())); //去掉空格
        // 判断车牌号是否重复
        int countNum = carInfoMapper.isExitsCar(carInfo);
        if (countNum > 0){
            return AjaxResult.error("车牌号存在重复，请确定！");
        }

        if (CommonUtil.isNotBlank(carInfo.getId()))
        {
            carInfo.setUpdateBy(userId); // 更新人
            carInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 修改
            carInfoMapper.updateById(carInfo);
        }
        else
        {
            carInfo.setId(StringUtils.getUUID()); // 主键
            carInfo.setDelFlag("0");
            carInfo.setCreateBy(userId); // 创建人
            carInfo.setEpsId(SecurityUtils.getEpsId());
            carInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
            carInfo.setUpdateBy(userId); // 更新人
            carInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 新增 主键
            carInfoMapper.insert(carInfo);
        }
        this.updateRedisCarList();
        return AjaxResult.success("操作成功！",carInfo.getId());
    }

    /**
     * 批量删除车辆信息
     *
     * @param ids 需要删除的车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarInfoByIds(String[] ids)
    {
        int count = carInfoMapper.deleteCarInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆信息信息
     *
     * @param id 车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarInfoById(String id)
    {
        int count = carInfoMapper.deleteCarInfoById(id);
        this.updateRedisCarList();
        return AjaxResult.success(count);
    }


    /**
     * 导入
     *
     * @param list
     * @return
     */
    public AjaxResult doImport(List<CarInfo> list) {
        if (null != list && list.size() > 0) {
            Long userId = SecurityUtils.getUserId();
            List<CarInfo> addlist = new ArrayList<CarInfo>();
            List<CarInfo> updatalist = new ArrayList<CarInfo>();
            for (CarInfo carInfo : list) {
                if (CommonUtil.isNotBlank(carInfo.getId())){
                    carInfo.setUpdateBy(userId); // 更新人
                    carInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
                    updatalist.add(carInfo);
                }else{
                    carInfo.setId(StringUtils.getUUID()); // 主键
                    carInfo.setDelFlag("0");
                    carInfo.setCreateBy(userId); // 创建人
                    carInfo.setEpsId(SecurityUtils.getEpsId());
                    carInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                    carInfo.setUpdateBy(userId); // 更新人
                    carInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
                    addlist.add(carInfo);
                }
            }

            // 新增
            if (addlist.size() > 0) {
                for (CarInfo addbo:addlist){
                    // 新增 主键
                    addbo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                    carInfoMapper.insert(addbo);
                }
                // ------------创建的时间一样
               //  this.saveBatch(addlist);
            }
            // 修改
            if (updatalist.size() > 0) {
                this.updateBatchById(updatalist);
            }
        }
        this.updateRedisCarList();
        return AjaxResult.success();
    }

    /**
     * 地图 ；车俩地图描点
     */
    @Override
    public List<CarLocationVO> carLocation(CarLocationParam carInfo) {
        List<CarLocationVO>  carLocation = new ArrayList<>();
        List<CarInfo> carInfoList = this.getRedisCarList();
        for (CarInfo rtn : carInfoList) {
            if (CommonUtil.isNull(rtn.getStatus()).equals("1")){
                String devCodes = CommonUtil.isNull(rtn.getGantryCode());
                boolean addFlag = true;
                // 所属收费站编码
                if (CommonUtil.isNotBlank(carInfo.getTollCode())){
                    if (devCodes.indexOf(carInfo.getTollCode()) == -1){
                        addFlag = false;
                    }
                }
                // 门架编号
                if (CommonUtil.isNotBlank(carInfo.getGantryCode())){
                    if (devCodes.indexOf(carInfo.getGantryCode()) == -1){
                        addFlag = false;
                    }
                }
                // 服务区编码
                if (CommonUtil.isNotBlank(carInfo.getFwqbm())){
                    if (devCodes.indexOf(carInfo.getFwqbm()) == -1){
                        addFlag = false;
                    }
                }
                // 所属路线编码
                if (CommonUtil.isNotBlank(carInfo.getRoadCode())){
                    if (devCodes.indexOf(carInfo.getRoadCode()) == -1){
                        addFlag = false;
                    }
                }

                // 所属路段编码
                if (CommonUtil.isNotBlank(carInfo.getSectionCode())){
                    if (devCodes.indexOf(carInfo.getSectionCode()) == -1){
                        addFlag = false;
                    }
                }

                // 逃费类型
                if (CommonUtil.isNotBlank(carInfo.getEscapedType())){
                    if (CommonUtil.isNull(rtn.getEscapedType()).indexOf(carInfo.getEscapedType()) == -1){
                        addFlag = false;
                    }
                }
                // 车牌号
                if (CommonUtil.isNotBlank(carInfo.getCarNoQuery())){
                    if (CommonUtil.isNull(rtn.getCarNo()).indexOf(carInfo.getCarNoQuery()) == -1){
                        addFlag = false;
                    }
                }
                if (addFlag){
                    CarLocationVO addvo = new CarLocationVO();
                    addvo.setId(rtn.getId());
                    addvo.setCarNo(rtn.getCarNo());
                    addvo.setCarType(rtn.getCarType());
                    addvo.setLonStr(rtn.getLastPassLongitude());
                    addvo.setLatStr(rtn.getLastPassLatitude());
                    if(CommonUtil.isNotBlank(addvo.getLonStr())) {
                        addvo.setLon(new BigDecimal(addvo.getLonStr()));
                    }
                    if(CommonUtil.isNotBlank(addvo.getLatStr())) {
                        addvo.setLat(new BigDecimal(addvo.getLatStr()));
                    }
                    addvo.setStatus(rtn.getStatus());
                    carLocation.add(addvo);
                }
            }
        }

       /* List<CarLocationVO> carLocation = carInfoMapper.getCarLocation(carInfo);
        if(CollectionUtils.isNotEmpty(carLocation)) {
            for (CarLocationVO carLocationVO : carLocation) {
                if(CommonUtil.isNotBlank(carLocationVO.getLonStr())) {
                    carLocationVO.setLon(new BigDecimal(carLocationVO.getLonStr()));
                }
                if(CommonUtil.isNotBlank(carLocationVO.getLatStr())) {
                    carLocationVO.setLat(new BigDecimal(carLocationVO.getLatStr()));
                }
            }
        }

        List<CarLocationVO> carLocation2 = carInfoMapper.getCarLocation(carInfo);
        */
        return carLocation;
    }

    /**
     * 地图：重点车辆库统计 前10条
     * @return
     */
    @Override
    public List<CarInfoVO> selectCarVoList() {
        return carInfoMapper.selectCarVoList();
    }

    /**
     * 跟新缓存
     */
    public void updateRedisCarList() {
        CarInfo carInfoQuery = new CarInfo();
        List<CarInfo> list = carInfoMapper.selectCarInfoList(carInfoQuery);

        List<CarVO> carVOList = new ArrayList<>();
        for (CarInfo rtn : list) {
            CarVO tempVO = new CarVO();
            tempVO.setCarId(rtn.getId());
            tempVO.setCarNo(rtn.getCarNo());
            carVOList.add(tempVO);
        }
        redisCache.setCacheObject(Constants.car_list_jc, carVOList);
        redisCache.setCacheObject(Constants.car_list, list);
    }


    /**
     * 从缓存拿到carlist
     */
    public List<CarInfo> getRedisCarList() {
        List<CarInfo> list = null;
        Object obj = redisCache.getCacheObject(Constants.car_list);
        if (null != obj) {
            list = (List) obj;
        } else {
            CarInfo carInfo = new CarInfo();
            list = carInfoMapper.selectCarInfoList(carInfo);
            redisCache.setCacheObject(Constants.car_list, list);
        }
        return list;
    }


}
