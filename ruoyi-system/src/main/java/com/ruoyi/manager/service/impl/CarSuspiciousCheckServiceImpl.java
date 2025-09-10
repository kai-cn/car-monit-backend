package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarSuspiciousCheckMapper;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import com.ruoyi.manager.service.ICarSuspiciousCheckService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 可疑车辆人工核实Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarSuspiciousCheckServiceImpl extends ServiceImpl<CarSuspiciousCheckMapper, CarSuspiciousCheck> implements ICarSuspiciousCheckService {

    @Autowired
    private CarSuspiciousCheckMapper carSuspiciousCheckMapper;

    /**
     * 查询可疑车辆人工核实
     *
     * @param id 可疑车辆人工核实ID
     * @return 可疑车辆人工核实
     */
    @Override
    public CarSuspiciousCheck selectCarSuspiciousCheckById(String id) {
        return carSuspiciousCheckMapper.selectCarSuspiciousCheckById(id);
    }

    /**
     * 查询可疑车辆人工核实列表
     *
     * @param carSuspiciousCheck 可疑车辆人工核实
     * @return 可疑车辆人工核实
     */
    @Override
    public List<CarSuspiciousCheck> selectCarSuspiciousCheckList(CarSuspiciousCheck carSuspiciousCheck) {
        return carSuspiciousCheckMapper.selectCarSuspiciousCheckList(carSuspiciousCheck);
    }


    /**
     * 新增或者修改可疑车辆人工核实
     *
     * @param carSuspiciousCheck 可疑车辆人工核实
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarSuspiciousCheck(CarSuspiciousCheck carSuspiciousCheck)
    {
        if (CommonUtil.isNotBlank(carSuspiciousCheck.getId()))
        {
            // 修改
            carSuspiciousCheckMapper.updateById(carSuspiciousCheck);
        }
        else
        {
            // 新增 主键
            carSuspiciousCheckMapper.insert(carSuspiciousCheck);
        }
        return AjaxResult.success("操作成功！",carSuspiciousCheck.getId());
    }

    /**
     * 批量删除可疑车辆人工核实
     *
     * @param ids 需要删除的可疑车辆人工核实ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarSuspiciousCheckByIds(String[] ids)
    {
        int count = carSuspiciousCheckMapper.deleteCarSuspiciousCheckByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除可疑车辆人工核实信息
     *
     * @param id 可疑车辆人工核实ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSuspiciousCheckById(String id)
    {
        int count = carSuspiciousCheckMapper.deleteCarSuspiciousCheckById(id);
        return AjaxResult.success(count);
    }

    /**
     * 根据外键删除
     *
     * @param fkId
     * @return
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSuspiciousCheckBySuspiciousId(String fkId) {
        int count = carSuspiciousCheckMapper.deleteCarSuspiciousCheckBySuspiciousId(fkId);
        return AjaxResult.success(count);
    }



}
