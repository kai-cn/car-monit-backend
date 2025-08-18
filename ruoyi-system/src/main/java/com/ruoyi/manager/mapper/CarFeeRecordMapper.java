package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarFeeRecord;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 收费流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarFeeRecordMapper extends BaseMapper<CarFeeRecord> {
    /**
     * 查询收费流水
     *
     * @param id 收费流水ID
     * @return 收费流水
     */
    CarFeeRecord selectCarFeeRecordById(String id);

    /**
     * 查询收费流水列表
     *
     * @param carFeeRecord 收费流水
     * @return 收费流水集合
     */
    List<CarFeeRecord> selectCarFeeRecordList(CarFeeRecord carFeeRecord);

    /**
     * 批量删除收费流水
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarFeeRecordByIds(String[] ids);

    /**
     * 删除收费流水
     *
     * @param id 收费流水ID
     * @return 结果
     */
    int deleteCarFeeRecordById(String id);

}
