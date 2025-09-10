package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarSuspiciousCheck;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 可疑车辆人工核实Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarSuspiciousCheckMapper extends BaseMapper<CarSuspiciousCheck> {
    /**
     * 查询可疑车辆人工核实
     *
     * @param id 可疑车辆人工核实ID
     * @return 可疑车辆人工核实
     */
    CarSuspiciousCheck selectCarSuspiciousCheckById(String id);

    /**
     * 查询可疑车辆人工核实列表
     *
     * @param carSuspiciousCheck 可疑车辆人工核实
     * @return 可疑车辆人工核实集合
     */
    List<CarSuspiciousCheck> selectCarSuspiciousCheckList(CarSuspiciousCheck carSuspiciousCheck);

    /**
     * 批量删除可疑车辆人工核实
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarSuspiciousCheckByIds(String[] ids);

    /**
     * 删除可疑车辆人工核实
     *
     * @param id 可疑车辆人工核实ID
     * @return 结果
     */
    int deleteCarSuspiciousCheckById(String id);

    /**
     * 删除可疑车辆人工核实
     *
     * @param fkId 可疑车辆人工核实ID
     * @return 结果
     */
    int deleteCarSuspiciousCheckBySuspiciousId(String fkId);

}
