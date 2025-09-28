package com.ruoyi.base.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.base.mapper.GeometryMapper;
import com.ruoyi.base.domain.Geometry;
import com.ruoyi.base.service.IGeometryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 车辆信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@Service
public class GeometryServiceImpl extends ServiceImpl<GeometryMapper, Geometry> implements IGeometryService {

    @Autowired
    private GeometryMapper geometryMapper;

    /**
     * 查询车辆信息
     *
     * @param ID 车辆信息ID
     * @return 车辆信息
     */
    @Override
    public Geometry selectGeometryById(Integer ID) {
        return geometryMapper.selectGeometryById(ID);
    }

    /**
     * 查询车辆信息列表
     *
     * @param geometry 车辆信息
     * @return 车辆信息
     */
    @Override
    public List<Geometry> selectGeometryList(Geometry geometry) {
        return geometryMapper.selectGeometryList(geometry);
    }


    /**
     * 新增或者修改车辆信息
     *
     * @param geometry 车辆信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveGeometry(Geometry geometry)
    {
        if (null != geometry.getId())
        {
            // 修改
            geometryMapper.updateById(geometry);
        }
        else
        {
            // 新增 主键
            geometryMapper.insert(geometry);
        }
        return AjaxResult.success("操作成功！",geometry.getId());
    }

    /**
     * 批量删除车辆信息
     *
     * @param IDs 需要删除的车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteGeometryByIds(Integer[] IDs)
    {
        int count = geometryMapper.deleteGeometryByIds(IDs);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆信息信息
     *
     * @param ID 车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteGeometryById(Integer ID)
    {
        int count = geometryMapper.deleteGeometryById(ID);
        return AjaxResult.success(count);
    }



}
