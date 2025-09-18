package com.ruoyi.manager.service;

import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.manager.domain.CarExceptRecord;
import java.util.List;
import com.baomidou.mybatisplus.extension.service.IService;
import com.ruoyi.manager.domain.vo.PCCarStatisticsDetailVO;
import com.ruoyi.manager.domain.vo.PCCarStatisticsVO;

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

    /**
     * 批量修改异常流水状态
     * @param exceptIdList
     * @param status
     */
    void updateStatusByExceptId(List<String> exceptIdList, String status);


    /**
     * 批量删除异常车辆流水：根据车俩删除异常流水
     *
     * @param fkId
     * @return 结果
     */
    AjaxResult deleteCarExceptRecordByCarId(String fkId);


    /**
     * 根据车牌号统计
     *
     * @param carExceptRecord  车牌号
     * @return 异常车辆流水
     */
    CarExceptRecord exceptRecordCount(CarExceptRecord carExceptRecord);


    PCCarStatisticsVO buildPCCarStatisticsVO(List<String> ids, String escapedType);


    List<PCCarStatisticsDetailVO> buildPCCarStatisticsVODetail(List<String> ids, String escapedType);
}
