package com.ruoyi.base.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.common.core.domain.AjaxResult;

import java.util.List;

/**
 * 车辆信息Service接口
 *
 * @author ruoyi
 * @date 2025-09-27
 */
public interface IGeometryService extends IService<Geometry> {
    /**
     * 查询车辆信息
     *
     * @param ID 车辆信息ID
     * @return 车辆信息
     */
    Geometry selectGeometryById(Integer ID);

    /**
     * 查询车辆信息列表
     *
     * @param geometry 车辆信息
     * @return 车辆信息集合
     */
    List<Geometry> selectGeometryList(Geometry geometry);


    /**
     * 新增或者修改车辆信息
     *
     * @param geometry 车辆信息
     * @return 结果
     */
    AjaxResult saveGeometry(Geometry geometry);

    /**
     * 批量删除车辆信息
     *
     * @param IDs 需要删除的车辆信息ID
     * @return 结果
     */
    AjaxResult deleteGeometryByIds(Integer[] IDs);


    /**
     * 跟新redis
     */
    void updateRedisList();


    /**
     * 从缓存拿到carlist
     */
    List<Geometry> getRedisList();

    /**
     * 根据路线code 查询
     */
    List<Geometry> getListByCode(List<String> roadCodeList);

}
