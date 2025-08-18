package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarTrackInfo;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 车辆行驶轨迹Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarTrackInfoMapper extends BaseMapper<CarTrackInfo> {
    /**
     * 查询车辆行驶轨迹
     *
     * @param id 车辆行驶轨迹ID
     * @return 车辆行驶轨迹
     */
    CarTrackInfo selectCarTrackInfoById(String id);

    /**
     * 查询车辆行驶轨迹列表
     *
     * @param carTrackInfo 车辆行驶轨迹
     * @return 车辆行驶轨迹集合
     */
    List<CarTrackInfo> selectCarTrackInfoList(CarTrackInfo carTrackInfo);

    /**
     * 批量删除车辆行驶轨迹
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarTrackInfoByIds(String[] ids);

    /**
     * 删除车辆行驶轨迹
     *
     * @param id 车辆行驶轨迹ID
     * @return 结果
     */
    int deleteCarTrackInfoById(String id);

}
