package com.ruoyi.manager.service;

import com.baomidou.mybatisplus.spring.service.IService;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarWhiteInfo;

import java.util.List;

/**
 * 车俩白名单Service接口
 *
 * @author ruoyi
 * @date 2025-09-12
 */
public interface ICarWhiteInfoService extends IService<CarWhiteInfo> {
    /**
     * 查询车俩白名单
     *
     * @param id 车俩白名单ID
     * @return 车俩白名单
     */
    CarWhiteInfo selectCarWhiteInfoById(String id);

    /**
     * 查询车俩白名单列表
     *
     * @param carWhiteInfo 车俩白名单
     * @return 车俩白名单集合
     */
    List<CarWhiteInfo> selectCarWhiteInfoList(CarWhiteInfo carWhiteInfo);


    /**
     * 新增或者修改车俩白名单
     *
     * @param carWhiteInfo 车俩白名单
     * @return 结果
     */
    AjaxResult saveCarWhiteInfo(CarWhiteInfo carWhiteInfo);

    /**
     * 批量删除车俩白名单
     *
     * @param ids 需要删除的车俩白名单ID
     * @return 结果
     */
    AjaxResult deleteCarWhiteInfoByIds(String[] ids);


    /**
     * 跟新redis
     */
    void updateRedisCarWhiteList();


    /**
     * 从缓存拿到carlist
     */
    List<CarWhiteInfo> getRedisCarWhiteList();

}
