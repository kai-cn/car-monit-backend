package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarRouteDetailMapper;
import com.ruoyi.manager.domain.CarRouteDetail;
import com.ruoyi.manager.service.ICarRouteDetailService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 常用路线明细Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarRouteDetailServiceImpl extends ServiceImpl<CarRouteDetailMapper, CarRouteDetail> implements ICarRouteDetailService {

    @Autowired
    private CarRouteDetailMapper carRouteDetailMapper;

    /**
     * 查询常用路线明细
     *
     * @param id 常用路线明细ID
     * @return 常用路线明细
     */
    @Override
    public CarRouteDetail selectCarRouteDetailById(String id) {
        return carRouteDetailMapper.selectCarRouteDetailById(id);
    }

    /**
     * 查询常用路线明细列表
     *
     * @param carRouteDetail 常用路线明细
     * @return 常用路线明细
     */
    @Override
    public List<CarRouteDetail> selectCarRouteDetailList(CarRouteDetail carRouteDetail) {
        return carRouteDetailMapper.selectCarRouteDetailList(carRouteDetail);
    }


    /**
     * 新增或者修改常用路线明细
     *
     * @param carRouteDetail 常用路线明细
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarRouteDetail(CarRouteDetail carRouteDetail)
    {
        if (CommonUtil.isNotBlank(carRouteDetail.getId()))
        {
            // 修改
            carRouteDetailMapper.updateById(carRouteDetail);
        }
        else
        {
            // 新增 主键
            carRouteDetailMapper.insert(carRouteDetail);
        }
        return AjaxResult.success("操作成功！",carRouteDetail.getId());
    }

    /**
     * 批量删除常用路线明细
     *
     * @param ids 需要删除的常用路线明细ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarRouteDetailByIds(String[] ids)
    {
        int count = carRouteDetailMapper.deleteCarRouteDetailByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除常用路线明细信息
     *
     * @param id 常用路线明细ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarRouteDetailById(String id)
    {
        int count = carRouteDetailMapper.deleteCarRouteDetailById(id);
        return AjaxResult.success(count);
    }



}
