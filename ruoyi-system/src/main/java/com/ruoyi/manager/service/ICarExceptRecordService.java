package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarExceptRecord;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;

/**
 * 异常车辆流水Service接口
 *
 * @author ruoyi
 * @date 2025-08-18
 */
public interface ICarExceptRecordService extends IService<CarExceptRecord> {
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
     * 新增或者修改异常车辆流水
     *
     * @param carExceptRecord 异常车辆流水
     * @return 结果
     */
    AjaxResult saveCarExceptRecord(CarExceptRecord carExceptRecord);

    /**
     * 批量删除异常车辆流水
     *
     * @param ids 需要删除的异常车辆流水ID
     * @return 结果
     */
    AjaxResult deleteCarExceptRecordByIds(String[] ids);

}
