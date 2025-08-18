package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarRouteDetail;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 常用路线明细Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarRouteDetailMapper extends BaseMapper<CarRouteDetail> {
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
     * 批量删除常用路线明细
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarRouteDetailByIds(String[] ids);

    /**
     * 删除常用路线明细
     *
     * @param id 常用路线明细ID
     * @return 结果
     */
    int deleteCarRouteDetailById(String id);

}
