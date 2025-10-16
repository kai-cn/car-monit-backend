package com.ruoyi.base.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.base.domain.Geometry;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车辆信息Mapper接口
 *
 * @author ruoyi
 * @date 2025-09-27
 */
@Repository
public interface GeometryMapper extends BaseMapper<Geometry> {
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
     * 批量删除车辆信息
     *
     * @param IDs 需要删除的数据ID
     * @return 结果
     */
    int deleteGeometryByIds(Integer[] IDs);

    /**
     * 删除车辆信息
     *
     * @param ID 车辆信息ID
     * @return 结果
     */
    int deleteGeometryById(Integer ID);

    /**
     * 查询未同步的路线
     * @return
     */
    List<Geometry> syncAllGeometry();
}
