package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarSuspicious;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 可疑车辆Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarSuspiciousService extends IService<CarSuspicious> {
    /**
     * 查询可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 可疑车辆
     */
    CarSuspicious selectCarSuspiciousById(String id);

    /**
     * 查询可疑车辆列表
     *
     * @param carSuspicious 可疑车辆
     * @return 可疑车辆集合
     */
    List<CarSuspicious> selectCarSuspiciousList(CarSuspicious carSuspicious);


    /**
     * 新增或者修改可疑车辆
     *
     * @param carSuspicious 可疑车辆
     * @return 结果
     */
    AjaxResult saveCarSuspicious(CarSuspicious carSuspicious);

    /**
     * 批量删除可疑车辆
     *
     * @param ids 需要删除的可疑车辆ID
     * @return 结果
     */
    AjaxResult deleteCarSuspiciousByIds(String[] ids);

    List<CarSuspicious> selectCarSuspiciousListLimit10();
}
