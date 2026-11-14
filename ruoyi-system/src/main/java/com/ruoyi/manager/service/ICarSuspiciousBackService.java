package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarSuspiciousBack;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 可疑车辆备份Service接口
 *
 * @author ruoyi
 * @date 2026-02-05
 */
public interface ICarSuspiciousBackService extends IService<CarSuspiciousBack> {
    /**
     * 查询可疑车辆备份
     *
     * @param id 可疑车辆备份ID
     * @return 可疑车辆备份
     */
    CarSuspiciousBack selectCarSuspiciousBackById(String id);

    /**
     * 查询可疑车辆备份列表
     *
     * @param carSuspiciousBack 可疑车辆备份
     * @return 可疑车辆备份集合
     */
    List<CarSuspiciousBack> selectCarSuspiciousBackList(CarSuspiciousBack carSuspiciousBack);


    /**
     * 新增或者修改可疑车辆备份
     *
     * @param carSuspiciousBack 可疑车辆备份
     * @return 结果
     */
    AjaxResult saveCarSuspiciousBack(CarSuspiciousBack carSuspiciousBack);

    /**
     * 批量删除可疑车辆备份
     *
     * @param ids 需要删除的可疑车辆备份ID
     * @return 结果
     */
    AjaxResult deleteCarSuspiciousBackByIds(String[] ids);

}
