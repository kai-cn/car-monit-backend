package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarExceptRecord;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 异常车辆流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarExceptRecordMapper extends BaseMapper<CarExceptRecord> {
    /**
     * 查询异常车辆流水
     *
     * @param id 异常车辆流水ID
     * @return 异常车辆流水
     */
    CarExceptRecord selectCarExceptRecordById(String id);

    /**
     * 查询异常车辆流水列表
     *
     * @param carExceptRecord 异常车辆流水
     * @return 异常车辆流水集合
     */
    List<CarExceptRecord> selectCarExceptRecordList(CarExceptRecord carExceptRecord);

    /**
     * 批量删除异常车辆流水
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarExceptRecordByIds(String[] ids);

    /**
     * 删除异常车辆流水
     *
     * @param id 异常车辆流水ID
     * @return 结果
     */
    int deleteCarExceptRecordById(String id);

}
