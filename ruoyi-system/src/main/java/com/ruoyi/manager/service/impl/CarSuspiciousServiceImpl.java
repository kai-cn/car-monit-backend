package com.ruoyi.manager.service.impl;

import cn.hutool.core.collection.CollectionUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import com.ruoyi.manager.mapper.CarSuspiciousMapper;
import com.ruoyi.manager.domain.CarSuspicious;
import com.ruoyi.manager.service.ICarExceptRecordService;
import com.ruoyi.manager.service.ICarInfoService;
import com.ruoyi.manager.service.ICarSuspiciousCheckService;
import com.ruoyi.manager.service.ICarSuspiciousService;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;

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
    private ICarInfoService carInfoService;
    @Autowired
    private ICarSuspiciousCheckService carSuspiciousCheckService;
    @Autowired
    private ICarExceptRecordService carExceptRecordService;

    /**
     * 查询可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 可疑车辆
     */
    @Override
    public CarSuspicious selectCarSuspiciousById(String id) {
        CarSuspicious carSuspicious = carSuspiciousMapper.selectCarSuspiciousById(id);
        if(null == carSuspicious){
            return new CarSuspicious();
        }

        // 查询车辆信息
        if(StrUtil.isNotEmpty(carSuspicious.getCarNo())){
            LambdaQueryWrapper<CarInfo> queryWrapper = new LambdaQueryWrapper<>();
            queryWrapper.eq(CarInfo::getCarNo,carSuspicious.getCarNo());
            List<CarInfo> list = this.carInfoService.list(queryWrapper);
            carSuspicious.setCarInfo(CollectionUtil.isNotEmpty( list) ? list.get(0) : new CarInfo());
        }

        // 人工核实详情
        LambdaQueryWrapper<CarSuspiciousCheck> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CarSuspiciousCheck::getCarSuspiciousId,carSuspicious.getId());
        List<CarSuspiciousCheck> list = this.carSuspiciousCheckService.list();
        carSuspicious.setCarSuspiciousCheck(CollectionUtil.isNotEmpty(list) ? list.get(0): new CarSuspiciousCheck());

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
        CarInfo carInfo = carSuspicious.getCarInfo();
        if(null == carInfo || StrUtil.isEmpty(carInfo.getCarNo())){
            return AjaxResult.error("人工核检失败, 车辆信息不存在");
        }

        if (CommonUtil.isNotBlank(carSuspicious.getId()))
        {
            // 修改
            carSuspiciousMapper.updateById(carSuspicious);
        }
        else
        {
            // 新增 主键
            carSuspiciousMapper.insert(carSuspicious);
        }

        // 删除人工核验详情
        this.carSuspiciousCheckService.remove(Wrappers.<CarSuspiciousCheck>lambdaQuery()
                .eq(CarSuspiciousCheck::getCarSuspiciousId,carSuspicious.getId()));

        // 删除异常车辆信息
        this.carExceptRecordService.remove(Wrappers.<CarExceptRecord>lambdaQuery()
                .eq(CarExceptRecord::getCarSuspiciousId,carSuspicious.getId()));

        // 确认逃费
        if("1".equals(carSuspicious.getIsExcept())){
            // 车辆信息
            CarInfo one = this.carInfoService.getOne(Wrappers.<CarInfo>lambdaQuery()
                    .eq(CarInfo::getCarNo,carSuspicious.getCarNo()));
            if(null == one){
                this.carInfoService.save(carInfo);
            } else {
                carInfo = one;
            }

            // 人工核实详情
            CarSuspiciousCheck carSuspiciousCheck = carSuspicious.getCarSuspiciousCheck();
            if(null != carSuspiciousCheck){
                carSuspiciousCheck.setCarSuspiciousId(carSuspicious.getId());
                carSuspiciousCheck.setAttachments(carSuspicious.getFileIds());
                carSuspiciousCheck.setSuspicousFlag(carSuspicious.getIsExcept());

                //车辆信息
                carSuspiciousCheck.setCarId(carInfo.getId());
                carSuspiciousCheck.setCarNo(carInfo.getCarNo());
                this.carSuspiciousCheckService.save(carSuspiciousCheck);
            }

            CarExceptRecord carExceptRecord = getCarExceptRecord(carSuspicious, carInfo, carSuspiciousCheck);
            this.carExceptRecordService.saveCarExceptRecord(carExceptRecord);
        }
        return AjaxResult.success("操作成功！",carSuspicious.getId());
    }

    /**
     * 构建异常车辆信息
     * @param carSuspicious
     * @param carInfo
     * @param carSuspiciousCheck
     * @return
     */
    private static CarExceptRecord getCarExceptRecord(CarSuspicious carSuspicious, CarInfo carInfo, CarSuspiciousCheck carSuspiciousCheck) {
        CarExceptRecord carExceptRecord = new CarExceptRecord();
        carExceptRecord.setCarSuspiciousId(carSuspicious.getId());
        carExceptRecord.setCarId(carInfo.getId());
        carExceptRecord.setCarNo(carInfo.getCarNo());
        carExceptRecord.setCarType(carInfo.getCarType());
        carExceptRecord.setCarNum(carInfo.getCarNum());
        carExceptRecord.setCarVehicle(carInfo.getCarVehicle());
        carExceptRecord.setInStationId(carSuspicious.getInStationId());
        carExceptRecord.setInStation(carSuspicious.getInStation());
        carExceptRecord.setInTime(carSuspicious.getInTime());
        carExceptRecord.setOutStationId(carSuspicious.getGantryStationId());
        carExceptRecord.setOutStation(carSuspicious.getGantrytStation());
        carExceptRecord.setOutTime(carSuspicious.getGantryTime());
        carExceptRecord.setStatus("0");

        if(null != carSuspiciousCheck){
            carExceptRecord.setTotalAmount(carSuspiciousCheck.getTotalAmount());
            carExceptRecord.setChargeAmount(carSuspiciousCheck.getChargeAmount());
            carExceptRecord.setDifAmount(carSuspiciousCheck.getDifAmount());
            carExceptRecord.setEscapedType(carSuspiciousCheck.getEscapedType());
        }
        return carExceptRecord;
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

    @Override
    public List<CarSuspicious> selectCarSuspiciousListLimit10() {
        return carSuspiciousMapper.selectCarSuspiciousListLimit10();
    }
}
