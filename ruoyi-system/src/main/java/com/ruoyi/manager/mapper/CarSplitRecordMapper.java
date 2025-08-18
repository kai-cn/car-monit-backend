package com.ruoyi.manager.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.ruoyi.manager.domain.CarSplitRecord;
import org.springframework.stereotype.Repository;
import java.util.List;

/**
 * 拆分流水Mapper接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Repository
public interface CarSplitRecordMapper extends BaseMapper<CarSplitRecord> {
    /**
     * 查询拆分流水
     *
     * @param id 拆分流水ID
     * @return 拆分流水
     */
    CarSplitRecord selectCarSplitRecordById(String id);

    /**
     * 查询拆分流水列表
     *
     * @param carSplitRecord 拆分流水
     * @return 拆分流水集合
     */
    List<CarSplitRecord> selectCarSplitRecordList(CarSplitRecord carSplitRecord);

    /**
     * 批量删除拆分流水
     *
     * @param ids 需要删除的数据ID
     * @return 结果
     */
    int deleteCarSplitRecordByIds(String[] ids);

    /**
     * 删除拆分流水
     *
     * @param id 拆分流水ID
     * @return 结果
     */
    int deleteCarSplitRecordById(String id);

}
