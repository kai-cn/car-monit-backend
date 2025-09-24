package com.ruoyi.manager.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.common.utils.CommonUtil;
import com.ruoyi.manager.domain.CarWhiteInfo;
import com.ruoyi.manager.mapper.CarWhiteInfoMapper;
import com.ruoyi.manager.service.ICarWhiteInfoService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * 车俩白名单Service业务层处理
 *
 * @author ruoyi
 * @date 2025-09-12
 */
@Service
public class CarWhiteInfoServiceImpl extends ServiceImpl<CarWhiteInfoMapper, CarWhiteInfo> implements ICarWhiteInfoService {

    @Autowired
    private CarWhiteInfoMapper carWhiteInfoMapper;

    @Autowired
    private RedisCache redisCache;

    /**
     * 查询车俩白名单
     *
     * @param id 车俩白名单ID
     * @return 车俩白名单
     */
    @Override
    public CarWhiteInfo selectCarWhiteInfoById(String id) {
        return carWhiteInfoMapper.selectCarWhiteInfoById(id);
    }

    /**
     * 查询车俩白名单列表
     *
     * @param carWhiteInfo 车俩白名单
     * @return 车俩白名单
     */
    @Override
    public List<CarWhiteInfo> selectCarWhiteInfoList(CarWhiteInfo carWhiteInfo) {
        return carWhiteInfoMapper.selectCarWhiteInfoList(carWhiteInfo);
    }


    /**
     * 新增或者修改车俩白名单
     *
     * @param carWhiteInfo 车俩白名单
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult saveCarWhiteInfo(CarWhiteInfo carWhiteInfo)
    {
        if (CommonUtil.isNotBlank(carWhiteInfo.getId()))
        {
            // 修改
            carWhiteInfoMapper.updateById(carWhiteInfo);
        }
        else
        {
            // 新增 主键
            carWhiteInfoMapper.insert(carWhiteInfo);
        }
        this.updateRedisCarList();
        return AjaxResult.success("操作成功！",carWhiteInfo.getId());
    }

    /**
     * 批量删除车俩白名单
     *
     * @param ids 需要删除的车俩白名单ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    @Override
    public AjaxResult deleteCarWhiteInfoByIds(String[] ids)
    {
        int count = carWhiteInfoMapper.deleteCarWhiteInfoByIds(ids);
        this.updateRedisCarList();
        return AjaxResult.success(count);
    }

    /**
     * 删除车俩白名单信息
     *
     * @param id 车俩白名单ID
     * @return 结果
     */
    @Transactional(rollbackFor = Exception.class)
    public AjaxResult deleteCarWhiteInfoById(String id)
    {
        int count = carWhiteInfoMapper.deleteCarWhiteInfoById(id);
        this.updateRedisCarList();
        return AjaxResult.success(count);
    }

    /**
     * 跟新缓存
     */
    public void updateRedisCarList() {
        CarWhiteInfo carWhiteInfo = new CarWhiteInfo();
        List<CarWhiteInfo> list = carWhiteInfoMapper.selectCarWhiteInfoList(carWhiteInfo);
        redisCache.setCacheObject(Constants.white_car_list, list);
    }


    /**
     * 从缓存拿到carlist
     */
    public List<CarWhiteInfo> getRedisCarList() {
        List<CarWhiteInfo> list = null;
        Object obj = redisCache.getCacheObject(Constants.white_car_list);
        if (null != obj) {
            list = (List) obj;
        } else {
            CarWhiteInfo carWhiteInfo = new CarWhiteInfo();
            list = carWhiteInfoMapper.selectCarWhiteInfoList(carWhiteInfo);
            redisCache.setCacheObject(Constants.white_car_list, list);
        }
        return list;
    }




}
