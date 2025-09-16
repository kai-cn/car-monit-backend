package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarExceptRecord;
import org.apache.ibatis.annotations.Param;
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

    /**
     * 批量修改状态
     *
     * @return 结果
     */
    void updateStatusByExceptId(@Param("exceptIdList") List<String> exceptIdList, @Param("status") String status);


    /**
     * 批量删除异常车辆流水：根据车俩删除异常流水
     *
     * @param fkId
     * @return 结果
     */
    int deleteCarExceptRecordByCarId(String fkId);

    /**
     * 根据车牌号统计
     *
     * @param carExceptRecord  车牌号
     * @return 异常车辆流水
     */
    CarExceptRecord exceptRecordCount(CarExceptRecord carExceptRecord);


}
