package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarExceptRecordMapper;
import com.ruoyi.manager.domain.CarExceptRecord;
import com.ruoyi.manager.service.ICarExceptRecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 异常车辆流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarExceptRecordServiceImpl extends ServiceImpl<CarExceptRecordMapper, CarExceptRecord> implements ICarExceptRecordService {

    @Autowired
    private CarExceptRecordMapper carExceptRecordMapper;

    /**
     * 查询异常车辆流水
     *
     * @param id 异常车辆流水ID
     * @return 异常车辆流水
     */
    @Override
    public CarExceptRecord selectCarExceptRecordById(String id) {
        return carExceptRecordMapper.selectCarExceptRecordById(id);
    }

    /**
     * 查询异常车辆流水列表
     *
     * @param carExceptRecord 异常车辆流水
     * @return 异常车辆流水
     */
    @Override
    public List<CarExceptRecord> selectCarExceptRecordList(CarExceptRecord carExceptRecord) {
        return carExceptRecordMapper.selectCarExceptRecordList(carExceptRecord);
    }


    /**
     * 新增或者修改异常车辆流水
     *
     * @param carExceptRecord 异常车辆流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarExceptRecord(CarExceptRecord carExceptRecord)
    {
        if (CommonUtil.isNotBlank(carExceptRecord.getId()))
        {
            // 修改
            carExceptRecordMapper.updateById(carExceptRecord);
        }
        else
        {
            // 新增 主键
            carExceptRecordMapper.insert(carExceptRecord);
        }
        return AjaxResult.success("操作成功！",carExceptRecord.getId());
    }

    /**
     * 批量删除异常车辆流水
     *
     * @param ids 需要删除的异常车辆流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarExceptRecordByIds(String[] ids)
    {
        int count = carExceptRecordMapper.deleteCarExceptRecordByIds(ids);
        return AjaxResult.success(count);
    }

    @Override
    public void updateStatusByExceptId(List<String> exceptIdList, String status) {
        carExceptRecordMapper.updateStatusByExceptId(exceptIdList, status);
    }

    /**
     * 删除异常车辆流水信息
     *
     * @param id 异常车辆流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarExceptRecordById(String id)
    {
        int count = carExceptRecordMapper.deleteCarExceptRecordById(id);
        return AjaxResult.success(count);
    }



}
