package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.manager.domain.CarWarningInfo;
import com.ruoyi.manager.mapper.CarWarningInfoMapper;
import com.ruoyi.manager.service.ICarWarningInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 预警车辆Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarWarningInfoServiceImpl extends ServiceImpl<CarWarningInfoMapper, CarWarningInfo> implements ICarWarningInfoService {

    @Autowired
    private CarWarningInfoMapper carWarningInfoMapper;

    /**
     * 查询预警车辆
     *
     * @param id 预警车辆ID
     * @return 预警车辆
     */
    @Override
    public CarWarningInfo selectCarWarningInfoById(String id) {
        return carWarningInfoMapper.selectCarWarningInfoById(id);
    }

    /**
     * 查询预警车辆列表
     *
     * @param carWarningInfo 预警车辆
     * @return 预警车辆
     */
    @Override
    public List<CarWarningInfo> selectCarWarningInfoList(CarWarningInfo carWarningInfo) {
        return carWarningInfoMapper.selectCarWarningInfoList(carWarningInfo);
    }


    /**
     * 新增或者修改预警车辆
     *
     * @param carWarningInfo 预警车辆
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarWarningInfo(CarWarningInfo carWarningInfo)
    {
        Long userId = 1L;
        if (CommonUtil.isNotBlank(carWarningInfo.getId()))
        {
            carWarningInfo.setUpdateBy(userId); // 更新人
            carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 修改
            carWarningInfoMapper.updateById(carWarningInfo);
        }
        else
        {
            carWarningInfo.setDelFlag("0");
            carWarningInfo.setCreateBy(userId); // 创建人
            carWarningInfo.setCreateTime(DateUtils.getTimestamp()); // 创建时间
            carWarningInfo.setUpdateBy(userId); // 更新人
            carWarningInfo.setUpdateTime(DateUtils.getTimestamp()); // 更新时间
            // 新增 主键
            carWarningInfoMapper.insert(carWarningInfo);
        }
        return AjaxResult.success("操作成功！",carWarningInfo.getId());
    }

    /**
     * 批量删除预警车辆
     *
     * @param ids 需要删除的预警车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarWarningInfoByIds(String[] ids)
    {
        int count = carWarningInfoMapper.deleteCarWarningInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除预警车辆信息
     *
     * @param id 预警车辆ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarWarningInfoById(String id)
    {
        int count = carWarningInfoMapper.deleteCarWarningInfoById(id);
        return AjaxResult.success(count);
    }

    @Override
    public List<CarWarningInfo> selectCarWarningInfoListLimit100() {
        return carWarningInfoMapper.selectCarWarningInfoListLimit100();
    }


}
