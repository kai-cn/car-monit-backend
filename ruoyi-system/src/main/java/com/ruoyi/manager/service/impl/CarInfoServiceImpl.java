package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarInfo;
import com.ruoyi.manager.domain.vo.bigscreen.CarInfoVO;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationParam;
import com.ruoyi.manager.domain.vo.bigscreen.CarLocationVO;
import com.ruoyi.manager.mapper.CarInfoMapper;
import com.ruoyi.manager.service.ICarInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;

/**
 * 车辆信息Service业务层处理
 *
 * @author ruoyi
 * @date 2025-08-18
 */
@Service
public class CarInfoServiceImpl extends ServiceImpl<CarInfoMapper, CarInfo> implements ICarInfoService {

    @Autowired
    private CarInfoMapper carInfoMapper;

    /**
     * 查询车辆信息
     *
     * @param id 车辆信息ID
     * @return 车辆信息
     */
    @Override
    public CarInfo selectCarInfoById(String id) {
        return carInfoMapper.selectCarInfoById(id);
    }

    /**
     * 查询车辆信息列表
     *
     * @param carInfo 车辆信息
     * @return 车辆信息
     */
    @Override
    public List<CarInfo> selectCarInfoList(CarInfo carInfo) {
        return carInfoMapper.selectCarInfoList(carInfo);
    }


    /**
     * 新增或者修改车辆信息
     *
     * @param carInfo 车辆信息
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarInfo(CarInfo carInfo)
    {
        if (CommonUtil.isNotBlank(carInfo.getId()))
        {
            // 修改
            carInfoMapper.updateById(carInfo);
        }
        else
        {
            // 新增 主键
            carInfoMapper.insert(carInfo);
        }
        return AjaxResult.success("操作成功！",carInfo.getId());
    }

    /**
     * 批量删除车辆信息
     *
     * @param ids 需要删除的车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarInfoByIds(String[] ids)
    {
        int count = carInfoMapper.deleteCarInfoByIds(ids);
        return AjaxResult.success(count);
    }

    /**
     * 删除车辆信息信息
     *
     * @param id 车辆信息ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarInfoById(String id)
    {
        int count = carInfoMapper.deleteCarInfoById(id);
        return AjaxResult.success(count);
    }


    /**
     * 导入
     *
     * @param list
     * @return
     */
    public AjaxResult doImport(List<CarInfo> list) {
        if (null != list && list.size() > 0) {
            this.saveOrUpdateBatch(list);
        }
        return AjaxResult.success();
    }

    @Override
    public List<CarLocationVO> carLocation(CarLocationParam carInfo) {
       return carInfoMapper.getCarLocation(carInfo);
    }

    @Override
    public List<CarInfoVO> selectCarVoList() {
        return carInfoMapper.selectCarVoList();
    }

    @Override
    public List<CarInfoVO> getCarAudit() {
        return Collections.emptyList();
    }
}
