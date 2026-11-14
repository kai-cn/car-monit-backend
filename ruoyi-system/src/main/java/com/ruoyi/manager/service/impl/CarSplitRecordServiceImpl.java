package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.spring.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarSplitRecordMapper;
import com.ruoyi.manager.domain.CarSplitRecord;
import com.ruoyi.manager.service.ICarSplitRecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 拆分流水Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarSplitRecordServiceImpl extends ServiceImpl<CarSplitRecordMapper, CarSplitRecord> implements ICarSplitRecordService {

    @Autowired
    private CarSplitRecordMapper carSplitRecordMapper;

    /**
     * 查询拆分流水
     *
     * @param id 拆分流水ID
     * @return 拆分流水
     */
    @Override
    public CarSplitRecord selectCarSplitRecordById(String id) {
        return carSplitRecordMapper.selectCarSplitRecordById(id);
    }

    /**
     * 查询拆分流水列表
     *
     * @param carSplitRecord 拆分流水
     * @return 拆分流水
     */
    @Override
    public List<CarSplitRecord> selectCarSplitRecordList(CarSplitRecord carSplitRecord) {
        return carSplitRecordMapper.selectCarSplitRecordList(carSplitRecord);
    }


    /**
     * 新增或者修改拆分流水
     *
     * @param carSplitRecord 拆分流水
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarSplitRecord(CarSplitRecord carSplitRecord)
    {
        if (CommonUtil.isNotBlank(carSplitRecord.getId()))
        {
            // 修改
            carSplitRecordMapper.updateById(carSplitRecord);
        }
        else
        {
            // 新增 主键
            carSplitRecordMapper.insert(carSplitRecord);
        }
        return AjaxResult.success("操作成功！",carSplitRecord.getId());
    }

    /**
     * 批量删除拆分流水
     *
     * @param ids 需要删除的拆分流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarSplitRecordByIds(String[] ids)
    {
        int count = carSplitRecordMapper.deleteCarSplitRecordByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除拆分流水信息
     *
     * @param id 拆分流水ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSplitRecordById(String id)
    {
        int count = carSplitRecordMapper.deleteCarSplitRecordById(id);
        return AjaxResult.success(count);
    }



}
