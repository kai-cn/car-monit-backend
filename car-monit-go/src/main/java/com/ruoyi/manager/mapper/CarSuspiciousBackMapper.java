package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarSuspiciousBack;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 可疑车辆备份Mapper接口
 *
 * @author ruoyi
 * @date 2026-10-31
 */
@Repository
public interface CarSuspiciousBackMapper extends BaseMapper<CarSuspiciousBack> {
    /**
     * 查询可疑车辆备份
     *
     * @param id 可疑车辆备份ID
     * @return 可疑车辆备份
     */
    CarSuspiciousBack selectCarSuspiciousBackById(String id);

    /**
     * 查询可疑车辆备份列表
     *
     * @param carSuspiciousBack 可疑车辆备份
     * @return 可疑车辆备份集合
     */
    List<CarSuspiciousBack> selectCarSuspiciousBackList(CarSuspiciousBack carSuspiciousBack);

    /**
     * 批量删除可疑车辆备份
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarSuspiciousBackByIds(String[] ids);

    /**
     * 删除可疑车辆备份
     *
     * @param id 可疑车辆备份ID
     * @return 结果
     */
    int deleteCarSuspiciousBackById(String id);

}
