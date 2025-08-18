package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarRouteInfo;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 常用路线Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarRouteInfoService extends IService<CarRouteInfo> {
    /**
     * 查询常用路线
     *
     * @param id 常用路线ID
     * @return 常用路线
     */
    CarRouteInfo selectCarRouteInfoById(String id);

    /**
     * 查询常用路线列表
     *
     * @param carRouteInfo 常用路线
     * @return 常用路线集合
     */
    List<CarRouteInfo> selectCarRouteInfoList(CarRouteInfo carRouteInfo);


    /**
     * 新增或者修改常用路线
     *
     * @param carRouteInfo 常用路线
     * @return 结果
     */
    AjaxResult saveCarRouteInfo(CarRouteInfo carRouteInfo);

    /**
     * 批量删除常用路线
     *
     * @param ids 需要删除的常用路线ID
     * @return 结果
     */
    AjaxResult deleteCarRouteInfoByIds(String[] ids);

}
