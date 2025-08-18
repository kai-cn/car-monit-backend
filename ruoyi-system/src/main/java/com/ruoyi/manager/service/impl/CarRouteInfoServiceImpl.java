package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.mapper.CarRouteInfoMapper;
import com.ruoyi.manager.domain.CarRouteInfo;
import com.ruoyi.manager.service.ICarRouteInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 常用路线Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarRouteInfoServiceImpl extends ServiceImpl<CarRouteInfoMapper, CarRouteInfo> implements ICarRouteInfoService {

    @Autowired
    private CarRouteInfoMapper carRouteInfoMapper;

    /**
     * 查询常用路线
     *
     * @param id 常用路线ID
     * @return 常用路线
     */
    @Override
    public CarRouteInfo selectCarRouteInfoById(String id) {
        return carRouteInfoMapper.selectCarRouteInfoById(id);
    }

    /**
     * 查询常用路线列表
     *
     * @param carRouteInfo 常用路线
     * @return 常用路线
     */
    @Override
    public List<CarRouteInfo> selectCarRouteInfoList(CarRouteInfo carRouteInfo) {
        return carRouteInfoMapper.selectCarRouteInfoList(carRouteInfo);
    }


    /**
     * 新增或者修改常用路线
     *
     * @param carRouteInfo 常用路线
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarRouteInfo(CarRouteInfo carRouteInfo)
    {
        if (CommonUtil.isNotBlank(carRouteInfo.getId()))
        {
            // 修改
            carRouteInfoMapper.updateById(carRouteInfo);
        }
        else
        {
            // 新增 主键
            carRouteInfoMapper.insert(carRouteInfo);
        }
        return AjaxResult.success("操作成功！",carRouteInfo.getId());
    }

    /**
     * 批量删除常用路线
     *
     * @param ids 需要删除的常用路线ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarRouteInfoByIds(String[] ids)
    {
        int count = carRouteInfoMapper.deleteCarRouteInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除常用路线信息
     *
     * @param id 常用路线ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarRouteInfoById(String id)
    {
        int count = carRouteInfoMapper.deleteCarRouteInfoById(id);
        return AjaxResult.success(count);
    }



}
