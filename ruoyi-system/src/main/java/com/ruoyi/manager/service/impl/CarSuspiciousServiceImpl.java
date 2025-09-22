package com.ruoyi.manager.service.impl;

import com.alibaba.fastjson2.JSON;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.base.service.forest.HttpSysUtilApiService;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import com.ruoyi.manager.domain.vo.CarParaVO;
import com.ruoyi.manager.domain.vo.TrailBo;
import com.ruoyi.manager.mapper.CarInfoMapper;
import com.ruoyi.manager.mapper.CarSuspiciousMapper;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.ICarSuspiciousCheckService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import javax.annotation.Resource;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

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
        String carNo = CommonUtil.isNull(rtnVo.getCarNo()); // 车牌号

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
                addCarInfo.setCreateBy(userId); // 创建人
                addCarInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
                addCarInfo.setUpdateBy(userId); // 更新人
                addCarInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间

                addCarInfo.setCarNo(carNo);
                addCarInfo.setCarType(rtnVo.getCarType());
                addCarInfo.setCarNum(rtnVo.getCarNum());
                addCarInfo.setCarVehicle(rtnVo.getCarVehicle());
                addCarInfo.setPlateColor(rtnVo.getPlateColor());
                addCarInfo.setEscapedType(escapedType);
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
                carExceptRecord.setCarType(rtnVo.getCarType());
                carExceptRecord.setCarVehicle(rtnVo.getCarVehicle());
                carExceptRecord.setCarNum(rtnVo.getCarNum());
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
        updatebo.setEscapedType(escapedType);
        if("0".equals(CommonUtil.isNull(carSuspicious.getIsExcept()))){
            updatebo.setExceptFileIds("");
            updatebo.setEscapedType("");
        }
        carSuspiciousMapper.updateById(updatebo);

        // 跟新重点车俩库
        CarInfo carInfoQuery = new CarInfo();
        List<CarInfo> list = carInfoMapper.selectCarInfoList(carInfoQuery);
        redisCache.setCacheObject(Constants.car_list, list);

        return AjaxResult.success("操作成功！",carSuspicious.getId());
    }

    /**
     * 可疑车俩
     *
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult syncSuspiciousCar() {
        CarParaVO carParaVO = new CarParaVO();
        // 调用接口
        Map<String, List<TrailBo>> map = httpSysUtilApiService.syncSuspiciousCar(carParaVO);
        if (map != null) {
            for (Map.Entry<String, List<TrailBo>> entry : map.entrySet()) {
                String carNo = entry.getKey();
                List<TrailBo> trailBoList = entry.getValue();
                for (TrailBo trailBo : trailBoList) {
                    CarSuspicious suspicious = new CarSuspicious();//生成可疑车辆
                    suspicious.setCarNo(carNo);
                    suspicious.setTrackId(trailBo.getPointUuid());
                    suspicious.setTrackJosn(JSON.toJSONString(trailBo));
                    if (trailBo.getGantryCaptureBO() != null) {
                        suspicious.setPlateColor(trailBo.getGantryCaptureBO().getPlatecolor());
                        suspicious.setSectionCode(trailBo.getGantryCaptureBO().getSectioncode());
                        suspicious.setSectionName(trailBo.getGantryCaptureBO().getSectionname());
                        suspicious.setRoadCode(trailBo.getGantryCaptureBO().getRoadcode());
                        suspicious.setRoadName(trailBo.getGantryCaptureBO().getRoadname());
                        suspicious.setOrgName(trailBo.getGantryCaptureBO().getOrgname());
                    }
                    if (trailBo.getStationCapture() != null) {
                        suspicious.setCarType(trailBo.getStationCapture().getCartype());
                    }
                }
            }
        }
        return AjaxResult.success();
    }
}
