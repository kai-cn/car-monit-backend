package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarSuspiciousBackMapper;
import com.ruoyi.manager.domain.CarSuspiciousBack;
import com.ruoyi.manager.service.ICarSuspiciousBackService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 可疑车辆备份Service业务层处理
 *
 * @author ruoyi
 * @date 2026-10-31
 */
@Service
public class CarSuspiciousBackServiceImpl extends ServiceImpl<CarSuspiciousBackMapper, CarSuspiciousBack> implements ICarSuspiciousBackService {

    @Autowired
    private CarSuspiciousBackMapper carSuspiciousBackMapper;

    /**
     * 查询可疑车辆备份
     *
     * @param id 可疑车辆备份ID
     * @return 可疑车辆备份
     */
    @Override
    public CarSuspiciousBack selectCarSuspiciousBackById(String id) {
        return carSuspiciousBackMapper.selectCarSuspiciousBackById(id);
    }

    /**
     * 查询可疑车辆备份列表
     *
     * @param carSuspiciousBack 可疑车辆备份
     * @return 可疑车辆备份
     */
    @Override
    public List<CarSuspiciousBack> selectCarSuspiciousBackList(CarSuspiciousBack carSuspiciousBack) {
        return carSuspiciousBackMapper.selectCarSuspiciousBackList(carSuspiciousBack);
    }


    /**
     * 新增或者修改可疑车辆备份
     *
     * @param carSuspiciousBack 可疑车辆备份
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarSuspiciousBack(CarSuspiciousBack carSuspiciousBack)
    {
        if (CommonUtil.isNotBlank(carSuspiciousBack.getId()))
        {
            // 修改
            carSuspiciousBackMapper.updateById(carSuspiciousBack);
        }
        else
        {
            // 新增 主键
            carSuspiciousBackMapper.insert(carSuspiciousBack);
        }
        return AjaxResult.success("操作成功！",carSuspiciousBack.getId());
    }

    /**
     * 批量删除可疑车辆备份
     *
     * @param ids 需要删除的可疑车辆备份ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarSuspiciousBackByIds(String[] ids)
    {
        int count = carSuspiciousBackMapper.deleteCarSuspiciousBackByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除可疑车辆备份信息
     *
     * @param id 可疑车辆备份ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarSuspiciousBackById(String id)
    {
        int count = carSuspiciousBackMapper.deleteCarSuspiciousBackById(id);
        return AjaxResult.success(count);
    }



}
