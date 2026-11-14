package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarSplitRecord;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 拆分流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarSplitRecordService extends IService<CarSplitRecord> {
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
     * 新增或者修改拆分流水
     *
     * @param carSplitRecord 拆分流水
     * @return 结果
     */
    AjaxResult saveCarSplitRecord(CarSplitRecord carSplitRecord);

    /**
     * 批量删除拆分流水
     *
     * @param ids 需要删除的拆分流水ID
     * @return 结果
     */
    AjaxResult deleteCarSplitRecordByIds(String[] ids);

}
