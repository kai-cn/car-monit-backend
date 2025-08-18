package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarRouteInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 常用路线Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarRouteInfoMapper extends BaseMapper<CarRouteInfo> {
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
     * 批量删除常用路线
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarRouteInfoByIds(String[] ids);

    /**
     * 删除常用路线
     *
     * @param id 常用路线ID
     * @return 结果
     */
    int deleteCarRouteInfoById(String id);

}
