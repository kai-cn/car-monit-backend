package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarSuspicious;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 可疑车辆Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarSuspiciousMapper extends BaseMapper<CarSuspicious> {
    /**
     * 查询可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 可疑车辆
     */
    CarSuspicious selectCarSuspiciousById(String id);

    /**
     * 查询可疑车辆列表
     *
     * @param carSuspicious 可疑车辆
     * @return 可疑车辆集合
     */
    List<CarSuspicious> selectCarSuspiciousList(CarSuspicious carSuspicious);

    /**
     * 批量删除可疑车辆
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarSuspiciousByIds(String[] ids);

    /**
     * 删除可疑车辆
     *
     * @param id 可疑车辆ID
     * @return 结果
     */
    int deleteCarSuspiciousById(String id);

}
