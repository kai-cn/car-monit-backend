package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarFeeRecord;
import java.util.List;
import com.baomidou.mybatisplus.spring.service.IService;

/**
 * 收费流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarFeeRecordService extends IService<CarFeeRecord> {
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
     * 新增或者修改收费流水
     *
     * @param carFeeRecord 收费流水
     * @return 结果
     */
    AjaxResult saveCarFeeRecord(CarFeeRecord carFeeRecord);

    /**
     * 批量删除收费流水
     *
     * @param ids 需要删除的收费流水ID
     * @return 结果
     */
    AjaxResult deleteCarFeeRecordByIds(String[] ids);

}
