package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 可疑车辆人工核实Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarSuspiciousCheckService extends IService<CarSuspiciousCheck> {
    /**
     * 查询可疑车辆人工核实
     *
     * @param id 可疑车辆人工核实ID
     * @return 可疑车辆人工核实
     */
    CarSuspiciousCheck selectCarSuspiciousCheckById(String id);

    /**
     * 查询可疑车辆人工核实列表
     *
     * @param carSuspiciousCheck 可疑车辆人工核实
     * @return 可疑车辆人工核实集合
     */
    List<CarSuspiciousCheck> selectCarSuspiciousCheckList(CarSuspiciousCheck carSuspiciousCheck);


    /**
     * 新增或者修改可疑车辆人工核实
     *
     * @param carSuspiciousCheck 可疑车辆人工核实
     * @return 结果
     */
    AjaxResult saveCarSuspiciousCheck(CarSuspiciousCheck carSuspiciousCheck);

    /**
     * 批量删除可疑车辆人工核实
     *
     * @param ids 需要删除的可疑车辆人工核实ID
     * @return 结果
     */
    AjaxResult deleteCarSuspiciousCheckByIds(String[] ids);

    /**
     * 根据外键删除
     * @param fkId
     * @return
     */
    AjaxResult deleteCarSuspiciousCheckBySuspiciousId(String fkId);

}
