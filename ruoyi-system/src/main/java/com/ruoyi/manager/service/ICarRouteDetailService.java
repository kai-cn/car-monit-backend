package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarRouteDetail;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 常用路线明细Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarRouteDetailService extends IService<CarRouteDetail> {
    /**
     * 查询常用路线明细
     *
     * @param id 常用路线明细ID
     * @return 常用路线明细
     */
    CarRouteDetail selectCarRouteDetailById(String id);

    /**
     * 查询常用路线明细列表
     *
     * @param carRouteDetail 常用路线明细
     * @return 常用路线明细集合
     */
    List<CarRouteDetail> selectCarRouteDetailList(CarRouteDetail carRouteDetail);


    /**
     * 新增或者修改常用路线明细
     *
     * @param carRouteDetail 常用路线明细
     * @return 结果
     */
    AjaxResult saveCarRouteDetail(CarRouteDetail carRouteDetail);

    /**
     * 批量删除常用路线明细
     *
     * @param ids 需要删除的常用路线明细ID
     * @return 结果
     */
    AjaxResult deleteCarRouteDetailByIds(String[] ids);

}
