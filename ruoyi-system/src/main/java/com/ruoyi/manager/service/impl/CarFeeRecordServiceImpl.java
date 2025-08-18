package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarFeeRecordMapper;
import com.ruoyi.manager.domain.CarFeeRecord;
import com.ruoyi.manager.service.ICarFeeRecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 收费流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarFeeRecordServiceImpl extends ServiceImpl<CarFeeRecordMapper, CarFeeRecord> implements ICarFeeRecordService {

    @Autowired
    private CarFeeRecordMapper carFeeRecordMapper;

    /**
     * 查询收费流水
     *
     * @param id 收费流水ID
     * @return 收费流水
     */
    @Override
    public CarFeeRecord selectCarFeeRecordById(String id) {
        return carFeeRecordMapper.selectCarFeeRecordById(id);
    }

    /**
     * 查询收费流水列表
     *
     * @param carFeeRecord 收费流水
     * @return 收费流水
     */
    @Override
    public List<CarFeeRecord> selectCarFeeRecordList(CarFeeRecord carFeeRecord) {
        return carFeeRecordMapper.selectCarFeeRecordList(carFeeRecord);
    }


    /**
     * 新增或者修改收费流水
     *
     * @param carFeeRecord 收费流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarFeeRecord(CarFeeRecord carFeeRecord)
    {
        if (CommonUtil.isNotBlank(carFeeRecord.getId()))
        {
            // 修改
            carFeeRecordMapper.updateById(carFeeRecord);
        }
        else
        {
            // 新增 主键
            carFeeRecordMapper.insert(carFeeRecord);
        }
        return AjaxResult.success("操作成功！",carFeeRecord.getId());
    }

    /**
     * 批量删除收费流水
     *
     * @param ids 需要删除的收费流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarFeeRecordByIds(String[] ids)
    {
        int count = carFeeRecordMapper.deleteCarFeeRecordByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除收费流水信息
     *
     * @param id 收费流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarFeeRecordById(String id)
    {
        int count = carFeeRecordMapper.deleteCarFeeRecordById(id);
        return AjaxResult.success(count);
    }



}
